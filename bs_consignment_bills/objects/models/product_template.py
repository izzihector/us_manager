# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    owner_id = fields.Many2one(comodel_name="res.partner", string="Owner")
    is_consignment = fields.Boolean(string="Is Consignment", compute='compute_is_consignment', store=True)

    @api.depends('owner_id')
    def compute_is_consignment(self):
        for product in self:
            product.is_consignment = True if product.owner_id else False
            if product.is_consignment:
                product.purchase_ok = False