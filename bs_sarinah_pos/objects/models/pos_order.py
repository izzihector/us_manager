# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch", related='config_id.branch_id', store=True,
                                ondelete='restrict')
    config_id = fields.Many2one(store=True)
    payment_type = fields.Selection(string='Payment Type', store=True, selection=[
        ('cash', 'Cash'), ('bank', 'Bank'), ('cash_and_bank', 'Cash and Bank')],
        compute='_compute_payment_type')

    @api.depends('payment_ids', 'payment_ids.payment_method_id', 'payment_ids.payment_method_id.is_cash_count')
    def _compute_payment_type(self):
        for record in self:
            is_cash_payments = (record.payment_ids
                    .mapped('payment_method_id')
                    .mapped('is_cash_count'))
            if all(is_cash_payments):
                record.payment_type = 'cash'
            elif not any(is_cash_payments):
                record.payment_type = 'bank'
            elif len(is_cash_payments):
                record.payment_type = 'cash_and_bank'
            else:
                record.payment_type = False

