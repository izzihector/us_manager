# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class ResBranch(models.Model):
    _inherit = 'res.branch'

    default_pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="Default Pricelist")
