# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        if vals.get('department_id'):
            self.clear_caches()
        return res

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        if vals.get('department_id'):
            self.clear_caches()
        return res
