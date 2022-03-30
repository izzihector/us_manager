# -*- coding: utf-8 -*-
# Copyright 2021 Linksoft Mitra Informatika

from odoo import api, fields, models, tools


class VendorProductVariant(models.Model):
    _name = 'vendor.product.variant'
    _description = 'Vendor Product Variant'
    _inherits = {'vendor.product': 'vendor_product_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vendor_product_id = fields.Many2one('vendor.product', 'Vendor Product', auto_join=True, index=True,
                                        ondelete="cascade", required=True)
    attribute_value_ids = fields.Many2many(comodel_name="product.attribute.value", string="Attribute Values ",
                                           required=True)
    variant_price_ids = fields.Many2many(comodel_name='product.supplierinfo', string='Variant Prices',
                                         compute="_compute_price_ids")
    active = fields.Boolean(string="Is Active ", default=True)
    product_id = fields.Many2one('product.product', 'Product Variant')
    product_code = fields.Char(string="Vendor product code")

    def name_get(self):
        result = []
        for product in self:
            name = u"[{}] {} - {}".format(
                product.product_code and product.product_code or '',
                product.product_name and product.product_name or '',
                product.partner_id and product.partner_id.name or '',
            )
            if product.attribute_value_ids:
                name += ' (' + ', '.join(product.attribute_value_ids.mapped('name')) + ')'
            result.append((product.id, name))
        return result

    @api.depends('price_ids.vendor_product_variant_id')
    def _compute_price_ids(self):
        for record in self:
            vendor_price_ids = record.price_ids.filtered(lambda price_id: price_id.vendor_product_variant_id == record)
            record.variant_price_ids = [(6, 0, vendor_price_ids.ids)]

    def unlink_or_archive(self):
        try:
            with self.env.cr.savepoint(), tools.mute_logger('odoo.sql_db'):
                self.unlink()
        except Exception:
            # We catch all kind of exceptions to be sure that the operation
            # doesn't fail.
            if len(self) > 1:
                self[:len(self) // 2].unlink_or_archive()
                self[len(self) // 2:].unlink_or_archive()
            else:
                if self.active:
                    # Note: this can still fail if something is preventing
                    # from archiving.
                    # This is the case from existing stock reordering rules.
                    self.write({'active': False})

    @api.model
    def create(self, values):
        product = self.env['vendor.product'].browse(values.get('vendor_product_id'))
        categ = product.product_category_id
        values['product_code'] = categ.sudo().get_product_default_code()
        return super(VendorProductVariant, self).create(values)
