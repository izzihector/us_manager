# -*- coding: utf-8 -*-
# MCS | Matrica Consulting Service Dev By Brata Bayu

from odoo import api, fields, models, _
from odoo.tools import pycompat
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError


class mcs_branch(models.Model):
    _name 			= 'mcs.branch'
    _description 	= 'Model Base Branch (Business Unit)'

    name 			= fields.Char('Name', required=True)
    address 		= fields.Text('Address', size=252)
    telephone_no 	= fields.Char("Telephone No")
    company_id 		=  fields.Many2one('res.company', 'Company', required=True)
    parent_id 		= fields.Many2one(comodel_name='mcs.branch', string="Parent", ondelete='cascade', required=False)



class mcs_res_users(models.Model):
    _inherit = 'res.users'
    
    branch_id = fields.Many2one('mcs.branch', 'Business Unit')
    branch_ids = fields.Many2many('mcs.branch', id1='user_id', id2='branch_id',string='Business Unit')

    def write(self, values):
        if 'branch_id' in values or 'branch_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
            self.has_group.clear_cache(self)
        user = super(mcs_res_users, self).write(values)
        return user