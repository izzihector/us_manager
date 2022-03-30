# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
import psycopg2
import pytz
from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
import odoo.addons.decimal_precision as dp


_logger = logging.getLogger(__name__)

class AccountInvoiceInherit(models.Model):
	_inherit = "account.move"

	pos_order_id = fields.Many2one('pos.order',string="POS order" ,readonly=True)
	order_discount = fields.Float("Discount",default=0.0 ,readonly=True)
	is_created_from_pos = fields.Boolean("Is Created From POS" ,readonly=True)
	discount_on = fields.Char('Discount On' ,readonly=True)

	@api.model
	def discount_line_move_line_get(self):
		res = []
		account_id = False
		value = 0.0
		if self.discount_on == 'order':
			if self.order_discount:
				if self.pos_order_id.config_id.acc_account_id:
					account_id = self.pos_order_id.config_id.acc_account_id.id
				value = self.order_discount
		res.append({
			'name': 'Order Discount',
			'price_unit': value,
			'quantity': 1,
			'price': -value,
			'account_id': account_id or False,
		})
		return res

	def action_move_create(self):
		""" Creates invoice related analytics and financial move lines """
		account_move = self.env['account.move']

		for inv in self:
			if not inv.journal_id.sequence_id:
				raise UserError(_('Please define sequence on the journal related to this invoice.'))
			if not inv.invoice_line_ids.filtered(lambda line: line.account_id):
				raise UserError(_('Please add at least one invoice line.'))
			if inv.move_id:
				continue


			if not inv.date_invoice:
				inv.write({'date_invoice': fields.Date.context_today(self)})
			if not inv.date_due:
				inv.write({'date_due': inv.date_invoice})
			company_currency = inv.company_id.currency_id

			# create move lines (one per invoice line + eventual taxes and analytic lines)
			iml = inv.invoice_line_move_line_get()
			iml += inv.tax_line_move_line_get()
			if inv.is_created_from_pos and inv.discount_on == 'order':
				iml += inv.discount_line_move_line_get()

			diff_currency = inv.currency_id != company_currency
			# create one move line for the total and possibly adjust the other lines amount
			total, total_currency, iml = inv.compute_invoice_totals(company_currency, iml)

			name = inv.name or ''
			if inv.payment_term_id:
				totlines = inv.payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
				res_amount_currency = total_currency
				for i, t in enumerate(totlines):
					if inv.currency_id != company_currency:
						amount_currency = company_currency._convert(t[1], inv.currency_id, inv.company_id, inv._get_currency_rate_date() or fields.Date.today())
					else:
						amount_currency = False

					# last line: add the diff
					res_amount_currency -= amount_currency or 0
					if i + 1 == len(totlines):
						amount_currency += res_amount_currency

					iml.append({
						'type': 'dest',
						'name': name,
						'price': t[1],
						'account_id': inv.account_id.id,
						'date_maturity': t[0],
						'amount_currency': diff_currency and amount_currency,
						'currency_id': diff_currency and inv.currency_id.id,
						'invoice_id': inv.id
					})
			else:
				iml.append({
					'type': 'dest',
					'name': name,
					'price': total,
					'account_id': inv.account_id.id,
					'date_maturity': inv.date_due,
					'amount_currency': diff_currency and total_currency,
					'currency_id': diff_currency and inv.currency_id.id,
					'invoice_id': inv.id
				})
			part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
			line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
			line = inv.group_lines(iml, line)

			line = inv.finalize_invoice_move_lines(line)

			date = inv.date or inv.date_invoice
			move_vals = {
				'ref': inv.reference,
				'line_ids': line,
				'journal_id': inv.journal_id.id,
				'date': date,
				'narration': inv.comment,
			}
			move = account_move.create(move_vals)
			# Pass invoice in method post: used if you want to get the same
			# account move reference when creating the same invoice after a cancelled one:
			move.post(invoice = inv)
			# make the invoice point to that move
			vals = {
				'move_id': move.id,
				'date': date,
				'move_name': move.name,
			}
			inv.write(vals)
		return True

		if self.company_id.anglo_saxon_accounting and self.type in ('out_invoice', 'out_refund'):
			for i_line in self.invoice_line_ids:
				res.extend(self._anglo_saxon_sale_move_lines(i_line))
				
		if self.env.user.company_id.anglo_saxon_accounting:
			if self.type in ['in_invoice', 'in_refund']:
				for i_line in self.invoice_line_ids:
					res.extend(self._anglo_saxon_purchase_move_lines(i_line, res))
		return res


	def get_taxes_values(self):
		tax_grouped = {}
		round_curr = self.currency_id.round
		for line in self.invoice_line_ids:
			price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			if line.orderline_discount_type  == "fixed":
				price_unit = line.price_unit  - line.discount 
			taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
			for tax in taxes:
				val = self._prepare_tax_line_vals(line, tax)
				key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

				if key not in tax_grouped:
					tax_grouped[key] = val
					tax_grouped[key]['base'] = round_curr(val['base'])
				else:
					tax_grouped[key]['amount'] += val['amount']
					tax_grouped[key]['base'] += round_curr(val['base'])
		return tax_grouped

	@api.depends(
		'line_ids.debit',
		'line_ids.credit',
		'line_ids.currency_id',
		'line_ids.amount_currency',
		'line_ids.amount_residual',
		'line_ids.amount_residual_currency',
		'line_ids.payment_id.state')
	def _compute_amount(self):
		invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]
		self.env['account.payment'].flush(['state'])
		if invoice_ids:
			self._cr.execute(
				'''
					SELECT move.id
					FROM account_move move
					JOIN account_move_line line ON line.move_id = move.id
					JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
					JOIN account_move_line rec_line ON
						(rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
						OR
						(rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
					JOIN account_payment payment ON payment.id = rec_line.payment_id
					JOIN account_journal journal ON journal.id = rec_line.journal_id
					WHERE payment.state IN ('posted', 'sent')
					AND journal.post_at = 'bank_rec'
					AND move.id IN %s
				''', [tuple(invoice_ids)]
			)
			in_payment_set = set(res[0] for res in self._cr.fetchall())
		else:
			in_payment_set = {}

		for move in self:
			total_untaxed = 0.0
			total_untaxed_currency = 0.0
			total_tax = 0.0
			total_tax_currency = 0.0
			total_residual = 0.0
			total_residual_currency = 0.0
			total = 0.0
			total_currency = 0.0
			currencies = set()

			for line in move.line_ids:
				if line.currency_id:
					currencies.add(line.currency_id)

				if move.is_invoice(include_receipts=True):
					# === Invoices ===

					if not line.exclude_from_invoice_tab:
						# Untaxed amount.
						total_untaxed += line.balance
						total_untaxed_currency += line.amount_currency
						total += line.balance
						total_currency += line.amount_currency
					elif line.tax_line_id:
						# Tax amount.
						total_tax += line.balance
						total_tax_currency += line.amount_currency
						total += line.balance
						total_currency += line.amount_currency
					elif line.account_id.user_type_id.type in ('receivable', 'payable'):
						# Residual amount.
						total_residual += line.amount_residual
						total_residual_currency += line.amount_residual_currency
				else:
					# === Miscellaneous journal entry ===
					if line.debit:
						total += line.balance
						total_currency += line.amount_currency

			if move.type == 'entry' or move.is_outbound():
				sign = 1
			else:
				sign = -1
			move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
			move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
			move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
			move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
			move.amount_untaxed_signed = -total_untaxed
			move.amount_tax_signed = -total_tax
			move.amount_total_signed = -total
			move.amount_residual_signed = total_residual

			currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
			is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual

			# Compute 'invoice_payment_state'.
			if move.state == 'posted' and is_paid:
				if move.id in in_payment_set:
					move.invoice_payment_state = 'in_payment'
				else:
					move.invoice_payment_state = 'paid'
			else:
				move.invoice_payment_state = 'not_paid'



