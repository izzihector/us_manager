# -*- coding: utf-8 -*-

# ===================================================
# |     Developmeny By : Brata Bayu S, S.Kom        |
# ===================================================


from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError, ValidationError
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class mcs_product_custom(models.Model):
    _inherit 		= 'product.template'
    _description 	= 'Setting Product Attribut Custom Sales Price'

    brt 			= fields.Char()

    def action_generate_priceitem(self):
    	product = self.env['product.template'].sudo().search([('is_consignment', '=', False),('type', '=', 'product')])
    	producttotal = self.env['product.template'].search_count([('is_consignment', '=', False),('type', '=', 'product')])
    	print('=================================',producttotal)
    	for x in product:
    		PriceListid = self.env['product.pricelist'].sudo().search([('name', '=', 'Public Pricelist')],limit=1)
    		Product = self.env['product.product'].sudo().search([('product_tmpl_id', '=', x.id)],limit=1)
    		print('================================= NAMA PRODUCT', x.id, x.name)
    		print('================================= NAMA PRODUCT', Product.id, Product.name)
    		# print('================================= temlate PRODUCT', x.product_id.id)
    		nama = 'Variant :'+x.name
    		# self.env.cr.commit()
    		# self.env.cr.execute("""INSERT INTO product_pricelist_item (pricelist_id, name, min_quantity, fixed_price, product_tmpl_id) 
    		# 						VALUES  1, %s,1,%s,%s""", (str(nama),float(x.standard_price),int(x.id),))

    		createPrice = self.env['product.pricelist.item'].sudo().create(
                                                        {
                                                            'applied_on': '0_product_variant',
                                                            'base': 'list_price',
                                                            'compute_price': 'fixed',
                                                            'pricelist_id': 1,
                                                            'name': 'Variant :'+x.name,
                                                            'min_quantity': 1,
                                                            'active': 't',
                                                            'currency_id': 12,
                                                            'fixed_price': x.standard_price,
                                                            'company_id': 1,
                                                            'product_id': Product.id,
                                                            'product_tmpl_id':x.id
                                                        }
                                                    )

      #  