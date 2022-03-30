# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", related='journal_id.department_id', store=True)

    @api.onchange('branch_id')
    def onchange_branch_department(self):
        if self.branch_id:
            self.department_id = self.branch_id.department_id.id
