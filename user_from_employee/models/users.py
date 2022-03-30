# -*- coding: utf-8 -*-

from odoo import fields, models

class ResUser(models.Model):
    _inherit = "res.users"

    employee_id = fields.Many2one('hr.employee', string='Related employee')
    is_employee = fields.Boolean(string='Is an employee', default=False)