class AccountInvoiceLineInherit(models.Model):
	_inherit = "account.move.line"

	pos_order_id = fields.Many2one('pos.order',string="POS order" ,readonly=True)
	orderline_discount_type = fields.Char('Discount Type' ,readonly=True)
	is_created_from_pos = fields.Boolean("Is Created From POS" ,readonly=True)

	@api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
		'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
		'invoice_id.date_invoice', 'invoice_id.date')
	def _compute_price(self):
		for i in self:
			currency = i.invoice_id and i.invoice_id.currency_id or None
			if i.orderline_discount_type  == "fixed":
				price = i.price_unit - i.discount
			else:
				price = i.price_unit * (1 - (i.discount or 0.0) / 100.0)
			taxes = False
			if i.invoice_line_tax_ids:
				taxes = i.invoice_line_tax_ids.compute_all(price, currency, i.quantity, product=i.product_id, partner=i.invoice_id.partner_id)
			i.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else i.quantity * price
			i.price_total = taxes['total_included'] if taxes else i.price_subtotal
			if i.invoice_id.currency_id and i.invoice_id.company_id and i.invoice_id.currency_id != i.invoice_id.company_id.currency_id:
				price_subtotal_signed = i.invoice_id.currency_id.with_context(date=i.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed, i.invoice_id.company_id.currency_id)
			sign = i.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
			i.price_subtotal_signed = price_subtotal_signed * sign
			
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:   