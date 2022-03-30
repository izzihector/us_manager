# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    balance_bank = fields.Float('Balance', compute='compute_balance_cash')

    def action_confirm(self):
        if self.payment_type == 'outbound':
            if self.balance_bank < self.amount:
                raise UserError(_('Balance in bank or cash not enough'))
        rec = super(AccountPayment, self).action_confirm()
        return rec

    @api.depends('journal_id')
    def compute_balance_cash(self):
        for r in self:
            r.balance_bank = 0
            if r.journal_id:
                for coa in r.journal_id.default_credit_account_id:
                    if coa:
                        cek = self.env['account.move.line'].search([('account_id', '=', coa.id)])
                        if cek:
                            data10 = sum([line.balance for line in cek])
                            r.balance_bank = data10