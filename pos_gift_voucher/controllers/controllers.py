# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import requests, json

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

_BASE_URL = "https://dev-gv.vernoss.com:8001"
_USERNAME = "testify"
_PASSWORD = "rahasia"
_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpbklkIjoidGVzdGlmeSIsImlkIjoiNjE3YmYzMDk5YjYyNDQ2NzlkM2E5MTlhIiwiZGlzcGxheU5hbWUiOiJUZXN0aW5nIiwicGVybWlzc2lvbnMiOlsic3lzdGVtX2FkbWluIl0sInJvbGVzIjpbInN5c3RlbV9hZG1pbiJdLCJjbGllbnRDb2RlIjoiIiwiZW50aXR5SWQiOiIiLCJpYXQiOjE2Mzc1NjUzNDAsImV4cCI6MTYzNzY1MTc0MH0.sUr3RFiDFc2Sv08fxBxlii_8osXSLj1yP4uXCRlEln8"
_MAX_USE_COUNT = 3
_EXPIRED_IN = 7

def generate_error(field, message):
    return { field: message }

def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

class PosGiftVoucher(http.Controller):
    @http.route('/api/voucher/check', methods=['POST'], csrf=False, auth='public')
    def voucher_check(self, voucher_code=False, **kw):
        token = self.vernoss_get_token()
        if token is False:
            return False

        headers = {
            'content-type' : "application/json",
            'Authorization' : str("Bearer %s" % token),
        }

        url = "%s/api/v1/voucher/info?voucherCode=%s" % (_BASE_URL, voucher_code)

        res = requests.get(url, headers=headers, verify=False)
        voucher_api = json.loads(res.content.decode('utf-8'))

        success = False
        message = ""
        obj = False

        if voucher_api is not False:
            if 'status' in voucher_api:
                if voucher_api['status'] == 0:
                    if 'data' in voucher_api:
                        if 'useable' in voucher_api['data']:
                            if voucher_api['data']['useable'] == True:
                                obj = voucher_api['data']
                                success = True
                            else:
                                message = "Vernoss: Already exceeded the use count."
                else:
                    message = "Vernoss: %s" % voucher_api['error']
        data = {
            "success": success,
            "message": message,
            "data": obj,
        }

        return json.dumps(data, default=date_handler)

    @http.route('/api/voucher/activation', methods=['POST'], csrf=False, auth='public')
    def voucher_activation(self, order_id=False, voucher_code=False, **kw):
        value = dict(kw)

        token = self.vernoss_get_token()
        if token is False:
            return False

        by = False 
        success = False
        message = ''
        voucher_code_arr = []
        noVoucher = []
        activedVoucher = []
        noCoupon = []
        noOrder = []
        succesVoucher = []
        failVoucher = []

        # voucher = request.env['gift.voucher'].sudo().search([('voucher_serial_no', '=', voucher_code)])
        # if len(voucher) < 1:

        if order_id:
            if voucher_code:
                order = request.env['pos.order'].sudo().search([('pos_reference', '=', order_id)], limit=1)
                if len(order) > 0:
                    voucher_code_arr = voucher_code.split(", ")
                    voucher_count = len(voucher_code_arr)
                    order_item_qty = 0

                    for line in order.lines:
                        order_item_qty += int(line.qty) 

                    if voucher_count <= order_item_qty:
                        for voucher_code_piece in voucher_code_arr:
                            headers = {
                                'content-type' : "application/json",
                                'Authorization' : str("Bearer %s" % token),
                            }

                            url = "%s/api/v1/voucher/info?voucherCode=%s" % (_BASE_URL, voucher_code_piece)

                            res = requests.get(url, headers=headers, verify=False)
                            voucher_api = json.loads(res.content.decode('utf-8'))

                            voucher_exist = False
                            if voucher_api is not False:
                                if 'status' in voucher_api:
                                    if voucher_api['status'] == 0:
                                        voucher_exist = True

                            if voucher_exist is True:
                                if voucher_api['data']['status'] == 'stockInStore':
                                    coupon = request.env['product.product'].sudo().search([
                                            ('coupon', '=', True),
                                            ('list_price', '=', voucher_api['data']['denom']),
                                        ], limit=1)
                                    if coupon:
                                        pos_order_line = request.env['pos.order.line'].sudo().search([
                                                ('product_id', '=', coupon.id),
                                                ('order_id', '=', order.id),
                                            ], limit=1)
                                        if pos_order_line:
                                            # transaction begin
                                            headers = {
                                                'content-type' : "application/json",
                                                'Authorization' : str("Bearer %s" % token),
                                            }
                                            url = "%s/api/v1/voucher/activation" % _BASE_URL
                                            payload = {
                                                "voucherCodes": [voucher_code_piece]
                                            }
                                            res = requests.put(url, json=payload, headers=headers, verify=False)
                                            data2 = json.loads(res.content.decode('utf-8'))
                                            if 'status' in data2 and data2['status'] == 0: 
                                                voucher_activated_qty = pos_order_line.voucher_activated_qty
                                                pos_order_line.voucher_activated_qty = voucher_activated_qty + 1

                                                order_date = order.date_order 
                                                request.env['gift.voucher'].create({
                                                    'voucher_name': coupon.name,
                                                    'qty': 1,
                                                    'uom': coupon.uom_id.id,
                                                    'company_id': False,
                                                    'date': order_date,
                                                    'voucher_serial_no': voucher_code_piece,
                                                    'source': order_id,
                                                    'redeemed_out': True,
                                                    'amount': voucher_api['data']['denom'],
                                                    'remaining_amt': voucher_api['data']['remainValue'],
                                                    'voucher_validity': 1000,
                                                    'last_date': datetime.strptime(str(datetime.today().date()), '%Y-%m-%d') + relativedelta(months=100),
                                                    'product_id': coupon.id,
                                                    'used_amt': 0,
                                                })

                                                succesVoucher.append(voucher_code_piece)
                                            else:
                                                failVoucher.append(voucher_code_piece)
                                        else:
                                            noOrder.append(voucher_code_piece)
                                    else:
                                        noCoupon.append(voucher_code_piece)
                                else:
                                    activedVoucher.append(voucher_code_piece)
                            else:
                                noVoucher.append(voucher_code_piece)
                    else:
                        message = "The qty of scanned vouchers exceeds the limit"
                else:
                    message = "Order ID not found"
            else:
                message = "Voucher code not set"
        else:
            message = "Order ID not set"

        # else:
            # message = "Voucher code has been activated before" 

        if len(noVoucher) > 0 or len(activedVoucher) > 0 or len(noCoupon) > 0 or len(noOrder) > 0 or len(failVoucher) > 0 or len(succesVoucher) > 0:
            message = ""

        if len(succesVoucher) > 0:
            message += "Voucher success to activate: %s ... " % (', '.join(succesVoucher))

        if len(noVoucher) > 0:
            message += "Voucher not found: %s ... " % (', '.join(noVoucher))

        if len(activedVoucher) > 0:
            message += "Voucher has been activated or used: %s ... " % (', '.join(activedVoucher))

        if len(noCoupon) > 0:
            message += "Voucher has no master data: %s ... " % (', '.join(noCoupon))

        if len(noOrder) > 0:
            message += "Voucher has no order: %s ... " % (', '.join(noOrder))

        if len(failVoucher) > 0:
            message += "Voucher failed to activate: %s ... " % (', '.join(failVoucher))

        data = {
            "by": by,
            "success": success,
            "message": message,
        }

        return json.dumps(data, default=date_handler)

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
            if 'accessToken' in data and data['accessToken'] is not False:
                token = data['accessToken']

        return token

    def vernoss_voucher_activation(self, voucherCode, _token = False):
        if _token is False:
            token = self.vernoss_get_token()
        else:
            token = _token

        if token is False:
            return False

        headers = {
            'content-type' : "application/json",
            'Authorization' : str("Bearer %s" % token),
        }

        url = "%s/api/v1/voucher/activation" % _BASE_URL

        payload = {
            "voucherCodes": [voucherCode] 
        }

        data = False

        try:
            res = requests.put(url, json=payload, headers=headers, verify=False)
            data = json.loads(res.content.decode('utf-8'))
        except: 
            return False

        res = False

        if data is not False:
            if 'data' in data and 'status' in data['data'] and data['data']['status'] == 0:
                res = True

        return res

    def vernoss_voucher_info(self, voucherCode, _token = False):
        if _token is False:
            token = self.vernoss_get_token()
        else:
            token = _token

        if token is False:
            return False

        headers = {
            'content-type' : "application/json",
            'Authorization' : str("Bearer %s" % token),
        }

        url = "%s/api/v1/voucher/info?voucherCode=%s" % (_BASE_URL, voucherCode)

        data = False

        try:
            res = requests.get(url, headers=headers, verify=False)
            data = json.loads(res.content.decode('utf-8'))
        except: 
            return False 

        return data