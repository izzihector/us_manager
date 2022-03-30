# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", related='order_id.department_id')
