# -*- coding: utf-8 -*-
# Copyright 2019 Bumiswa
from odoo import api, fields, models


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", ondelete='restrict')
