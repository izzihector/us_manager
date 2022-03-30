# -*- coding: utf-8 -*-
'''
@author: Manuel F Martinez <manpaz@bashlinux.com>
@organization: Bashlinux
@copyright: Copyright (c) 2012 Bashlinux
@license: GPL
'''

#Replace this file with posbox odoo-server's hw_escpos/escpos/escpos.py to print code128 barcode on XmlReciept

import logging
import time
import copy
import io
import base64
import math
import md5
import re
import traceback
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import Image
import ImageDraw
import re

#from PIL import Image
import io

_logger = logging.getLogger(__name__)

try:
    import jcconv
except ImportError:
    jcconv = None
    _logger.warning('ESC/POS: please install jcconv for improved Japanese receipt printing:\n  # pip install jcconv')

try: 
    import qrcode
except ImportError:
    qrcode = None
    _logger.warning('ESC/POS: please install the qrcode python module for qrcode printing in point of sale receipts:\n  # pip install qrcode')

from constants import *
from exceptions import *

def utfstr(stuff):
    """ converts stuff to string and does without failing if stuff is a utf8 string """
    if isinstance(stuff,str):
        return stuff
    else:
        return str(stuff)

class StyleStack:
    """ 
    The stylestack is used by the xml receipt serializer to compute the active styles along the xml
    document. Styles are just xml attributes, there is no css mechanism. But the style applied by
    the attributes are inherited by deeper nodes.
    """
    def __init__(self):
        self.stack = []
        self.defaults = {   # default style values
            'align':     'left',
            'underline': 'off',
            'bold':      'off',
            'size':      'normal',
            'font'  :    'a',
            'width':     48,
            'indent':    0,
            'tabwidth':  2,
            'bullet':    ' - ',
            'line-ratio':0.5,
            'color':    'black',

            'value-decimals':           2,
            'value-symbol':             '',
            'value-symbol-position':    'after',
            'value-autoint':            'off',
            'value-decimals-separator':  '.',
            'value-thousands-separator': ',',
            'value-width':               0,
            
        }

        self.types = { # attribute types, default is string and can be ommitted
            'width':    'int',
            'indent':   'int',
            'tabwidth': 'int',
            'line-ratio':       'float',
            'value-decimals':   'int',
            'value-width':      'int',
        }

        self.cmds = { 
            # translation from styles to escpos commands
            # some style do not correspond to escpos command are used by
            # the serializer instead
            'align': {
                'left':     TXT_ALIGN_LT,
                'right':    TXT_ALIGN_RT,
                'center':   TXT_ALIGN_CT,
                '_order':   1,
            },
            'underline': {
                'off':      TXT_UNDERL_OFF,
                'on':       TXT_UNDERL_ON,
                'double':   TXT_UNDERL2_ON,
                # must be issued after 'size' command
                # because ESC ! resets ESC -
                '_order':   10,
            },
            'bold': {
                'off':      TXT_BOLD_OFF,
                'on':       TXT_BOLD_ON,
                # must be issued after 'size' command
                # because ESC ! resets ESC E
                '_order':   10,
            },
            'font': {
                'a':        TXT_FONT_A,
                'b':        TXT_FONT_B,
                # must be issued after 'size' command
                # because ESC ! resets ESC M
                '_order':   10,
            },
            'size': {
                'normal':           TXT_NORMAL,
                'double-height':    TXT_2HEIGHT,
                'double-width':     TXT_2WIDTH,
                'double':           TXT_DOUBLE,
                '_order':           1,
            },
            'color': {
                'black':    TXT_COLOR_BLACK,
                'red':      TXT_COLOR_RED,
                '_order':   1,
            },
        }

        self.push(self.defaults) 

    def get(self,style):
        """ what's the value of a style at the current stack level"""
        level = len(self.stack) -1
        while level >= 0:
            if style in self.stack[level]:
                return self.stack[level][style]
            else:
                level = level - 1
        return None

    def enforce_type(self, attr, val):
        """converts a value to the attribute's type"""
        if not attr in self.types:
            return utfstr(val)
        elif self.types[attr] == 'int':
            return int(float(val))
        elif self.types[attr] == 'float':
            return float(val)
        else:
            return utfstr(val)

    def push(self, style={}):
        """push a new level on the stack with a style dictionnary containing style:value pairs"""
        _style = {}
        for attr in style:
            if attr in self.cmds and not style[attr] in self.cmds[attr]:
                print(('WARNING: ESC/POS PRINTING: ignoring invalid value: '+utfstr(style[attr])+' for style: '+utfstr(attr)))
            else:
                _style[attr] = self.enforce_type(attr, style[attr])
        self.stack.append(_style)

    def set(self, style={}):
        """overrides style values at the current stack level"""
        _style = {}
        for attr in style:
            if attr in self.cmds and not style[attr] in self.cmds[attr]:
                print(('WARNING: ESC/POS PRINTING: ignoring invalid value: '+utfstr(style[attr])+' for style: '+utfstr(attr)))
            else:
                self.stack[-1][attr] = self.enforce_type(attr, style[attr])

    def pop(self):
        """ pop a style stack level """
        if len(self.stack) > 1 :
            self.stack = self.stack[:-1]

    def to_escpos(self):
        """ converts the current style to an escpos command string """
        cmd = ''
        # Sort commands because some commands affect others (see _order attributes above)
        ordered_cmds = list(self.cmds.keys())
        ordered_cmds.sort(lambda x, y: cmp(self.cmds[x]['_order'], self.cmds[y]['_order']))
        for style in ordered_cmds:
            cmd += self.cmds[style][self.get(style)]
        return cmd

