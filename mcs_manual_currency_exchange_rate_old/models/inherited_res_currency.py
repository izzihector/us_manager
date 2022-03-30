# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import models, fields, api

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    inverted_rate = fields.Float(string='*Inverted Rate', readonly=True)

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        if self._context.get('active_manutal_currency'):
            res = self._context.get('manual_rate')
        else:
            res = currency_rates.get(to_currency.id) / currency_rates.get(from_currency.id)
        return res


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    inverted_rate = fields.Float(string='*Inverted Rate')

    # Note: Add by TPW 2022-02-15 ----
    @api.onchange('rate')
    def _onchange_rate(self):
        if self.rate:
            self.inverted_rate = 1 / self.rate

    # Note: Add by TPW 2022-02-15 ----
    @api.onchange('inverted_rate')
    def _onchange_inverted_rate(self):
        if self.inverted_rate:
            self.rate = 1 / self.inverted_rate

