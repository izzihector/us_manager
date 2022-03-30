# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", related='location_id.department_id')
