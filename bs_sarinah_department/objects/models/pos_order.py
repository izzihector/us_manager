# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", related='config_id.department_id', store=True,
                                    ondelete='restrict')
