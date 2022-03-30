# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class HkWishlistApi(http.Controller):

    @http.route('/wishlist_api/<string:action>/', type='json', auth='public')
    def index(self, action=None, **kw):
        # value = dict(kw)
        # data = value['data']
        data = request.jsonrequest
        headers = request.httprequest.headers
        list_data = []
        Wishlist = request.env['product.wishlist'].sudo()

        code = ""
        message = ""

        if 'Sarinah-Key' in headers:
            auth_user = request.env['ir.config_parameter'].sudo().get_param('mcs_sarinah_key')
            if headers['Sarinah-Key'] == auth_user:
                if 'user_id' in data:
                    user = request.env['res.users'].sudo().search([('id', '=', data['user_id'])])
                    if action == 'add':
                        wish = Wishlist.search(
                            [('partner_id', '=', user.partner_id.id), ('product_id', '=', data['product_id'])])
                        if not wish:
                            Wishlist.create({
                                'partner_id': user.partner_id.id,
                                'product_id': data['product_id'],
                                'currency_id': 12,
                                'pricelist_id': 1,
                                'price': data['price'],
                                'website_id': 1,
                            })
                        else:
                            message = "Duplicated wishlisted product for this user."
                            code = "400"
                    elif action == 'delete':
                        wish = Wishlist.search([('partner_id', '=', user.partner_id.id), ('product_id', '=', data['product_id'])])
                        if wish:
                            wish.unlink()
                        else:
                            message = "Cannot Delete! This product is not in wishlist of this user."
                            code = "400"
                    elif action == 'list':
                        wishes = Wishlist.search([('partner_id', '=', user.partner_id.id)])
                        for wish in wishes:
                            list_data.append({
                                'product_id': wish.product_id.id,
                                'price': wish.price
                            })
                    else:
                        message = "Invalid Parameter"
                        code = "400"
                else:
                    message = "Please provide User ID"
                    code = "400"
            else:
                message = "Invalid Key!"
                code = "400"
        else:
            message = "Please provide valid key in headers!"
            code = "400"

        if not message:
            code = "200"
            message = "Success"

        data = {
            "code": code,
            "message": message,
            "data": list_data
        }

        # jess = json.dumps(data)
        return data

