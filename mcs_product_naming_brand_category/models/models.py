# -*- coding: utf-8 -*-

from odoo import models, fields, api


class inheritProductBrand(models.Model):
    _inherit = 'product.brand'

    code = fields.Char("Brand Code", required=True)

    _sql_constraints = [
        ('email_code', 'UNIQUE(code)', 'code must be unique !')
    ]

class inheritProductBrand(models.Model):
    _inherit = 'product.template'

    is_autonaming = fields.Boolean("Auto Naming", default=True)

    @api.onchange('is_autonaming', 'brand_id', 'categ_id')
    def _onchange_autonaming(self):

        self.name = None

        if self.is_autonaming:
            brand = ''
            categ = ''

            if self.brand_id:
                brand = self.brand_id.code or ''

            if self.categ_id:
                categ = (self.categ_id.parent_id.name + ' ' if self.categ_id.parent_id else '') + self.categ_id.name

            self.name = brand.upper() + ' ' + categ.upper()

class inheritProductAttributeValue(models.Model):
    _inherit = 'product.attribute'

    show_in_desc = fields.Boolean("Show In Description")

class inheritProductAttribute(models.Model):
    _inherit = 'product.template.attribute.value'

    def _show_desc_variant_attributes(self):
        return self.filtered(lambda ptav: ptav.attribute_id.show_in_desc)

    def _get_combination_name(self):
        """Exclude values from single value lines or from no_variant attributes."""
        return ", ".join([ptav.name for ptav in self._without_no_variant_attributes()._filter_single_value_lines()._show_desc_variant_attributes()])

    def _get_combination_name_new(self):
        """Exclude values from single value lines or from no_variant attributes."""
        return ", ".join([ptav.name for ptav in self._show_desc_variant_attributes()])
