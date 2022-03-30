# -*- coding: utf-8 -*-
# Copyright 2021 Linksoft Mitra Informatika

from odoo import api, fields, models


class UoMCategory(models.Model):
    _inherit = 'uom.category'
    
    is_available_on_portal = fields.Boolean(string="Show in Vendor Portal", default=True, )
