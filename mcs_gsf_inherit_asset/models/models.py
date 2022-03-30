# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero
from datetime import date, datetime

class JournalEntry(models.Model):
    _inherit = 'account.move'

    asset_id2 = fields.Many2one('account.asset.asset', string='Asset')

class Asset(models.Model):
    _inherit = 'account.asset.asset'


    request_sell = fields.Boolean('Request to Sell', default=False)
    manager_approve = fields.Boolean('Manager Approved', default=False)
    degresiv_faktor = fields.Integer('Degressive Factor %')

    @api.onchange('degresiv_faktor')
    def onchange_degresiv(self):
        for r in self:
            if r.degresiv_faktor:
                r.method_progress_factor = round((1-(((100/100)-(r.degresiv_faktor/100))**(1/12))),3)

    def ask_to_sell(self):
        for r in self:
            r.write({
                'request_sell': True,
            })
            manager = self.env['hr.department'].search([('name','=','Divisi Akuntansi Keuangan')], limit=1)
            managers = self.env['res.users'].search([('name','=',manager.manager_id.name)], limit=1)
            model = self.env['ir.model'].search([('model','=','account.asset.asset')], limit=1)
            mixin_obj = self.env['mail.activity']
            counterpart_aml_residual_dict = {
                'res_model_id': model.id,
                'res_id': r.id,
                'res_name': r.name,
                'activity_type_id': 4,
                'summary': 'Approve sell asset',
                'note': 'Please Approve This Request to sell asset',
                'date_deadline': datetime.now(),
                'user_id': managers.id,
            }
            mixin_obj.create(counterpart_aml_residual_dict)

    def approve_manager(self):
        for r in self:
            r.write({
                'manager_approve': True,
            })

    def cancel_request_sell(self):
        for r in self:
            r.write({
                'request_sell': False,
                'manager_approve': False,
            })


    def action_set_to_close(self):
        """ Returns an action opening the asset pause wizard."""
        self.ensure_one()
        new_wizard = self.env['account.asset.asset.sell'].create({
            'asset_id': self.id,
        })
        return {
            'name': _('Sell Asset'),
            'view_mode': 'form',
            'res_model': 'account.asset.asset.sell',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
        }

    # def sell_set_to_close(self):
    #     move_ids = self._get_disposal_moves()
    #     if move_ids:
    #         return self._return_disposal_view(move_ids)
    #     # Fallback, as if we just clicked on the smartbutton
    #     return self.open_entries()


    def open_entries(self):
        move_ids = []
        for asset in self:
            for depreciation_line in asset.depreciation_line_ids:
                if depreciation_line.move_id:
                    move_ids.append(depreciation_line.move_id.id)
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids)],
        }

