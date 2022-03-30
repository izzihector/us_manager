from odoo import models, fields, api


class Location(models.Model):
    _name = 'mcs_property.location'

    name = fields.Char()