# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, time, datetime

class ABSLInherit(models.Model):
	_inherit = 'account.bank.statement.line'

	is_cash_in_out_entry = fields.Boolean('Is Cash In Out Entry')

class POSConfigSummery(models.Model):
	_inherit = 'pos.config'
	
	is_cash_in_out = fields.Boolean('Do Cash In Out From POS')
	is_print_statement = fields.Boolean('Print Statement Receipt')

class pos_cash_in_out(models.Model):
	_name = 'pos.cash.in.out'
	_rec_name = 'user_id'

	user_id  = fields.Many2one('res.users','Responsible')
	session_id  = fields.Many2one('pos.session','Session')
	amount  =  fields.Float('Amount')
	create_date  =  fields.Datetime('Create Date', default = datetime.now(), )
	cash_type = fields.Selection([
		('credit', 'Credit'),
		('debit', 'Debit')
		], string='Type', default='credit')

	def get_statement_data(self,stmt_st_date, stmt_end_date,selected_cashier):
		cash_in_data = []
		cash_out_data = []
		credit_total = 0.0
		debit_total = 0.0
		final_data = []
		if selected_cashier == 'Select Cashier':
			statements = self.env['account.bank.statement.line'].search([
				('date', '>=', stmt_st_date ),
				('date', '<=', stmt_end_date),
				('is_cash_in_out_entry', '=', True),
				])
		else:
			statements = self.env['account.bank.statement.line'].search([
				('date', '>=', stmt_st_date ),
				('date', '<=', stmt_end_date),
				('is_cash_in_out_entry', '=', True),
				('statement_id.pos_session_id.user_id', '=', int(selected_cashier)),
				])
		for line in statements:
			data = {}
			if line.amount > 0 :
				credit_total += line.amount
				# data.update({'type': 'Cr', 'total': line.amount, 'date':line.date})
				data.update({'credit': line.amount, 'debit': '-', 'date':line.date})
				cash_in_data.append(data)
			else:
				debit_total += -(line.amount)
				data.update({'credit': '-', 'debit': -(line.amount), 'date':line.date})
				# data.update({'Credit': '-','Debit': 'Dr', 'total': -(line.amount), 'date':line.date})
				cash_out_data.append(data)
			final_data.append(data)

		return[cash_in_data,cash_out_data,final_data,credit_total,debit_total]

class PosBoxIn(models.TransientModel):
	_name = 'cash.box.in'

	def _calculate_values_for_statement_line(self, record):
		if not record.journal_id.company_id.transfer_account_id:
			raise UserError(_("You have to define an 'Internal Transfer Account' in your cash register's journal."))
		return {
			'date': record.date,
			'statement_id': record.id,
			'journal_id': record.journal_id.id,
			'amount': self.amount or 0.0,
			'is_cash_in_out_entry':True,
			'account_id': record.journal_id.company_id.transfer_account_id.id,
			'ref': '%s' % (self.ref or ''),
			'name': self.name,
		}

	def create_cash_in(self, cashier, reason, amount, session_id):

		cash_in_obj = self.env['pos.cash.in.out']
		
		user = self.env['res.users'].browse(cashier)
		vals = {
			'cash_type': 'credit',
			'user_id': cashier,
			'session_id' : session_id,
			'amount' : float(amount),
			'create_date': datetime.now().date(),
		}
		cash_create = cash_in_obj.sudo().create(vals)
		
		account_in_obj = self.env['account.bank.statement.line']
		stmt_id = self.env['pos.session'].browse(session_id).cash_register_id
		
		if not stmt_id:
			return False

		if stmt_id.difference < 0.0:
			account = stmt_id.journal_id.loss_account_id
			name = _('Loss')
		else:
			# statement.difference > 0.0
			account = stmt_id.journal_id.profit_account_id
			name = _('Profit')
			
		values = {
			'statement_id': stmt_id.id,
			'name': reason,
			'account_id': account.id,
			'ref' : stmt_id.name,
			'amount' : float(amount),
			'is_cash_in_out_entry':True,
			'date': datetime.now().date(),
		}
		account_create = account_in_obj.sudo().create(values)

		return True
		

class PosBoxOut(models.TransientModel):
	_inherit = 'cash.box.out'

	def _calculate_values_for_statement_line(self, record):
		if not record.journal_id.company_id.transfer_account_id:
			raise UserError(_("You have to define an 'Internal Transfer Account' in your cash register's journal."))
		amount = self.amount or 0.0
		return {
			'date': record.date,
			'statement_id': record.id,
			'journal_id': record.journal_id.id,
			'is_cash_in_out_entry':True,
			'amount': -amount if amount > 0.0 else amount,
			'account_id': record.journal_id.company_id.transfer_account_id.id,
			'name': self.name,
		}

	def create_cash_out(self, cashier, reason, amount, session_id):

		cash_out_obj = self.env['pos.cash.in.out']
		
		user = self.env['res.users'].browse(cashier)
		vals = {
			'cash_type': 'debit',
			'user_id': cashier,
			'session_id' : session_id,
			'amount' : float(amount),
			'create_date': datetime.now().date(),
		}
		cash_create = cash_out_obj.sudo().create(vals)

		account_in_obj = self.env['account.bank.statement.line']
		stmt_id = self.env['pos.session'].browse(session_id).cash_register_id
		
		if not stmt_id:
			return False
		if stmt_id.difference < 0.0:
			account = stmt_id.journal_id.loss_account_id
			name = _('Loss')
		else:
			# statement.difference > 0.0
			account = stmt_id.journal_id.profit_account_id
			name = _('Profit')

		values = {
			'statement_id': stmt_id.id,
			'name': reason,
			'ref' : stmt_id.name,
			'amount' : -float(amount),
			'account_id': account.id,
			'is_cash_in_out_entry':True,
			'date': datetime.now().date(),
		}
		account_create = account_in_obj.sudo().create(values)
		
		return True
				
			   
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
