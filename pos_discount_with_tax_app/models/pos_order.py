	# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

class PosOrderLineInherit(models.Model):
	_inherit = 'pos.order.line'

	orderline_discount_type = fields.Char('Discount Type')
	is_line_discount = fields.Boolean("IS Line Discount")

	@api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
	def _compute_amount_line_all(self):
		for line in self:
			fpos = line.order_id.fiscal_position_id
			tax_ids_after_fiscal_position = fpos.map_tax(line.tax_ids, line.product_id, line.order_id.partner_id) if fpos else line.tax_ids
			if line.orderline_discount_type == "fixed":
				price = line.price_unit - line.discount
			else:
				price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id, partner=line.order_id.partner_id)
			line.update({
			'price_subtotal_incl': taxes['total_included'],
			'price_subtotal': taxes['total_excluded'],
			})


class PosOrderInherit(models.Model):
	_inherit = 'pos.order'

	order_discount =  fields.Float(string='Order Discount', default = 0.0, readonly=True)
	order_discount_type = fields.Char('Order Discount Type')
	discount_on = fields.Char('Discount On')

	@api.model
	def _amount_line_tax(self, line, fiscal_position_id):
		taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.order_id.company_id.id)
		if fiscal_position_id:
			taxes = fiscal_position_id.map_tax(taxes, line.product_id, line.order_id.partner_id)
		for order in self:
			if line.orderline_discount_type == 'percentage':
				price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			else:
				price = line.price_unit - line.discount

		taxes = taxes.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)['taxes']
		return sum(tax.get('amount', 0.0) for tax in taxes)

	@api.model
	def _order_fields(self, ui_order):
		res = super(PosOrderInherit, self)._order_fields(ui_order)
		if 'discount_on' in ui_order :
			res['discount_on'] =  ui_order['discount_on']
		if 'discount_order' in ui_order :
			res['order_discount'] =  ui_order['discount_order']
		if 'order_discount_type' in ui_order :
			res['order_discount_type'] =  ui_order['order_discount_type']
		return res

	def _prepare_invoice(self):
		res = super(PosOrderInherit, self)._prepare_invoice()
		res.update({
				'pos_order_id' : self.id,
				'order_discount': self.order_discount,
				'is_created_from_pos' : True,
				'discount_on' : self.discount_on,
			}) 
		return res

	def _action_create_invoice_line(self, line=False, invoice_id=False):
		res = super(PosOrderInherit, self)._action_create_invoice_line(line,invoice_id)
		res.update({
				'pos_order_id' : self.id,
				'orderline_discount_type' : line.orderline_discount_type ,
				'is_created_from_pos' : True,
			}) 
		return res


class PosSession(models.Model):
	_inherit = 'pos.session'

	def _prepare_balancing_line_vals(self, imbalance_amount, move):
		config_id = self.config_id
		account = self._get_balancing_account()
		if config_id.allow_order_disc:
			account = config_id.acc_account_id
		partial_vals = {
			'name': _('Difference at closing PoS session'),
			'account_id': account.id,
			'move_id': move.id,
			'partner_id': False,
		}
		# `imbalance_amount` is already in terms of company currency so it is the amount_converted
		# param when calling `_credit_amounts`. amount param will be the converted value of
		# `imbalance_amount` from company currency to the session currency.
		imbalance_amount_session = 0
		if (not self.is_in_company_currency):
			imbalance_amount_session = self.company_id.currency_id._convert(imbalance_amount, self.currency_id, self.company_id, fields.Date.context_today(self))
		return self._credit_amounts(partial_vals, imbalance_amount_session, imbalance_amount)

