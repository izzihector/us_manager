# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests, json
import logging


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def check_wallet_vernoss(self, partner):
        headers = {
            'content-type': "application/json",
            'Authorization': "Bearer %s" % self.env['ir.config_parameter'].sudo().get_param('vernoss_access_token'),
            'Api-Key': self.env['ir.config_parameter'].sudo().get_param('vernoss_api_key'),
        }

        partner_id = partner.pop('id', False)
        loyalty_member = ""
        if partner_id:
            loyalty_member = self.env['res.partner'].browse(partner_id).loyalty_id

        url = "%s/loyalty-member/get-wallet?loyaltyMemberId=%s" % (
            self.env['ir.config_parameter'].sudo().get_param('vernoss_base_url'),
            loyalty_member
        )

        try:
            res = requests.get(url, headers=headers, verify=False)
            data = json.loads(res.content.decode('utf-8'))
        except:
            return False

        if data:
            if 'responseCode' in data:
                if data['responseCode'] == '00':
                    if 'payload' in data:
                        if data['payload']:
                            self.browse(partner_id).write({
                                'loyalty_points': data['payload']['totalAvailablePoints']
                            })
                else:
                    return False

        return partner_id

    @api.model
    def create_from_ui(self, partner):
        """ create or modify a partner from the point of sale ui.
            partner contains the partner's fields. """
        # image is a dataurl, get the data after the comma
        if partner.get('image_1920'):
            partner['image_1920'] = partner['image_1920'].split(',')[1]
        partner_id = partner.pop('id', False)
        if partner_id:  # Modifying existing partner
            self.browse(partner_id).write(partner)
        else:
            partner['lang'] = self.env.user.lang
            partner['is_loyalty'] = True
            partner_id = self.create(partner).id
        return partner_id


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def sendEarnTransaction(self, order):
        headers = {
            'content-type': "application/json",
            'Authorization': "Bearer %s" % self.env['ir.config_parameter'].sudo().get_param('vernoss_access_token'),
            'Api-Key': self.env['ir.config_parameter'].sudo().get_param('vernoss_api_key'),
        }

        partner_id = order.pop('partner_id', False)
        loyalty_member = ""
        if partner_id:
            loyalty_member = self.env['res.partner'].browse(partner_id).loyalty_id

        point = 0
        point_avg = 0
        total_line = 0
        for line in order['lines']:
            total_line += 1
            if 'reward_id' in line[2]:
                point = -1 * line[2]['price_subtotal_incl']

                url = "%s/loyalty-member/burn-transaction" % (
                    self.env['ir.config_parameter'].sudo().get_param('vernoss_base_url')
                )

                pay = {
                        "loyaltyMemberId": loyalty_member,
                        "productCode": "VOUCHER_SAR",
                        "companyCode": "SARID",
                        "productPrice": 10000,
                        "burnAmount": point,
                        "burnType": "EXACT",
                        "locationCode": "SARID_LOC",
                        "storeCode": "SARINAH_STORE",
                        "channelReference": "POS"
                    }

                try:
                    res = requests.post(url, json=pay, headers=headers, verify=False)
                    data = json.loads(res.content.decode('utf-8'))
                except:
                    return False

                if data:
                    if 'responseCode' in data:
                        if data['responseCode'] != '00':
                            return {'responseMessage': data['responseMessage']}
        if point != 0:
            point_avg = point / total_line

        url = "%s/loyalty-member/earn-transaction" % (
            self.env['ir.config_parameter'].sudo().get_param('vernoss_base_url')
        )

        basketItems = []
        for line in order['lines']:
            product = self.env['product.product'].search([('id', '=', line[2]['product_id'])])
            basketItems.append({
                'productCode': product.default_code,
                'retailValueBeforeTax': line[2]['price_subtotal_incl'] - point,
            })

        paymentItems = []
        for line in order['statement_ids']:
            product = self.env['pos.payment.method'].search([('id', '=', line[2]['payment_method_id'])])
        paymentItems.append({
            'paymentMethod': "302",
            'paymentAmount': order['amount_total'] - point_avg,
        })

        payload = {
            "loyaltyMemberId": loyalty_member,
            "locationCode": "SARID_LOC",
            "storeCode": "SARINAH_STORE",
            "channelReference": "POS",
            "basketItems": basketItems,
            "totalPayment": order['amount_total'] - point_avg,
            "paymentItems": paymentItems
        }
        try:
            res = requests.post(url, json=payload, headers=headers, verify=False)
            data = json.loads(res.content.decode('utf-8'))
            _logger.info("Vernoss Response :%s " % (data))
        except:
            _logger.info("Error Vernoss ")
            return {'responseMessage': "Check Your Internet Connection!"}
        if data:
            if 'responseCode' in data:
                if data['responseCode'] in ['00', '10']:
                    if 'payload' in data:
                        earn_points = 0
                        total_points = 0
                        if "memberWallet" in data['payload']:
                            self.env['res.partner'].browse(partner_id).write({
                                'loyalty_points': data['payload']['memberWallet']['totalAvailablePoints']
                            })
                            total_points = data['payload']['memberWallet']['totalAvailablePoints']

                        if "pointResult" in data['payload']:
                            for point in data['payload']["pointResult"]:
                                earn_points += point["earnedPoints"]

                        return {
                            'point': total_points,
                            'earn_points': earn_points
                        }
                else:
                    return {'responseMessage': data['responseMessage']}
        return {'responseMessage': "Check Your Internet Connection!"}

    @api.model
    def create_from_ui(self, orders, draft=False):
        order_ids = super(PosOrder, self).create_from_ui(orders, draft)
        for order in self.sudo().browse([o['id'] for o in order_ids]):
            if order.loyalty_points != 0 and order.partner_id:
                order.partner_id.loyalty_points -= order.loyalty_points
        return order_ids
