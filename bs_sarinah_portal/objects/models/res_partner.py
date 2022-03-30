# -*- coding: utf-8 -*-
# Copyright 2020 Linksoft Mitra Informatika
from odoo import api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    portal_product_categ_id = fields.Many2one(comodel_name="product.category", string="Portal Product Category",
                                              required=False)
    consignment_margin = fields.Float(string="Default Consignment Margin (%)",  required=False)
    is_price_include_consignment_margin = fields.Boolean(string="Vendor Price as Sale Price", default=True, )
    brand_ids = fields.Many2many(comodel_name='product.brand', string='Vendor Brands')
    
    # Copied from portal/wizard/portal_wizard.py with several modification.
    def action_send_portal_email(self):
        wizard_id = self.env['portal.wizard'].create({})
        for line in wizard_id.user_ids:
            if len(line.partner_id.user_ids) == 1:
                line.user_id = line.partner_id.user_ids.id
            else:
                raise UserError('Cannot decide which user should be used for %s' % line.partner_id.display_name)
        wizard_id.user_ids._send_email()
