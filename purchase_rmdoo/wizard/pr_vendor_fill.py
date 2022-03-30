# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class ReplenishRequestVendorFill(models.TransientModel):
    _name = 'replenish.request.vendorfill'
    _description = 'Purchase Request Vendor Fill'
    
    product_replenish_request_id = fields.Many2one('product.replenish.request', string='Request', required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    
    
    def button_fill(self):
        if self.ensure_one():
            self.env['product.supplierinfo'].create({
                'min_qty':1.0,
                'price':self.price_unit,
                'name':self.partner_id.id,
                'currency_id':self.currency_id.id,
                'product_id':self.product_replenish_request_id.product_id.id,
                'product_tmpl_id':self.product_replenish_request_id.product_tmpl_id.id,
            })
            return self.product_replenish_request_id and self.product_replenish_request_id.replenish_request_id.launch_replenishment()
        else:
            return False