class XmlSerializer:
    """ 
    Converts the xml inline / block tree structure to a string,
    keeping track of newlines and spacings.
    The string is outputted asap to the provided escpos driver.
    """
    def __init__(self,escpos):
        self.escpos = escpos
        self.stack = ['block']
        self.dirty = False

    def start_inline(self,stylestack=None):
        """ starts an inline entity with an optional style definition """
        self.stack.append('inline')
        if self.dirty:
            self.escpos._raw(' ')
        if stylestack:
            self.style(stylestack)

    def start_block(self,stylestack=None):
        """ starts a block entity with an optional style definition """
        if self.dirty:
            self.escpos._raw('\n')
            self.dirty = False
        self.stack.append('block')
        if stylestack:
            self.style(stylestack)

    def end_entity(self):
        """ ends the entity definition. (but does not cancel the active style!) """
        if self.stack[-1] == 'block' and self.dirty:
            self.escpos._raw('\n')
            self.dirty = False
        if len(self.stack) > 1:
            self.stack = self.stack[:-1]

    def pre(self,text):
        """ puts a string of text in the entity keeping the whitespace intact """
        if text:
            self.escpos.text(text)
            self.dirty = True

    def text(self,text):
        """ puts text in the entity. Whitespace and newlines are stripped to single spaces. """
        if text:
            text = utfstr(text)
            text = text.strip()
            text = re.sub('\s+',' ',text)
            if text:
                self.dirty = True
                self.escpos.text(text)

    def linebreak(self):
        """ inserts a linebreak in the entity """
        self.dirty = False
        self.escpos._raw('\n')

    def style(self,stylestack):
        """ apply a style to the entity (only applies to content added after the definition) """
        self.raw(stylestack.to_escpos())

    def raw(self,raw):
        """ puts raw text or escpos command in the entity without affecting the state of the serializer """
        self.escpos._raw(raw)

class XmlLineSerializer:
    """ 
    This is used to convert a xml tree into a single line, with a left and a right part.
    The content is not output to escpos directly, and is intended to be fedback to the
    XmlSerializer as the content of a block entity.
    """
    def __init__(self, indent=0, tabwidth=2, width=48, ratio=0.5):
        self.tabwidth = tabwidth
        self.indent = indent
        self.width  = max(0, width - int(tabwidth*indent))
        self.lwidth = int(self.width*ratio)
        self.rwidth = max(0, self.width - self.lwidth)
        self.clwidth = 0
        self.crwidth = 0
        self.lbuffer  = ''
        self.rbuffer  = ''
        self.left    = True

    def _txt(self,txt):
        if self.left:
            if self.clwidth < self.lwidth:
                txt = txt[:max(0, self.lwidth - self.clwidth)]
                self.lbuffer += txt
                self.clwidth += len(txt)
        else:
            if self.crwidth < self.rwidth:
                txt = txt[:max(0, self.rwidth - self.crwidth)]
                self.rbuffer += txt
                self.crwidth  += len(txt)

    def start_inline(self,stylestack=None):
        if (self.left and self.clwidth) or (not self.left and self.crwidth):
            self._txt(' ')

    def start_block(self,stylestack=None):
        self.start_inline(stylestack)

    def end_entity(self):
        pass

    def pre(self,text):
        if text:
            self._txt(text)
    def text(self,text):
        if text:
            text = utfstr(text)
            text = text.strip()
            text = re.sub('\s+',' ',text)
            if text:
                self._txt(text)

    def linebreak(self):
        pass
    def style(self,stylestack):
        pass
    def raw(self,raw):
        pass

    def start_right(self):
        self.left = False

    def get_line(self):
        return ' ' * self.indent * self.tabwidth + self.lbuffer + ' ' * (self.width - self.clwidth - self.crwidth) + self.rbuffer
    

