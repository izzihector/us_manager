# -*- coding: utf-8 -*-

from odoo import models, fields, api

import requests, json
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

_BASE_URL = "https://dev-gv.vernoss.com:8001"
_USERNAME = "testify"
_PASSWORD = "rahasia"
_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpbklkIjoidGVzdGlmeSIsImlkIjoiNjE3YmYzMDk5YjYyNDQ2NzlkM2E5MTlhIiwiZGlzcGxheU5hbWUiOiJUZXN0aW5nIiwicGVybWlzc2lvbnMiOlsic3lzdGVtX2FkbWluIl0sInJvbGVzIjpbInN5c3RlbV9hZG1pbiJdLCJjbGllbnRDb2RlIjoiIiwiZW50aXR5SWQiOiIiLCJpYXQiOjE2Mzc1NjUzNDAsImV4cCI6MTYzNzY1MTc0MH0.sUr3RFiDFc2Sv08fxBxlii_8osXSLj1yP4uXCRlEln8"
_MAX_USE_COUNT = 3
_EXPIRED_IN = 7


class gift_voucher(models.Model):
    _name = 'gift.voucher'
    _description = 'Loyalty Gift Voucher Master'

    state = fields.Selection([
        ('draft', 'Request'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),
    ], 'Status', default='draft', readonly=True)
    source = fields.Char('Source')
    voucher_name = fields.Char('Gift Coupon Name', size=64, required=True)
    coupon_value = fields.Float('Coupon Value', size=64)
    voucher_serial_no = fields.Char('Gift Coupon Serial no.')
    qty = fields.Float('Product qty', size=64)
    uom = fields.Many2one('uom.uom', 'Product Unit of Measure', required=True)
    redeemed_in = fields.Boolean('IN')
    redeemed_out = fields.Boolean('OUT')
    shop_id = fields.Char('Shop')
    company_id = fields.Char('Company')
    date = fields.Date('Creation Date')
    amount = fields.Float('Amount', size=64)
    remaining_amt = fields.Float('Remaining Amount', size=64, default=0.0)
    used_amt = fields.Float('Used Amount', size=64, default=0.0)

    voucher_validity = fields.Integer('Validity', default=1)
    last_date = fields.Date('Expiry Date')
    product_id = fields.Many2one('product.product')

    def vernoss_get_token(self):
        headers = {
            'content-type' : "application/json",
        }

        url = "%s/auth/v1/login" % _BASE_URL

        payload = {
            "loginId" : _USERNAME,
            "password" : _PASSWORD,
        }

        data = False

        try:
            res = requests.post(url, json=payload, headers=headers, verify=False)
            data = json.loads(res.content.decode('utf-8'))
        except:
            return False

        token = False

        if data is not False:
            if data['accessToken'] is not False:
                token = data['accessToken']

        return token

    def vernoss_voucher_use(self, amount, voucherCode):
        token = self.vernoss_get_token()

        print("======================================= amount %s" % amount)
        print("======================================= voucherCode %s" % voucherCode)
        _logger.warning("======================================= amount %s" % amount)
        _logger.warning("======================================= voucherCode %s" % voucherCode)

        if token is False:
            return False

        headers = {
            'content-type' : "application/json",
            'Authorization' : str("Bearer %s" % token),
        }

        url = "%s/api/v1/voucher/use" % _BASE_URL

        payload = {
            "voucherCode": voucherCode,
            "virtualCode": voucherCode,
            "amount": amount
        }

        data = False

        try:
            res = requests.put(url, json=payload, headers=headers, verify=False)
            data = json.loads(res.content.decode('utf-8'))
        except: 
            return False

        res = False

        print("======================================= data %s" % data)
        _logger.warning("======================================= data %s" % data)

        if data is not False:
            if 'data' in data and 'status' in data and data['status'] == 0:
                res = True

        return res

    def approve(self):
        return self.write({'state': 'approve'})

    def cancel(self):
        return self.write({'state': 'cancel'})

    @api.model
    def update_coupon_amount(self, data):
        print("======================================= %s" % data)
        _logger.warning("======================================= %s" % data)
        coupon_id = self.search([('voucher_serial_no', '=', data.get('voucher_serial_no'))])
        # amount = coupon_id.used_amt
        # remaining_amt = coupon_id.amount - (data.get('amt') + amount)
        # used_amt = coupon_id.amount - remaining_amt

        # self.vernoss_voucher_use(data.get('amt'), coupon_id.voucher_serial_no)
        # self.vernoss_voucher_use(coupon_id.amount, coupon_id.voucher_serial_no)
        headers = {
            'content-type' : "application/json",
        }

        url = "%s/auth/v1/login" % _BASE_URL

        payload = {
            "loginId" : _USERNAME,
            "password" : _PASSWORD,
        }

        res = requests.post(url, json=payload, headers=headers, verify=False)
        res1 = json.loads(res.content.decode('utf-8'))

        token = False

        if res1 is not False:
            if res1['accessToken'] is not False:
                token = res1['accessToken']

        # amount = coupon_id.product_id.list_price
        amount = data.get('amt') if data.get('amt') <= coupon_id.product_id.list_price else coupon_id.product_id.list_price
        voucherCode = data.get('voucher_serial_no')

        print("======================================= amount %s" % amount)
        print("======================================= voucherCode %s" % voucherCode)
        _logger.warning("======================================= amount %s" % amount)
        _logger.warning("======================================= voucherCode %s" % voucherCode)

        headers = {
            'content-type' : "application/json",
            'Authorization' : str("Bearer %s" % token),
        }

        url = "%s/api/v1/voucher/use" % _BASE_URL

        payload = {
            "voucherCode": voucherCode,
            "virtualCode": voucherCode,
            "amount": amount
        }

        res = requests.put(url, json=payload, headers=headers, verify=False)
        res2 = json.loads(res.content.decode('utf-8'))

        print("======================================= res2 %s" % res2)
        _logger.warning("======================================= res2 %s" % res2)

        coupon_id.write({'remaining_amt': coupon_id.amount - amount,
                             'used_amt': amount})


        if (coupon_id.amount - amount) > 0:
            pos_order = self.env['pos.order'].search([('pos_reference', '=', coupon_id.source)], limit=1)
            if pos_order:
                omset_voucher = pos_order.omset_voucher
                pos_order.omset_voucher = omset_voucher + (coupon_id.amount - amount)
    
        # if not remaining_amt < 0.0:
        #     coupon_id.write({'remaining_amt': remaining_amt,
        #                      'used_amt': used_amt})
        # else:
        #     coupon_id.write({'remaining_amt': 0.0,
        #                      'used_amt': coupon_id.amount})

    @api.model
    def create(self, vals):
        res = super(gift_voucher, self).create(vals)
        res.remaining_amt = vals.get('amount')
        return res

    # def write(self, vals):
    #     res = self.vernoss_voucher_use(100, self.voucher_serial_no)

    #     raise UserError(str(res))

class product_template(models.Model):
    _inherit = "pos.order.line"

    voucher_activated_qty = fields.Integer()

class product_template(models.Model):
    _inherit = "product.template"

    is_coupon = fields.Boolean('Coupon')
    coupon = fields.Boolean('Coupon')
    validity = fields.Integer('Coupon Validity(days)', default=1, help='Coupon validity in days from the date of sale')
    is_prepaid_card = fields.Boolean('Is Prepaid Card')

    @api.onchange('coupon')
    def on_click_of_coupon(self):
        if not self.coupon:
            self.type = 'consu'
            self.is_coupon = False
        else:
            self.type = 'service'
            self.is_coupon = True

class posPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    for_gift_coupens = fields.Boolean('For Gift Coupons')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('coupon')
    def on_click_of_coupon(self):
        if not self.coupon:
            self.type = 'consu'
        else:
            self.type = 'service'
