# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_consignment = fields.Boolean(string="Is Consignment?")
    consignment_date_start = fields.Datetime(string="Consignment Bills Date Start")
    consignment_date_end = fields.Datetime(string="Consignment Bills Date End")

    # def compute_consignment_date(self):
    #     for record in self:
    #         sale_lines = record.invoice_line_ids.mapped('consignment_sale_ids')
    #         pos_lines = record.invoice_line_ids.mapped('consignment_pos_ids')
    #         if sale_lines or pos_lines:
    #             dates = sale_lines.mapped('order_id').mapped('date_order')
    #             dates += pos_lines.mapped('order_id').mapped('date_order')
    #             record.consignment_date_start = min(dates)
    #             record.consignment_date_end = max(dates)
    #         else:
    #             record.consignment_date_start = False
    #             record.consignment_date_end = False
