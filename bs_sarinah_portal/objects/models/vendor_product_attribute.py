# -*- coding: utf-8 -*-
# Copyright 2021 Linksoft Mitra Informatika

from odoo import api, fields, models


class VendorProductAttributeLine(models.Model):
    _name = 'vendor.product.attr.line'
    _description = 'Vendor Product Attribute Line'
    _parent_name = 'vendor_product_id'

    vendor_product_id = fields.Many2one(comodel_name="vendor.product", string="Vendor Product ", required=True,  )
    attribute_id = fields.Many2one(comodel_name="product.attribute", string="Attribute ", required=True,  )
    value_ids = fields.Many2many(comodel_name="product.attribute.value", string="Values ", required=True, domain="[('attribute_id', '=', attribute_id)]"  )

    def add_value_from_portal(self, value_id):
        if value_id not in self.value_ids.ids:
            self.value_ids = [(4, value_id, 0)]
            self.vendor_product_id.update_product_variant()
            return True
        return False

    def update_value_from_portal(self, value_ids):
        self.value_ids = [(6, 0, value_ids)]
        self.vendor_product_id.update_product_variant()

    def remove_value_from_portal(self, value_id):
        if value_id in self.attribute_id.value_ids.ids and value_id in self.value_ids.ids:
            self.value_ids = [(3, value_id, 0)]
            self.vendor_product_id.update_product_variant()
            return True
        return False

class VendorProductAttribute(models.Model):
    _name = 'vendor.product.attr'
    _description = 'Vendor Product Attribute'

    name = fields.Char(string="Name ", required=True,  )
    value_ids = fields.One2many(comodel_name="vendor.product.attr.value", inverse_name="attribute_id", string="Values ", required=False,  )
    

class VendorProductAttributeValue(models.Model):
    _name = 'vendor.product.attr.value'
    _description = 'Vendor Product Attribute Value'
    _parent_name = 'attribute_id'

    attribute_id = fields.Many2one(comodel_name="vendor.product.attr", string="Attribute ", required=True,  )
    name = fields.Char(string="Name ", required=True,  )

