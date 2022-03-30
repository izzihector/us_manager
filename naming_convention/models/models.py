# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


# Inventory
class NamingConventionCommodity(models.Model):
    _name = 'naming_convention.commodity'
    _description = 'Naming Convention Commodity'
    _rec_name = 'commodity'

    commodity = fields.Char('Commodity', required=1)
    description = fields.Char('Description')
    attribute_line_ids = fields.One2many(comodel_name='naming_convention.commodity.attribute', inverse_name='attribute_id', string='Attributes', copy=True)
    packaging_line_ids = fields.One2many(comodel_name='naming_convention.commodity.packaging', inverse_name='packaging_id', string='Model', copy=True)
    brand_line_ids = fields.One2many(comodel_name='naming_convention.commodity.brand', inverse_name='brand_id', string='Brand', copy=True)

class NamingConventionCommodityAttribute(models.Model):
    _name = 'naming_convention.commodity.attribute'
    _description = 'Naming Convention Type'
    _rec_name = 'commodity'

    commodity = fields.Char('Commodity', required=1)
    description = fields.Char('Description')
    attribute_id = fields.Many2one(comodel_name='naming_convention.commodity', string='Attribute/Type', index=True)

class NamingConventionCommodityPackaging(models.Model):
    _name = 'naming_convention.commodity.packaging'
    _description = 'Naming Convention Model'
    _rec_name = 'commodity'

    commodity = fields.Char('Commodity', required=1)
    description = fields.Char('Description')
    packaging_id = fields.Many2one(comodel_name='naming_convention.commodity', string='Model', index=True)

class NamingConventionCommodityBrand(models.Model):
    _name = 'naming_convention.commodity.brand'
    _description = 'Naming Convention Brand'
    _rec_name = 'commodity'

    commodity = fields.Char('Commodity', required=1)
    description = fields.Char('Description')
    brand_id = fields.Many2one(comodel_name='naming_convention.commodity', string='Brand', index=True)

class NamingConventionCommodityOrigin(models.Model):
    _name = 'naming_convention.commodity.origin'
    _description = 'Naming Convention Motif'
    _rec_name = 'commodity'

    commodity = fields.Char('Commodity', required=1)
    description = fields.Char('Description')

class NamingConventionCommodityPekerjaan(models.Model):
    _name = 'naming_convention.commodity.pekerjaan'
    _rec_name = 'commodity'

    commodity = fields.Char('Size', required=1)
    description = fields.Char('Description')
    sequence = fields.Char('Sequence')

class NamingConventionCommoditySubKatBarang(models.Model):
    _name = 'naming_convention.commodity.sub.kat.barang'
    _rec_name = 'commodity'

    commodity = fields.Char('Warna', required=1)
    description = fields.Char('Description')
    sequence = fields.Char('Sequence')
    pekerjaan_id = fields.Many2one('naming_convention.commodity.pekerjaan', string='Size')

class NamingConventionCommodityTema(models.Model):
    _name = 'naming_convention.commodity.tema'
    _rec_name = 'commodity'

    commodity = fields.Char('Tema', required=1)
    description = fields.Char('Description')
    sequence = fields.Char('Sequence')

class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    name = fields.Char('Name', index=True, required=False, translate=True, null=False)
    commodity_id = fields.Many2one(comodel_name='naming_convention.commodity', string='Commodity', index=True)
    attribute_id = fields.Many2one(comodel_name='naming_convention.commodity.attribute', string='Commodity Type', index=True)
    packaging_id = fields.Many2one(comodel_name='naming_convention.commodity.packaging', string='Commodity Model', index=True)
    brand_id = fields.Many2one(comodel_name='naming_convention.commodity.brand', string='Commodity Brand', index=True)
    origin_id = fields.Many2one(comodel_name='naming_convention.commodity.origin', string='Commodity Motif', index=True)
    pekerjaan_id = fields.Many2one('naming_convention.commodity.pekerjaan', string='Size', index=True)
    sub_barang_id = fields.Many2one('naming_convention.commodity.sub.kat.barang', string='Warna', index=True)
    tema_id = fields.Many2one('naming_convention.commodity.tema', string='Tema', index=True)
    owner_id = fields.Many2one('res.partner', string='Owner')
    sub_categ_2 = fields.Char('Sub Category 2')
    sub_categ_3 = fields.Char('Sub Category 3')
    sub_categ_4 = fields.Char('Sub Category 4')
    margin = fields.Float('% Margin')

    # @api.multi
    def button_set_name(self):
        if self.commodity_id:
            name_commodity = self.commodity_id.commodity + " "
        else:
            name_commodity = ""
        if self.origin_id:
            name_origin = self.origin_id.commodity + " "
        else:
            name_origin = ""
        if self.attribute_id:
            name_attribute = self.attribute_id.commodity + " "
        else:
            name_attribute = ""
        if self.brand_id:
            name_brand = self.brand_id.commodity + " "
        else:
            name_brand = ""
        if self.sub_barang_id:
            name_sub_barang = self.sub_barang_id.commodity
        else:
            name_sub_barang = ""
        if self.packaging_id:
            name_packaging = self.packaging_id.commodity
        else:
            name_packaging = ""
        if self.pekerjaan_id:
            name_pekerjaan = self.pekerjaan_id.commodity
        else:
            name_pekerjaan = ""

        self.name = name_commodity + name_brand + name_attribute + name_packaging + name_origin + name_pekerjaan + name_sub_barang

    #@api.onchange('commodity_id')
    #def onchange_commodity_id(self):
    #    if not self.commodity_id:
    #        self.attribute_id = None
    #        self.brand_id = None
    #        self.packaging_id = None
    #        return {}
    #    else:
    #        self.attribute_id = None
    #        self.brand_id = None
    #        self.packaging_id = None
    #        return {'domain': {'attribute_id': [('attribute_id', '=', self.commodity_id.id)],
    #                           'brand_id': [('brand_id', '=', self.commodity_id.id)],
    #                           'packaging_id': [('packaging_id', '=', self.commodity_id.id)],}}

class InheritSaleReport(models.Model):
    _inherit = 'sale.report'

    commodity_id = fields.Many2one(comodel_name='naming_convention.commodity', string='Naming Commodity', readonly=True)
    attribute_id = fields.Many2one(comodel_name='naming_convention.commodity.attribute', string='Naming Commodity Attribute', readonly=True)
    packaging_id = fields.Many2one(comodel_name='naming_convention.commodity.packaging', string='Naming Commodity Model', readonly=True)
    brand_id = fields.Many2one(comodel_name='naming_convention.commodity.brand', string='Naming Commodity Brand', readonly=True)
    origin_id = fields.Many2one(comodel_name='naming_convention.commodity.origin', string='Naming Commodity Motif', readonly=True)

    def _select(self):
        select_str = super(InheritSaleReport, self)._select()
        select_str += """
            ,t.commodity_id
            ,t.attribute_id
            ,t.packaging_id
            ,t.brand_id
            ,t.origin_id
            """
        return select_str

    def _group_by(self):
        group_by_str = super(InheritSaleReport, self)._group_by()
        group_by_str += """
            ,t.commodity_id
            ,t.attribute_id
            ,t.packaging_id
            ,t.brand_id
            ,t.origin_id
        """
        return group_by_str