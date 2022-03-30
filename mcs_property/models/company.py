from odoo import models, fields, api


class Company(models.Model):
    _inherit = 'res.company'

    is_property = fields.Boolean(track_visibility=True)
    npwp = fields.Char(track_visibility=True)