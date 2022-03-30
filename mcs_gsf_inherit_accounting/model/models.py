# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class COA(models.Model):
    _inherit = 'account.account'

    active = fields.Boolean('Active', default=True)