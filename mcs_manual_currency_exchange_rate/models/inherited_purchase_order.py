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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    apply_manual_currency_exchange = fields.Boolean(string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(string='Manual Currency Exchange Rate')
    active_manual_currency_rate = fields.Boolean('active Manual Currency', default=False)

    # Note: Add by TPW 2022-02-15 ----
    inverted_currency_exchange_rate = fields.Float(string='*Inverted Exchange Rate')

    # Note: Add by TPW 2022-02-15 ----
    @api.onchange('manual_currency_exchange_rate')
    def _onchange_manual_currency_exchange_rate(self):
        if self.manual_currency_exchange_rate:
            self.inverted_currency_exchange_rate = 1 / self.manual_currency_exchange_rate

    # Note: Add by TPW 2022-02-15 ----
    @api.onchange('inverted_currency_exchange_rate')
    def _onchange_inverted_currency_exchange_rate(self):
        if self.inverted_currency_exchange_rate:
            self.manual_currency_exchange_rate = 1 / self.inverted_currency_exchange_rate

    @api.onchange('company_id','currency_id')
    def onchange_currency_id(self):
        if self.company_id or self.currency_id:
            if self.company_id.currency_id != self.currency_id:
                self.active_manual_currency_rate = True
            else:
                self.active_manual_currency_rate = False
        else:
            self.active_manual_currency_rate = False

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            if self.product_id.seller_ids.filtered(lambda s: s.name.id == self.partner_id.id):
                self.price_unit = 0.0
            return
        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.company_id) if seller else 0.0
        if self.order_id.apply_manual_currency_exchange:
            self.price_unit = price_unit * self.order_id.manual_currency_exchange_rate
            return
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        self.price_unit = price_unit
