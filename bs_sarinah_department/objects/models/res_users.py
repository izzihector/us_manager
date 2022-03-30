# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_department_ids = fields.Many2many(comodel_name="hr.department", string="Allowed Department(s)",
                                              compute='compute_all_department', store=True)

    @api.depends('employee_id.department_id', 'employee_ids.department_id')
    def compute_all_department(self):
        for user in self:
            user.allowed_department_ids = self.env['hr.department'].search([('id', 'child_of', user.department_id.id)])
