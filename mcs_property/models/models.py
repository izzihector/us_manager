from odoo import models, fields, api


class Quotation(models.Model):
    _name = 'mcs_property.quotation'
    _description = 'mcs_property.quotation'

    name = fields.Char(track_visibility=True)

class Order(models.Model):
    _name = 'mcs_property.order'
    _description = 'mcs_property.order'

    name = fields.Char(track_visibility=True)

class ProductProperty(models.Model):
    _name = 'mcs_property.product_property'
    _description = 'mcs_property.product_property'

    name = fields.Char(track_visibility=True)

class BusinessTypes(models.Model):
    _name = 'mcs_property.business_types'
    _description = 'mcs_property.business_types'

    name = fields.Char(track_visibility=True)

class DocumentCategories(models.Model):
    _name = 'mcs_property.document_categories'
    _description = 'mcs_property.document_categories'

    name = fields.Char(track_visibility=True)

class ServiceUnit(models.Model):
    _name = 'mcs_property.service_unit'
    _description = 'mcs_property.service_unit'

    name = fields.Char(track_visibility=True)

class FormatNomor(models.Model):
    _name = 'mcs_property.format_nomor'
    _description = 'Format Nomor'

    name = fields.Selection([
        ('Penomoran Kontrak', 'Penomoran Kontrak'),
        ('Adendum Kontrak', 'Adendum Kontrak'),
    ], required=True)
    format_nomor = fields.Text(required=True)
