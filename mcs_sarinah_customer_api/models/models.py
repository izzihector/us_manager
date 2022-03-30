# -*- coding: utf-8 -*-

from odoo import models, fields, api


class inheritResPartner(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean(string='Is Customer?', index=True)
    date_of_birth = fields.Date(string='Date of Birth')
