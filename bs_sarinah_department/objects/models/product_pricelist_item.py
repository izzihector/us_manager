# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch", related='pricelist_id.branch_id')
    department_id = fields.Many2one(comodel_name="hr.department", string="Department", related='pricelist_id.department_id')
