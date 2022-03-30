# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    consignment_sale_ids = fields.One2many(comodel_name="sale.order.line", inverse_name="consignment_invoice_id",
                                           string="Consignment Sales")
    consignment_pos_ids = fields.One2many(comodel_name="pos.order.line", inverse_name="consignment_invoice_id",
                                          string="Consignment POS Order")