class AssetSell(models.TransientModel):
    _name = 'account.asset.asset.sell'
    _description = 'Sell Asset'

    asset_id = fields.Many2one('account.asset.asset', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    invoice_id = fields.Many2one('account.move', string="Customer Invoice", help="The disposal invoice is needed in order to generate the closing journal entry.", domain="[('type', '=', 'out_invoice'), ('state', '=', 'posted')]")
    invoice_line_id = fields.Many2one('account.move.line', help="There are multiple lines that could be the related to this asset", domain="[('move_id', '=', invoice_id), ('exclude_from_invoice_tab', '=', False)]")
    select_invoice_line_id = fields.Boolean(compute="_compute_select_invoice_line_id")

    action = fields.Selection([('sell', 'Sell'), ('dispose', 'Dispose')], required=True, default='sell')
    gain_account_id = fields.Many2one('account.account',
                                      domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
                                      related='company_id.gain_account_id',
                                      help="Account used to write the journal item in case of gain", readonly=False)
    loss_account_id = fields.Many2one('account.account',
                                      domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
                                      related='company_id.loss_account_id',
                                      help="Account used to write the journal item in case of loss", readonly=False)

    gain_or_loss = fields.Selection([('gain', 'Gain'), ('loss', 'Loss'), ('no', 'No')], compute='_compute_gain_or_loss',
                                    help="Technical field to know is there was a gain or a loss in the selling of the asset")

    @api.depends('invoice_id', 'action')
    def _compute_select_invoice_line_id(self):
        for record in self:
            record.select_invoice_line_id = record.action == 'sell' and len(record.invoice_id.invoice_line_ids) > 1

    @api.onchange('action')
    def _onchange_action(self):
        if self.action == 'sell' and self.asset_id.children_ids.filtered(
                lambda a: a.state in ('draft', 'open') or a.value_residual > 0):
            raise UserError(
                _("You cannot automate the journal entry for an asset that has a running gross increase. Please use 'Dispose' on the increase(s)."))

    @api.depends('asset_id', 'invoice_id', 'invoice_line_id')
    def _compute_gain_or_loss(self):
        for record in self:
            line = record.invoice_line_id or len(
                record.invoice_id.invoice_line_ids) == 1 and record.invoice_id.invoice_line_ids or self.env[
                       'account.move.line']
            if record.asset_id.value_residual < abs(line.balance):
                record.gain_or_loss = 'gain'
            elif record.asset_id.value_residual > abs(line.balance):
                record.gain_or_loss = 'loss'
            else:
                record.gain_or_loss = 'no'

    def do_action(self):
        self.ensure_one()
        for r in self:
            if r.action == 'sell':
                mixin_obj = self.env['account.move']
                name = r.asset_id.name + ": Sell"
                moves = {
                    'date': datetime.now(),
                    'ref': name,
                    'type': 'entry',
                    'journal_id': r.asset_id.category_id.journal_id.id,
                    'asset_id2': r.asset_id.id,
                }
                move = mixin_obj.create(moves)
                credit_1 = """
                                    INSERT INTO account_move_line (
                                        move_id,date,ref,journal_id,company_id,account_id,name,quantity,debit,credit,
                                        balance
                                    )
                                    VALUES (
                                        %s,'%s','%s',%s,%s,%s,'%s','%s','%s','%s',
                                        '%s'
                                    )
                                """ % (
                    move.id, datetime.now(), name, r.asset_id.category_id.journal_id.id, r.asset_id.company_id.id,
                    r.asset_id.category_id.account_asset_id.id, r.asset_id.name, 1, 0, r.asset_id.value,
                    r.asset_id.value * -1,
                )
                self._cr.execute(credit_1)
                selisih = r.asset_id.value - r.asset_id.value_residual
                debit_1 = """
                                    INSERT INTO account_move_line (
                                        move_id,date,ref,journal_id,company_id,account_id,name,quantity,debit,credit,
                                        balance
                                    )
                                    VALUES (
                                        %s,'%s','%s',%s,%s,%s,'%s','%s','%s','%s',
                                        '%s'
                                    )
                                """ % (
                    move.id, datetime.now(), name, r.asset_id.category_id.journal_id.id, r.asset_id.company_id.id,
                    r.asset_id.category_id.account_depreciation_expense_id.id, r.asset_id.name, 1, selisih, 0,
                    selisih,
                )
                self._cr.execute(debit_1)
                debit_2 = """
                                    INSERT INTO account_move_line (
                                        move_id,date,ref,journal_id,company_id,account_id,name,quantity,debit,credit,
                                        balance
                                    )
                                    VALUES (
                                        %s,'%s','%s',%s,%s,%s,'%s','%s','%s','%s',
                                        '%s'
                                    )
                                """ % (
                    move.id, datetime.now(), name, r.asset_id.category_id.journal_id.id, r.asset_id.company_id.id,
                    r.asset_id.category_id.account_asset_id.id, r.asset_id.name, 1, r.invoice_id.amount_untaxed, 0,
                    r.invoice_id.amount_untaxed,
                )
                self._cr.execute(debit_2)
                selisih2 = r.asset_id.value - selisih - r.invoice_id.amount_untaxed
                credit_2 = """
                                    INSERT INTO account_move_line (
                                        move_id,date,ref,journal_id,company_id,account_id,name,quantity,debit,credit,
                                        balance
                                    )
                                    VALUES (
                                        %s,'%s','%s',%s,%s,%s,'%s','%s','%s','%s',
                                        '%s'
                                    )
                                """ % (
                    move.id, datetime.now(), name, r.asset_id.category_id.journal_id.id, r.asset_id.company_id.id,
                    r.gain_account_id.id, r.asset_id.name, 1, 0, selisih2 * -1,
                    selisih2,
                )
                self._cr.execute(credit_2)
                managers = self.env['account.asset.depreciation.line'].search([('asset_id','=',r.asset_id.id),
                                                                               ('move_check','=', False)])
                if managers:
                    managers.unlink()
                ten = self.env['account.asset.depreciation.line'].search([('asset_id','=',r.asset_id.id),
                                                                               ('move_check','=', True)])
                line = self.env['account.asset.depreciation.line']
                lines = {
                    'name': 'End',
                    'sequence': 1,
                    'asset_id': r.asset_id.id,
                    'amount': r.asset_id.value_residual,
                    'remaining_value': 0,
                    'depreciated_value': r.asset_id.value,
                    'depreciation_date': datetime.now(),
                    'move_id': move.id,
                    'move_check': True,
                    'move_posted_check': True,

                }
                line.create(lines)
                r.asset_id.state = 'close'
                return self.asset_id.open_entries()
            else:
                mixin_obj = self.env['account.move']
                name = r.asset_id.name + ": Dispose"
                moves = {
                    'date': datetime.now(),
                    'ref': name,
                    'type': 'entry',
                    'journal_id': r.asset_id.category_id.journal_id.id,
                    'asset_id2': r.asset_id.id,
                }
                move = mixin_obj.create(moves)
                credit_1 = """
                                    INSERT INTO account_move_line (
                                        move_id,date,ref,journal_id,company_id,account_id,name,quantity,debit,credit,
                                        balance
                                    )
                                    VALUES (
                                        %s,'%s','%s',%s,%s,%s,'%s','%s','%s','%s',
                                        '%s'
                                    )
                                """ % (
                    move.id, datetime.now(), name, r.asset_id.category_id.journal_id.id, r.asset_id.company_id.id,
                    r.asset_id.category_id.account_asset_id.id, r.asset_id.name, 1, 0, r.asset_id.value,
                    r.asset_id.value * -1,
                )
                self._cr.execute(credit_1)
                selisih = r.asset_id.value - r.asset_id.value_residual
                debit_1 = """
                                    INSERT INTO account_move_line (
                                        move_id,date,ref,journal_id,company_id,account_id,name,quantity,debit,credit,
                                        balance
                                    )
                                    VALUES (
                                        %s,'%s','%s',%s,%s,%s,'%s','%s','%s','%s',
                                        '%s'
                                    )
                                """ % (
                    move.id, datetime.now(), name, r.asset_id.category_id.journal_id.id, r.asset_id.company_id.id,
                    r.asset_id.category_id.account_depreciation_expense_id.id, r.asset_id.name, 1, selisih, 0,
                    selisih,
                )
                self._cr.execute(debit_1)
                selisih3 = r.asset_id.value - selisih
                debit_2 = """
                                    INSERT INTO account_move_line (
                                        move_id,date,ref,journal_id,company_id,account_id,name,quantity,debit,credit,
                                        balance
                                    )
                                    VALUES (
                                        %s,'%s','%s',%s,%s,%s,'%s','%s','%s','%s',
                                        '%s'
                                    )
                                """ % (
                    move.id, datetime.now(), name, r.asset_id.category_id.journal_id.id, r.asset_id.company_id.id,
                    r.loss_account_id.id, r.asset_id.name, 1, selisih3, 0,
                    selisih3,
                )
                self._cr.execute(debit_2)
                managers = self.env['account.asset.depreciation.line'].search([('asset_id','=',r.asset_id.id),
                                                                               ('move_check','=', False)])
                if managers:
                    managers.unlink()
                ten = self.env['account.asset.depreciation.line'].search([('asset_id','=',r.asset_id.id),
                                                                               ('move_check','=', True)])
                line = self.env['account.asset.depreciation.line']
                lines = {
                    'name': 'End',
                    'sequence': 1,
                    'asset_id': r.asset_id.id,
                    'amount': r.asset_id.value_residual,
                    'remaining_value': 0,
                    'depreciated_value': r.asset_id.value,
                    'depreciation_date': datetime.now(),
                    'move_id': move.id,
                    'move_check': True,
                    'move_posted_check': True,

                }
                line.create(lines)
                r.asset_id.state = 'close'
                return self.asset_id.open_entries()


