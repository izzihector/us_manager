# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    sub_categ_4 = fields.Char('Import Code')
    ref_code = fields.Char('Code Reference')
    margin = fields.Float('% Margin')
