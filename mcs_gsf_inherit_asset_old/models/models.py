# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero
from datetime import date, datetime

class Asset(models.Model):
    _inherit = 'account.asset.asset'


    request_sell = fields.Boolean('Request to Sell', default=False)
    manager_approve = fields.Boolean('Manager Approved', default=False)


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
        new_wizard = self.env['account.asset.sell'].create({
            'asset_id': self.id,
        })
        return {
            'name': _('Sell Asset'),
            'view_mode': 'form',
            'res_model': 'account.asset.sell',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
        }