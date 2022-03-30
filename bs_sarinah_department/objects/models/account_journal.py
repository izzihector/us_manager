# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department")