class Escpos:
    """ ESC/POS Printer object """
    device    = None
    encoding  = None
    img_cache = {}

    CODE128_CHART = """
    0       212222  space   space   00
    1       222122  !       !       01
    2       222221  "       "       02
    3       121223  #       #       03
    4       121322  $       $       04
    5       131222  %       %       05
    6       122213  &       &       06
    7       122312  '       '       07
    8       132212  (       (       08
    9       221213  )       )       09
    10      221312  *       *       10
    11      231212  +       +       11
    12      112232  ,       ,       12
    13      122132  -       -       13
    14      122231  .       .       14
    15      113222  /       /       15
    16      123122  0       0       16
    17      123221  1       1       17
    18      223211  2       2       18
    19      221132  3       3       19
    20      221231  4       4       20
    21      213212  5       5       21
    22      223112  6       6       22
    23      312131  7       7       23
    24      311222  8       8       24
    25      321122  9       9       25
    26      321221  :       :       26
    27      312212  ;       ;       27
    28      322112  <       <       28
    29      322211  =       =       29
    30      212123  >       >       30
    31      212321  ?       ?       31
    32      232121  @       @       32
    33      111323  A       A       33
    34      131123  B       B       34
    35      131321  C       C       35
    36      112313  D       D       36
    37      132113  E       E       37
    38      132311  F       F       38
    39      211313  G       G       39
    40      231113  H       H       40
    41      231311  I       I       41
    42      112133  J       J       42
    43      112331  K       K       43
    44      132131  L       L       44
    45      113123  M       M       45
    46      113321  N       N       46
    47      133121  O       O       47
    48      313121  P       P       48
    49      211331  Q       Q       49
    50      231131  R       R       50
    51      213113  S       S       51
    52      213311  T       T       52
    53      213131  U       U       53
    54      311123  V       V       54
    55      311321  W       W       55
    56      331121  X       X       56
    57      312113  Y       Y       57
    58      312311  Z       Z       58
    59      332111  [       [       59
    60      314111  \       \       60
    61      221411  ]       ]       61
    62      431111  ^       ^       62
    63      111224  _       _       63
    64      111422  NUL     `       64
    65      121124  SOH     a       65
    66      121421  STX     b       66
    67      141122  ETX     c       67
    68      141221  EOT     d       68
    69      112214  ENQ     e       69
    70      112412  ACK     f       70
    71      122114  BEL     g       71
    72      122411  BS      h       72
    73      142112  HT      i       73
    74      142211  LF      j       74
    75      241211  VT      k       75
    76      221114  FF      l       76
    77      413111  CR      m       77
    78      241112  SO      n       78
    79      134111  SI      o       79
    80      111242  DLE     p       80
    81      121142  DC1     q       81
    82      121241  DC2     r       82
    83      114212  DC3     s       83
    84      124112  DC4     t       84
    85      124211  NAK     u       85
    86      411212  SYN     v       86
    87      421112  ETB     w       87
    88      421211  CAN     x       88
    89      212141  EM      y       89
    90      214121  SUB     z       90
    91      412121  ESC     {       91
    92      111143  FS      |       92
    93      111341  GS      }       93
    94      131141  RS      ~       94
    95      114113  US      DEL     95
    96      114311  FNC3    FNC3    96
    97      411113  FNC2    FNC2    97
    98      411311  ShiftB  ShiftA  98
    99      113141  CodeC   CodeC   99
    100     114131  CodeB   FNC4    CodeB
    101     311141  FNC4    CodeA   CodeA
    102     411131  FNC1    FNC1    FNC1
    103     211412  StartA  StartA  StartA
    104     211214  StartB  StartB  StartB
    105     211232  StartC  StartC  StartC
    106     2331112 Stop    Stop    Stop
    """.split()
    
    VALUES   = [int(value) for value in CODE128_CHART[0::5]]
    WEIGHTS  = dict(list(zip(VALUES, CODE128_CHART[1::5])))
    CODE128A = dict(list(zip(CODE128_CHART[2::5], VALUES)))
    CODE128B = dict(list(zip(CODE128_CHART[3::5], VALUES)))
    CODE128C = dict(list(zip(CODE128_CHART[4::5], VALUES)))
    
    for charset in (CODE128A, CODE128B):
        charset[' '] = charset.pop('space')
    
    def code128_format(self, data):
        """
        Generate an optimal barcode from ASCII text
        """
                
        text     = str(data)
        pos      = 0
        length   = len(text)
        
        # Start Code
        if text[:2].isdigit() and length > 1:
            charset = self.CODE128C
            codes   = [charset['StartC']]
        else:
            charset = self.CODE128B
            codes   = [charset['StartB']]
        
        # Data
        while pos < length:
            if charset is self.CODE128C:
                if text[pos:pos+2].isdigit() and length - pos > 1:
                    # Encode Code C two characters at a time
                    codes.append(int(text[pos:pos+2]))
                    pos += 2
                else:
                    # Switch to Code B
                    codes.append(charset['CodeB'])
                    charset = self.CODE128B
            elif text[pos:pos+4].isdigit() and length - pos >= 4:
                # Switch to Code C
                codes.append(charset['CodeC'])
                charset = self.CODE128C
            else:
                # Encode Code B one character at a time
                codes.append(charset[text[pos]])
                pos += 1
        
        # Checksum
        checksum = 0
        for weight, code in enumerate(codes):
            checksum += max(weight, 1) * code
        codes.append(checksum % 103)
        
        # Stop Code
        codes.append(charset['Stop'])
        return codes
    
    def code128_image(self, data, height=100, thickness=3, quiet_zone=True):
        
        if not data[-1] == self.CODE128B['Stop']:
            data = self.code128_format(data)
        print(("\n\n In code128 image formated DATA ---- ",data))
        barcode_widths = []
        for code in data:
            for weight in self.WEIGHTS[code]:
                barcode_widths.append(int(weight) * thickness)
        width = sum(barcode_widths)
        x = 0
    
        if quiet_zone:
            width += 20 * thickness
            x = 10 * thickness
    
        # Monochrome Image
        img  = Image.new('1', (width, height), 1)
        draw = ImageDraw.Draw(img)
        draw_bar = True
        for width in barcode_widths:
            if draw_bar:
                draw.rectangle(((x, 0), (x + width - 1, height)), fill=0)
            draw_bar = not draw_bar
            x += width
        print(("\n\n In code128 image IMG ---- ",img))
        return img

    def _check_image_size(self, size):
        """ Check and fix the size of the image to 32 bits """
        if size % 32 == 0:
            return (0, 0)
        else:
            image_border = 32 - (size % 32)
            if (image_border % 2) == 0:
                return (image_border / 2, image_border / 2)
            else:
                return (image_border / 2, (image_border / 2) + 1)

    def _print_image(self, line, size):
        """ Print formatted image """
        i = 0
        cont = 0
        buffer = ""

       
        self._raw(S_RASTER_N)
        buffer = "%02X%02X%02X%02X" % (((size[0]/size[1])/8), 0, size[1], 0)
        self._raw(buffer.decode('hex'))
        buffer = ""

        while i < len(line):
            hex_string = int(line[i:i+8],2)
            buffer += "%02X" % hex_string
            i += 8
            cont += 1
            if cont % 4 == 0:
                self._raw(buffer.decode("hex"))
                buffer = ""
                cont = 0

    def _raw_print_image(self, line, size, output=None ):
        """ Print formatted image """
        i = 0
        cont = 0
        buffer = ""
        raw = ""

        def __raw(string):
            if output:
                output(string)
            else:
                self._raw(string)
       
        raw += S_RASTER_N
        buffer = "%02X%02X%02X%02X" % (((size[0]/size[1])/8), 0, size[1], 0)
        raw += buffer.decode('hex')
        buffer = ""

        while i < len(line):
            hex_string = int(line[i:i+8],2)
            buffer += "%02X" % hex_string
            i += 8
            cont += 1
            if cont % 4 == 0:
                raw += buffer.decode("hex")
                buffer = ""
                cont = 0

        return raw

    def _convert_image(self, im):
        """ Parse image and prepare it to a printable format """
        pixels   = []
        pix_line = ""
        im_left  = ""
        im_right = ""
        switch   = 0
        img_size = [ 0, 0 ]


        if im.size[0] > 512:
            print("WARNING: Image is wider than 512 and could be truncated at print time ")
        if im.size[1] > 255:
            raise ImageSizeError()

        im_border = self._check_image_size(im.size[0])
        for i in range(im_border[0]):
            im_left += "0"
        for i in range(im_border[1]):
            im_right += "0"

        for y in range(im.size[1]):
            img_size[1] += 1
            pix_line += im_left
            img_size[0] += im_border[0]
            for x in range(im.size[0]):
                img_size[0] += 1
                RGB = im.getpixel((x, y))
                im_color = (RGB[0] + RGB[1] + RGB[2])
                im_pattern = "1X0"
                pattern_len = len(im_pattern)
                switch = (switch - 1 ) * (-1)
                for x in range(pattern_len):
                    if im_color <= (255 * 3 / pattern_len * (x+1)):
                        if im_pattern[x] == "X":
                            pix_line += "%d" % switch
                        else:
                            pix_line += im_pattern[x]
                        break
                    elif im_color > (255 * 3 / pattern_len * pattern_len) and im_color <= (255 * 3):
                        pix_line += im_pattern[-1]
                        break 
            pix_line += im_right
            img_size[0] += im_border[1]

        return (pix_line, img_size)

    def image(self,path_img):
        """ Open image file """
        im_open = Image.open(path_img)
        im = im_open.convert("RGB")
        # Convert the RGB image in printable image
        pix_line, img_size = self._convert_image(im)
        self._print_image(pix_line, img_size)

    def print_base64_image(self,img):

        print('print_b64_img')

        id = md5.new(img).digest()

        if id not in self.img_cache:
            print('not in cache')

            img = img[img.find(',')+1:]
            f = io.BytesIO('img')
            f.write(base64.decodestring(img))
            f.seek(0)
            img_rgba = Image.open(f)
            img = Image.new('RGB', img_rgba.size, (255,255,255))
            channels = img_rgba.split()
            if len(channels) > 1:
                # use alpha channel as mask
                img.paste(img_rgba, mask=channels[3])
            else:
                img.paste(img_rgba)

            print('convert image')
        
            pix_line, img_size = self._convert_image(img)

            print('print image')

            buffer = self._raw_print_image(pix_line, img_size)
            self.img_cache[id] = buffer

        print('raw image')

        self._raw(self.img_cache[id])

    def qr(self,text):
        """ Print QR Code for the provided string """
        qr_code = qrcode.QRCode(version=4, box_size=4, border=1)
        qr_code.add_data(text)
        qr_code.make(fit=True)
        qr_img = qr_code.make_image()
        im = qr_img._img.convert("RGB")
        # Convert the RGB image in printable image
        self._convert_image(im)

    def barcode(self, code, bc, width=255, height=2, pos='below', font='a'):
        """ Print Barcode """
        # Align Bar Code()
        self._raw(TXT_ALIGN_CT)
        # Height
        if height >=2 or height <=6:
            self._raw(BARCODE_HEIGHT)
        else:
            raise BarcodeSizeError()
        # Width
        if width >= 1 or width <=255:
            self._raw(BARCODE_WIDTH)
        else:
            raise BarcodeSizeError()
        # Font
        if font.upper() == "B":
            self._raw(BARCODE_FONT_B)
        else: # DEFAULT FONT: A
            self._raw(BARCODE_FONT_A)
        # Position
        if pos.upper() == "OFF":
            self._raw(BARCODE_TXT_OFF)
        elif pos.upper() == "BOTH":
            self._raw(BARCODE_TXT_BTH)
        elif pos.upper() == "ABOVE":
            self._raw(BARCODE_TXT_ABV)
        else:  # DEFAULT POSITION: BELOW 
            self._raw(BARCODE_TXT_BLW)
        # Type 
        if bc.upper() == "UPC-A":
            self._raw(BARCODE_UPC_A)
        elif bc.upper() == "UPC-E":
            self._raw(BARCODE_UPC_E)
        elif bc.upper() == "EAN13":
            self._raw(BARCODE_EAN13)
        elif bc.upper() == "EAN8":
            self._raw(BARCODE_EAN8)
        elif bc.upper() == "CODE39":
            self._raw(BARCODE_CODE39)
        elif bc.upper() == "ITF":
            self._raw(BARCODE_ITF)
        elif bc.upper() == "NW7":
            self._raw(BARCODE_NW7)
        else:
            raise BarcodeTypeError()
        # Print Code
        if code:
            self._raw(code)
        else:
            raise exception.BarcodeCodeError()

    def receipt(self,xml):
        """
        Prints an xml based receipt definition
        """

        def strclean(string):
            if not string:
                string = ''
            string = string.strip()
            string = re.sub('\s+',' ',string)
            return string

        def format_value(value, decimals=3, width=0, decimals_separator='.', thousands_separator=',', autoint=False, symbol='', position='after'):
            decimals = max(0,int(decimals))
            width    = max(0,int(width))
            value    = float(value)

            if autoint and math.floor(value) == value:
                decimals = 0
            if width == 0:
                width = ''

            if thousands_separator:
                formatstr = "{:"+str(width)+",."+str(decimals)+"f}"
            else:
                formatstr = "{:"+str(width)+"."+str(decimals)+"f}"


            ret = formatstr.format(value)
            ret = ret.replace(',','COMMA')
            ret = ret.replace('.','DOT')
            ret = ret.replace('COMMA',thousands_separator)
            ret = ret.replace('DOT',decimals_separator)

            if symbol:
                if position == 'after':
                    ret = ret + symbol
                else:
                    ret = symbol + ret
            return ret

        def print_elem(stylestack, serializer, elem, indent=0):
                
            elem_styles = {
                'h1': {'bold': 'on', 'size':'double'},
                'h2': {'size':'double'},
                'h3': {'bold': 'on', 'size':'double-height'},
                'h4': {'size': 'double-height'},
                'h5': {'bold': 'on'},
                'em': {'font': 'b'},
                'b':  {'bold': 'on'},
            }

            stylestack.push()
            if elem.tag in elem_styles:
                stylestack.set(elem_styles[elem.tag])
            stylestack.set(elem.attrib)

            if elem.tag in ('p','div','section','article','receipt','header','footer','li','h1','h2','h3','h4','h5'):
                serializer.start_block(stylestack)
                serializer.text(elem.text)
                for child in elem:
                    print_elem(stylestack,serializer,child)
                    serializer.start_inline(stylestack)
                    serializer.text(child.tail)
                    serializer.end_entity()
                serializer.end_entity()

            elif elem.tag in ('span','em','b','left','right'):
                serializer.start_inline(stylestack)
                serializer.text(elem.text)
                for child in elem:
                    print_elem(stylestack,serializer,child)
                    serializer.start_inline(stylestack)
                    serializer.text(child.tail)
                    serializer.end_entity()
                serializer.end_entity()

            elif elem.tag == 'value':
                serializer.start_inline(stylestack)
                serializer.pre(format_value( 
                                              elem.text,
                                              decimals=stylestack.get('value-decimals'),
                                              width=stylestack.get('value-width'),
                                              decimals_separator=stylestack.get('value-decimals-separator'),
                                              thousands_separator=stylestack.get('value-thousands-separator'),
                                              autoint=(stylestack.get('value-autoint') == 'on'),
                                              symbol=stylestack.get('value-symbol'),
                                              position=stylestack.get('value-symbol-position') 
                                            ))
                serializer.end_entity()

            elif elem.tag == 'line':
                width = stylestack.get('width')
                if stylestack.get('size') in ('double', 'double-width'):
                    width = width / 2

                lineserializer = XmlLineSerializer(stylestack.get('indent')+indent,stylestack.get('tabwidth'),width,stylestack.get('line-ratio'))
                serializer.start_block(stylestack)
                for child in elem:
                    if child.tag == 'left':
                        print_elem(stylestack,lineserializer,child,indent=indent)
                    elif child.tag == 'right':
                        lineserializer.start_right()
                        print_elem(stylestack,lineserializer,child,indent=indent)
                serializer.pre(lineserializer.get_line())
                serializer.end_entity()

            elif elem.tag == 'ul':
                serializer.start_block(stylestack)
                bullet = stylestack.get('bullet')
                for child in elem:
                    if child.tag == 'li':
                        serializer.style(stylestack)
                        serializer.raw(' ' * indent * stylestack.get('tabwidth') + bullet)
                    print_elem(stylestack,serializer,child,indent=indent+1)
                serializer.end_entity()

            elif elem.tag == 'ol':
                cwidth = len(str(len(elem))) + 2
                i = 1
                serializer.start_block(stylestack)
                for child in elem:
                    if child.tag == 'li':
                        serializer.style(stylestack)
                        serializer.raw(' ' * indent * stylestack.get('tabwidth') + ' ' + (str(i)+')').ljust(cwidth))
                        i = i + 1
                    print_elem(stylestack,serializer,child,indent=indent+1)
                serializer.end_entity()

            elif elem.tag == 'pre':
                serializer.start_block(stylestack)
                serializer.pre(elem.text)
                serializer.end_entity()

            elif elem.tag == 'hr':
                width = stylestack.get('width')
                if stylestack.get('size') in ('double', 'double-width'):
                    width = width / 2
                serializer.start_block(stylestack)
                serializer.text('-'*width)
                serializer.end_entity()

            elif elem.tag == 'br':
                serializer.linebreak()

            elif elem.tag == 'img':
                if 'src' in elem.attrib and 'data:' in elem.attrib['src']:
                    self.print_base64_image(elem.attrib['src'])

            elif elem.tag == 'barcode' and 'encoding' in elem.attrib:
                serializer.start_block(stylestack)
                self.barcode(strclean(elem.text),elem.attrib['encoding'])
                serializer.end_entity()

            elif elem.tag == 'cut':
                self.cut()
            elif elem.tag == 'partialcut':
                self.cut(mode='part')
            elif elem.tag == 'cashdraw':
                self.cashdraw(2)
                self.cashdraw(5)
            elif elem.tag == 'code128':
                print("\n\n element tag code128 is found")
                serializer.start_block(stylestack)
                img_instance = self.code128_image(strclean(elem.text))
