# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", related='location_ids.department_id')
