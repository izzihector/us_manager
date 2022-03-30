from odoo import models, fields, api

class Customers(models.Model):
    _inherit = 'res.partner'

    is_property = fields.Boolean(track_visibility=True)
    
    document_properties = fields.One2many(comodel_name='mcs_property.document_properties', string="Document Properties", inverse_name='res_partner_id')
    npwp = fields.Char(track_visibility=True)
    business_type_id = fields.Many2one(comodel_name='mcs_property.business_types', track_visibility=True)
    contracts = fields.One2many(comodel_name='mcs_property.contract', string="Contracts", inverse_name='partner_id')