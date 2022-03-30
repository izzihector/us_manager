# -*- coding: utf-8 -*-
# Copyright 2019 Bumiswa
from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", ondelete='restrict')
    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch", ondelete='restrict')

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        self.department_id = self.branch_id.department_id.id