#               convert PIL image.image object to base64 string 
                buffer = io.StringIO()
                img_instance.save(buffer, format="JPEG")
                img_str = base64.b64encode(buffer.getvalue())
#               base64 string pass to print 
#                 print"\n\n element tag code128 is found img_str",img_str
                self.print_base64_image(img_str)
                serializer.end_entity()

            stylestack.pop()

        try:
            stylestack      = StyleStack() 
            serializer      = XmlSerializer(self)
            root            = ET.fromstring(xml.encode('utf-8'))

            self._raw(stylestack.to_escpos())

            print_elem(stylestack,serializer,root)

            if 'open-cashdrawer' in root.attrib and root.attrib['open-cashdrawer'] == 'true':
                self.cashdraw(2)
                self.cashdraw(5)
            if not 'cut' in root.attrib or root.attrib['cut'] == 'true' :
                self.cut()

        except Exception as e:
            errmsg = str(e)+'\n'+'-'*48+'\n'+traceback.format_exc() + '-'*48+'\n'
            self.text(errmsg)
            self.cut()

            raise e

    def text(self,txt):
        """ Print Utf8 encoded alpha-numeric text """
        if not txt:
            return
        try:
            txt = txt.decode('utf-8')
        except:
            try:
                txt = txt.decode('utf-16')
            except:
                pass

        self.extra_chars = 0
        
        def encode_char(char):  
            """ 
            Encodes a single utf-8 character into a sequence of 
            esc-pos code page change instructions and character declarations 
            """ 
            char_utf8 = char.encode('utf-8')
            encoded  = ''
            encoding = self.encoding # we reuse the last encoding to prevent code page switches at every character
            encodings = {
                    # TODO use ordering to prevent useless switches
                    # TODO Support other encodings not natively supported by python ( Thai, Khazakh, Kanjis )
                    'cp437': TXT_ENC_PC437,
                    'cp850': TXT_ENC_PC850,
                    'cp852': TXT_ENC_PC852,
                    'cp857': TXT_ENC_PC857,
                    'cp858': TXT_ENC_PC858,
                    'cp860': TXT_ENC_PC860,
                    'cp863': TXT_ENC_PC863,
                    'cp865': TXT_ENC_PC865,
                    'cp866': TXT_ENC_PC866,
                    'cp862': TXT_ENC_PC862,
                    'cp720': TXT_ENC_PC720,
                    'iso8859_2': TXT_ENC_8859_2,
                    'iso8859_7': TXT_ENC_8859_7,
                    'iso8859_9': TXT_ENC_8859_9,
                    'cp1254'   : TXT_ENC_WPC1254,
                    'cp1255'   : TXT_ENC_WPC1255,
                    'cp1256'   : TXT_ENC_WPC1256,
                    'cp1257'   : TXT_ENC_WPC1257,
                    'cp1258'   : TXT_ENC_WPC1258,
                    'katakana' : TXT_ENC_KATAKANA,
            }
            remaining = copy.copy(encodings)

            if not encoding :
                encoding = 'cp437'

            while True: # Trying all encoding until one succeeds
                try:
                    if encoding == 'katakana': # Japanese characters
                        if jcconv:
                            # try to convert japanese text to a half-katakanas 
                            kata = jcconv.kata2half(jcconv.hira2kata(char_utf8))
                            if kata != char_utf8:
                                self.extra_chars += len(kata.decode('utf-8')) - 1
                                # the conversion may result in multiple characters
                                return encode_str(kata.decode('utf-8')) 
                        else:
                             kata = char_utf8
                        
                        if kata in TXT_ENC_KATAKANA_MAP:
                            encoded = TXT_ENC_KATAKANA_MAP[kata]
                            break
                        else: 
                            raise ValueError()
                    else:
                        encoded = char.encode(encoding)
                        break

                except ValueError: #the encoding failed, select another one and retry
                    if encoding in remaining:
                        del remaining[encoding]
                    if len(remaining) >= 1:
                        encoding = list(remaining.items())[0][0]
                    else:
                        encoding = 'cp437'
                        encoded  = '\xb1'    # could not encode, output error character
                        break;

            if encoding != self.encoding:
                # if the encoding changed, remember it and prefix the character with
                # the esc-pos encoding change sequence
                self.encoding = encoding
                encoded = encodings[encoding] + encoded

            return encoded
        
        def encode_str(txt):
            buffer = ''
            for c in txt:
                buffer += encode_char(c)
            return buffer

        txt = encode_str(txt)

        # if the utf-8 -> codepage conversion inserted extra characters, 
        # remove double spaces to try to restore the original string length
        # and prevent printing alignment issues
        while self.extra_chars > 0: 
            dspace = txt.find('  ')
            if dspace > 0:
                txt = txt[:dspace] + txt[dspace+1:]
                self.extra_chars -= 1
            else:
                break

        self._raw(txt)
        
    def set(self, align='left', font='a', type='normal', width=1, height=1):
        """ Set text properties """
        # Align
        if align.upper() == "CENTER":
            self._raw(TXT_ALIGN_CT)
        elif align.upper() == "RIGHT":
            self._raw(TXT_ALIGN_RT)
        elif align.upper() == "LEFT":
            self._raw(TXT_ALIGN_LT)
        # Font
        if font.upper() == "B":
            self._raw(TXT_FONT_B)
        else:  # DEFAULT FONT: A
            self._raw(TXT_FONT_A)
        # Type
        if type.upper() == "B":
            self._raw(TXT_BOLD_ON)
            self._raw(TXT_UNDERL_OFF)
        elif type.upper() == "U":
            self._raw(TXT_BOLD_OFF)
            self._raw(TXT_UNDERL_ON)
        elif type.upper() == "U2":
            self._raw(TXT_BOLD_OFF)
            self._raw(TXT_UNDERL2_ON)
        elif type.upper() == "BU":
            self._raw(TXT_BOLD_ON)
            self._raw(TXT_UNDERL_ON)
        elif type.upper() == "BU2":
            self._raw(TXT_BOLD_ON)
            self._raw(TXT_UNDERL2_ON)
        elif type.upper == "NORMAL":
            self._raw(TXT_BOLD_OFF)
            self._raw(TXT_UNDERL_OFF)
        # Width
        if width == 2 and height != 2:
            self._raw(TXT_NORMAL)
            self._raw(TXT_2WIDTH)
        elif height == 2 and width != 2:
            self._raw(TXT_NORMAL)
            self._raw(TXT_2HEIGHT)
        elif height == 2 and width == 2:
            self._raw(TXT_2WIDTH)
            self._raw(TXT_2HEIGHT)
        else: # DEFAULT SIZE: NORMAL
            self._raw(TXT_NORMAL)


    def cut(self, mode=''):
        """ Cut paper """
        # Fix the size between last line and cut
        # TODO: handle this with a line feed
        self._raw("\n\n\n\n\n\n")
        if mode.upper() == "PART":
            self._raw(PAPER_PART_CUT)
        else: # DEFAULT MODE: FULL CUT
            self._raw(PAPER_FULL_CUT)


    def cashdraw(self, pin):
        """ Send pulse to kick the cash drawer """
        if pin == 2:
            self._raw(CD_KICK_2)
        elif pin == 5:
            self._raw(CD_KICK_5)
        else:
            raise CashDrawerError()


    def hw(self, hw):
        """ Hardware operations """
        if hw.upper() == "INIT":
            self._raw(HW_INIT)
        elif hw.upper() == "SELECT":
            self._raw(HW_SELECT)
        elif hw.upper() == "RESET":
            self._raw(HW_RESET)
        else: # DEFAULT: DOES NOTHING
            pass


    def control(self, ctl):
        """ Feed control sequences """
        if ctl.upper() == "LF":
            self._raw(CTL_LF)
        elif ctl.upper() == "FF":
            self._raw(CTL_FF)
        elif ctl.upper() == "CR":
            self._raw(CTL_CR)
        elif ctl.upper() == "HT":
            self._raw(CTL_HT)
        elif ctl.upper() == "VT":
            self._raw(CTL_VT)