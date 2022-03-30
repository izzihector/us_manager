/* Copyright 2020 Pablo Carrio Garcia <david.gomez@aselcis.com>
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
*/

odoo.define('pos_mobile_barcode_canner.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var chrome = require('point_of_sale.chrome');
    var gui = require('point_of_sale.gui');
    var PosBaseWidget = require('point_of_sale.BaseWidget');

    var CameraScannerScreenWidget = screens.ScreenWidget.extend({
        template:'CameraScannerScreenWidget',

        _codeReader: null,
        _selectedDeviceId: null,

        start: function(){
          var self = this;

          this.$('.back').click(function(){
              self.gui.back();
          });

          Quagga.onProcessed(function(result) {
              var drawingCtx = Quagga.canvas.ctx.overlay,
                  drawingCanvas = Quagga.canvas.dom.overlay;

              if (result) {
                  if (result.boxes) {
                      drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
                      result.boxes.filter(function (box) {
                          return box !== result.box;
                      }).forEach(function (box) {
                          Quagga.ImageDebug.drawPath(box, {x: 0, y: 1}, drawingCtx, {color: "green", lineWidth: 2});
                      });
                  }

                  if (result.box) {
                      Quagga.ImageDebug.drawPath(result.box, {x: 0, y: 1}, drawingCtx, {color: "#00F", lineWidth: 2});
                  }

                  if (result.codeResult && result.codeResult.code) {
                      Quagga.ImageDebug.drawPath(result.line, {x: 'x', y: 'y'}, drawingCtx, {color: 'red', lineWidth: 3});
                  }
              }
          });
          Quagga.onDetected(function(result) {
              const beep = new Audio("/pos_mobile_barcode_scanner/static/src/sounds/beep.wav");
              beep.play();

              //console.log('SC_RES',result)

              if(result.codeResult.code.startsWith("0")){
                result.codeResult.format = 'upca';
                result.codeResult.code = result.codeResult.code.substring(1);
              }

              const code = {
                  'encoding': 'any',
                  'type': 'product',
                  'code': result.codeResult.code,
                  'base_code': result.codeResult.code,
                  'value': result.codeResult.code
              };

              switch (result.codeResult.format) {
                case 'ean_13':
                  code.encoding = 'ean13'
                  break;
                case 'ean_8':
                  code.encoding = 'ean8'
                  break;
                case 'upc_a':
                  code.encoding = 'upca'
                  break;
                default:
              }

              if (self.pos.scan_product(code)) {
                  if (self.barcode_product_screen) {
                      self.gui.show_screen(self.barcode_product_screen, null, null, true);
                  }
              } else {
                  var show_code;
                  if (code.code.length > 32) {
                      show_code = code.code.substring(0,29)+'...';
                  } else {
                      show_code = code.code;
                  }
                  self.stopScanner();
                  self.gui.show_popup('error-barcode',show_code);
                  self.gui.current_popup.options.cancel = function(){
                    self.startScanner();
                  }

              }
          });

          self.$("#deviceSelection").change(function(){
            self._selectedDeviceId = self.$(this).val();
            Quagga.stop();
            self.initReader();
          })
        },

        initReader: function(){
          var self = this;

          var streamLabel = Quagga.CameraAccess.getActiveStreamLabel();

          Quagga.init({
            inputStream: {
                type : "LiveStream",
                constraints: {
                    width: {min: 1024},
                    height: {min: 720},
                    facingMode: "environment",
                    deviceId: self._selectedDeviceId,
                    aspectRatio: 1
                },
                target: self.$('#camera-video-scanner').get(0)
            },
            locator: {
                patchSize: "medium",
                halfSample: true
            },
            numOfWorkers: 2,
            frequency: 10,
            decoder: {
                readers : ["ean_reader","ean_8_reader"]
            },
            locate: true
          }, function(err) {
              if (err) {
                  console.log(err);
                  return
              }
              self.getDevices();
              Quagga.start();
              console.log("Initialization finished. Ready to start");
          });
        },

        getDevices: function(){
          var self = this;

          var streamLabel = Quagga.CameraAccess.getActiveStreamLabel();

          Quagga.CameraAccess.enumerateVideoDevices()
          .then(function(devices) {
              var $deviceSelection = self.$("#deviceSelection");
              $deviceSelection.empty();

              devices.forEach(function(device) {
                  var $option = new Option((device.label || device.deviceId || device.id),(device.deviceId || device.id))
                  $option.selected = streamLabel === device.label;
                  $deviceSelection.append($option);
              });

              self.$('#sourceSelectPanel').removeClass("oe_hidden");
          });
        },

        stopScanner: function() {
          var self = this;

          self.$('#camera-video-scanner video').each(function(){
            const targetElement = self.$(this).get(0);

            if (targetElement && targetElement.pause) {
                targetElement.pause();
            }
          });

          setTimeout(() => {
              Quagga.pause();
          }, 0)
        },

        endScanner: function() {
          var self = this;

          self.$('#camera-video-scanner video').each(function(){
            const targetElement = self.$(this).get(0);

            if (targetElement && targetElement.pause) {
                targetElement.pause();
            }
          });

          setTimeout(() => {
              Quagga.stop();
          }, 0)
        },

        startScanner: function() {
          var self = this;

          self.$('#camera-video-scanner video').each(function(){
            const targetElement = self.$(this).get(0);

            if (targetElement && targetElement.play) {
                targetElement.play();
            }
          });

          setTimeout(() => {
              Quagga.start();
          }, 0)
        },

        show: function(reset){
            this._super();
            this.initReader();
        },

        close: function(){
            this._super();
            this.endScanner();
        },
    });
    gui.define_screen({name:'camera_scanner', widget: CameraScannerScreenWidget});

    var MobileBCScannerButtonWidget = PosBaseWidget.extend({
        template: 'MobileBCSannerButton',
        init: function(parent, options){
            options = options || {};
            this._super(parent,options);
        },
        renderElement: function(){
            var self = this;
            this._super();
            if(!this.pos.config.iface_pos_bcscanner_enable){
              this.$el.removeClass("oe_hidden");
            }else{
              this.$el.addClass("oe_hidden");
            }
        },
        hide: function(){
            this.$el.addClass('oe_hidden');
        },
        show: function(){
            this.$el.removeClass('oe_hidden');
        },
        start: function(){
            var self = this;

            this.$el.click(function(event){
              if (CameraScannerScreenWidget) {
                  self.gui.show_screen('camera_scanner', null, null, true);
              }
            });
        }
    });

    chrome.Chrome.include({
        build_widgets: function(){
            this.widgets.push({
                'name':   'mobile_barcode_scanner',
                'widget': MobileBCScannerButtonWidget,
                'append':  '.pos-rightheader'
            });
            this._super();
        },
    });

    screens.ProductScreenWidget.include({
        show: function(){
            this._super();
            this.chrome.widget.mobile_barcode_scanner.show();
        },
        close: function(){
            this._super();
            this.chrome.widget.mobile_barcode_scanner.hide();
        }
    });

    return {
        MobileBCScannerButtonWidget: MobileBCScannerButtonWidget
    };
});
