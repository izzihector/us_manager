# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import math
import logging
_logger = logging.getLogger(__name__)

class ProductCustom(http.Controller):
    @http.route('/product/generate_pricelist', auth='public')
    def generate_pricelist(self, **kw):
        product_products = request.env['product.product'].sudo().search([('is_consignment', '=', False), ('type', '=', 'product')])

        listdata = []
        for product_product in product_products:
            pricelist = request.env['product.pricelist.item'].sudo().search([('product_id', '=', product_product.id), ('applied_on', '=', '0_product_variant')])
            if len(pricelist) < 1 and product_product.lst_price > 0:
                res = request.env['product.pricelist.item'].sudo().create({
                    'pricelist_id': 1,
                    'product_id': product_product.id,
                    'product_tmpl_id': product_product.product_tmpl_id.id,
                    'fixed_price' : product_product.lst_price,
                    'applied_on': '0_product_variant',
                    'base': 'list_price',
                    'compute_price': 'fixed',
                    'min_quantity': 0,
                    'active': 't',
                })
                if res:
                    listdata.append({
                        "id": product_product.id,
                        "name": product_product.name,
                        "price": product_product.lst_price,
                    })
        
        data = {
            "result": listdata,
            "total": len(listdata),
        }

        jess = json.dumps(data)
        return jess