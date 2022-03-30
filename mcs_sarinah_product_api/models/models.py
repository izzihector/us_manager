# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class inheritProductTemplate(models.Model):
    _inherit = 'product.template'

    categ_id = fields.Many2one(index=True)

class inheritProductProduct(models.Model):
    _inherit = 'product.product'

    def generate_pricelist(self):
        product_products = self.env['product.product'].sudo().search([('is_consignment', '=', False)])

        generated = []
        for product_product in product_products:
            pricelist = self.env['product.pricelist.item'].sudo().search([('product_id', '=', product_product.id), ('applied_on', '=', '0_product_variant')])
            if len(pricelist) < 1 and product_product.lst_price > 0:
                res = self.env['product.pricelist.item'].sudo().create({
                    'pricelist_id': 1,
                    'product_id': product_product.id,
                    'fixed_price' : product_product.lst_price,
                    'applied_on': '0_product_variant',
                    'is_generated': False
                })
                if res:
                    generated.append(product_product.name)
        
        print("Jumlah di generate: %s \nData di generate: %s" % (len(generated), ', '.join(generated)))
        _logger.warning("Jumlah di generate: %s \nData di generate: %s" % (len(generated), ', '.join(generated)))
        raise UserError("Jumlah di generate: %s \nData di generate: %s" % (len(generated), ', '.join(generated)))


class inheritResPartner(models.Model):
    _inherit = 'res.partner'

    is_merchant = fields.Boolean(string='Is Merchant?', index=True)
