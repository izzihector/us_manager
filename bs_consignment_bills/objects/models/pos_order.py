# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    product_owner_id = fields.Many2one(comodel_name="res.partner", string="Product Owner", related='product_id.owner_id')
    consignment_invoice_id = fields.Many2one(comodel_name="account.move.line", string="Consignment Bills")
    consignment_invoice_state = fields.Selection(string="Consignment Bills Status", store=True,
                                                 related='consignment_invoice_id.parent_state')
