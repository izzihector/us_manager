# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=False, ondelete='restrict',
                                default=lambda self:self.env.user.department_id)
