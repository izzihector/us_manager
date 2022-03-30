# -*- coding: utf-8 -*-
from odoo import api, fields, models


class WizardProductApproval(models.TransientModel):
    _name = 'wizard.product.approval'
    _description = 'Wizard Product Approval'

    sale_ok = fields.Boolean(string="Publish on SO?")
    available_in_pos = fields.Boolean(string="Publish on POS?")
    is_published = fields.Boolean(string="Publish on Ecommerce?")

    def action_confirm(self):
        product_ids = self.env.context['product_tmpl_ids']
        products = self.env['product.template'].search(['|', ('active', '=', True), ('active', '=', False), ('id', 'in', product_ids)])
        products.write({
            'active': True,
            'sale_ok': self.sale_ok,
            'available_in_pos': self.available_in_pos,
            'is_published': self.is_published
        })
        variants = self.env['product.product'].search(
            [('product_tmpl_id', 'in', products.ids), ('active', '=', False)])
        variants.write({
            'active': True
        })
        return True
