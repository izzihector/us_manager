# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
import itertools
import json
from odoo import api, fields, models
from odoo.exceptions import UserError


class VendorProduct(models.Model):
    _inherit = 'vendor.product'

    state = fields.Selection(string="Status", selection=[
        ('draft', 'Need to Validate'),
        ('validate', 'Validated')], default='draft')
    product_category_id = fields.Many2one(comodel_name="product.category", string="Product Category ", required=True,  )
    margin_percentage = fields.Float(string="Margin Percentage", compute="_compute_margin_percentage")
    pricelist_item_ids = fields.One2many(comodel_name="product.pricelist.item", inverse_name="vendor_product_id",
                                         string="Pricelist Items")
    pricelist_item_count = fields.Integer(string="Pricelist Item Count", compute='compute_pricelist_item_count')
    minimum_quantity = fields.Float(string="Safety Stock", default=0, required=False,  )
    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure", required=False,  )
    product_brand_id = fields.Many2one(comodel_name='product.brand', string='Brand')
    product_brand_margin_id = fields.Many2one(comodel_name='product.brand.margin',
            string='Product Brand Margin', compute="_compute_product_brand_margin_id")
    attribute_line_ids = fields.One2many(comodel_name="vendor.product.attr.line", inverse_name="vendor_product_id", string="Attribute Line ", required=False, ondelete="cascade")
    product_variant_ids = fields.One2many(comodel_name="vendor.product.variant", inverse_name="vendor_product_id", string="Product Variant ", required=False, ondelete="cascade")
    product_variant_count = fields.Integer(string="Product Variant Count", compute='_compute_product_variant_count')
    product_id = fields.Many2one('product.product', 'Product Variant')
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    image_ids = fields.One2many(comodel_name='vendor.product.image', inverse_name='product_id', string='Product Images')
    sale_tax_id = fields.Many2many(comodel_name='account.tax', string='Sale Tax')
    product_manufacture_code = fields.Char(string='Vendor Manufacture Code')
    is_variant_need_update = fields.Boolean(string='Is Variant Need Update', compute="_compute_is_variant_need_update")

    @api.model
    def create(self, values):
        sale_tax = self.env.user.company_id.sudo().account_sale_tax_id
        values.update({
            'sale_tax_id': sale_tax.ids
        })
        record = super(VendorProduct, self).create(values)
        record_sudo = record.sudo()
        if not record.product_code:
            product_code = record_sudo.product_category_id.get_product_default_code()
            record.product_code = product_code
        brand_code = record.product_brand_id.code or ''
        category_id = record.product_category_id
        category_name = f'{category_id.parent_id.name} {category_id.name}'.strip()
        record.product_name = f'{brand_code} {category_name} {record.product_name}'.upper()
        return record

    def write(self, values):
        result = super(VendorProduct, self).write(values)
        if values.get('attribute_line_ids', False):
            self.update_product_variant()
        return result

    @api.depends(
        'partner_id.consignment_margin',
        'product_brand_id.consignment_margin',
        'product_brand_margin_id.consignment_margin'
    )
    def _compute_margin_percentage(self):
        for record in self:
            record_sudo = record.sudo()
            percentage = record_sudo.partner_id.consignment_margin
            if record_sudo.product_brand_id.consignment_margin > 0:
                percentage = record_sudo.product_brand_id.consignment_margin
            if record_sudo.product_brand_margin_id.consignment_margin > 0:
                percentage = record_sudo.product_brand_margin_id.consignment_margin
            record_sudo.margin_percentage = percentage

    @api.depends('product_category_id', 'product_brand_id')
    def _compute_product_brand_margin_id(self):
        for record in self:
            if record.product_category_id and self.product_brand_id:
                brand_margin_id = self.env['product.brand.margin'].search([
                    ('brand_id', '=', record.product_brand_id.id),
                    ('category_id', '=', record.product_category_id.id),
                ], limit=1)
                if brand_margin_id:
                    record.product_brand_margin_id = brand_margin_id.id
                    return
            record.product_brand_margin_id = False

    @api.depends('image_attachment_id.datas', )
    def _compute_image(self):
        for record in self:
            record.image = record.image_attachment_id.datas

    def compute_pricelist_item_count(self):
        for product in self:
            product.pricelist_item_count = len(product.pricelist_item_ids)

    def _compute_product_variant_count(self):
        for record in self:
            record.product_variant_count = len(record.product_variant_ids)

    @api.depends('product_variant_ids')
    def _compute_is_variant_need_update(self):
        for product in self:
            variant_is_missing = self.product_variant_ids.filtered(lambda variant: not variant.product_id)
            product.is_variant_need_update = len(variant_is_missing) > 0

    def action_validate(self):
        for product in self:
            if product.state == 'draft':
                product.generate_product()
                product.product_tmpl_id.write({
                    'owner_id': product.partner_id.id
                })
                product.write({'state': 'validate'})
                product.price_ids.write({
                    'state': 'to_validate'
                })

    def generate_product(self):
        product_tmpl_obj = self.env['product.template']
        product_image_obj = self.env['product.image']
        for product in self:
            attributes = []
            for attr in product.attribute_line_ids:
                attributes.append([0, 0, {'attribute_id': attr.attribute_id.id, 'value_ids': [[6, False, attr.mapped('value_ids').ids]]}])
            product_tmpl = product_tmpl_obj.with_context({'from_portal': True}).create({
                'name': product.product_name,
                'sale_ok': True,
                'purchase_ok': False,
                'owner_id': product.partner_id.id,
                'categ_id': product.product_category_id.id,
                'brand_id': product.product_brand_id.id,
                'uom_id': product.product_uom_id.id,
                'uom_po_id': product.product_uom_id.id,
                'available_in_pos': True,
                'attribute_line_ids': attributes,
                'type': 'product',
                'default_code': product.product_code
            })
            # auto approve for product
            product_tmpl.active = True
            product.product_tmpl_id = product_tmpl.id
            for variant in product.product_variant_ids:
                product_variant = product_tmpl.product_variant_ids.filtered(
                    lambda v: sorted(v.product_template_attribute_value_ids.mapped('name')) == sorted(
                        variant.attribute_value_ids.mapped('name')))
                variant.write({
                    'product_id': product_variant.id
                })
                product_variant.write({
                    'default_code': variant.product_code
                })
            product_tmpl.image_1920 = product.image_ids and product.image_ids[0].image_1920
            for image_id in product.image_ids[1:]:
                product_image_obj.create({
                    'name': image_id.name or product_tmpl.name,
                    'image_1920': image_id.image_1920,
                    'product_tmpl_id': product_tmpl.id,
                });

    def update_product_variant_on_validated_product(self):
        for product in self:
            product_tmpl_id = product.product_tmpl_id
            if product.state == 'validate' and product_tmpl_id:
                attributes = [(5, 0, 0)]
                for attr in product.attribute_line_ids:
                    attributes.append([0, 0, {'attribute_id': attr.attribute_id.id, 'value_ids': [[6, False, attr.mapped('value_ids').ids]]}])
                product_tmpl_id.write({'attribute_line_ids': attributes})
                for variant in product.product_variant_ids:
                    product_variant =product_tmpl_id.product_variant_ids.filtered(
                        lambda v: sorted(v.product_template_attribute_value_ids.mapped('name')) == sorted(
                            variant.attribute_value_ids.mapped('name')))
                    variant.write({'product_id': product_variant.id})
                    variant.variant_price_ids.filtered(lambda price: price.state == 'draft').state = 'to_validate'
                    product_variant.write({'default_code': variant.product_code})

    def action_confirm_pricelist(self):
        for product in self:
            product.price_ids.action_create_pricelist()

    def action_view_pricelist(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pricelist Items',
            'res_model': 'product.pricelist.item',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.pricelist_item_ids.ids)],
            'context': {
                'create': False,
                'edit': False,
                'delete': False
            }
        }

    def action_view_variant(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Variants',
            'res_model': 'vendor.product.variant',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.product_variant_ids.ids)],
            'context': {
                'create': False,
                'edit': True,
                'delete': False
            }
        }

    def action_draft(self):
        for product in self:
            if product.state == 'validate':
                product.write({
                    'state': 'draft'
                })
                product.price_ids.write({
                    'state': 'draft'
                })

    def get_images(self):
        self.ensure_one()
        return [{
            'id': image.id,
            'name': image.name,
            'binary': image.image_1920,
        } for image in self.image_ids]

    def get_attributes(self):
        all_attributes = self.env['product.attribute'].search([])

        available_attributes = [{
            'id': attribute.id,
            'name': attribute.name,
            'values': attribute.value_ids.read(['id', 'name']),
        } for attribute in all_attributes if attribute not in self.attribute_line_ids.mapped('attribute_id')]

        attributes = [{
            'id': attribute.id,
            'name': attribute.attribute_id.name,
            'values': attribute.attribute_id.value_ids.read(['id', 'name']),
            'selected_value_ids': attribute.value_ids.ids,
        } for attribute in self.attribute_line_ids]

        return {
                'product_id': self.id,
                'attributes': attributes,
                'available_attributes': available_attributes,
                'is_readonly': len(self.price_ids) and 'validate' in self.price_ids.mapped('state')
        }

    def get_variants(self):
        return [{
            'id': variant.id,
            'product_name': '[%s] %s' % (variant.product_code, variant.product_name),
            'attributes': variant.attribute_value_ids.mapped('name'),
            'prices': [
                ('{symbol} {amount}' if price.currency_id.position == 'before' else '{amount} {symbol}').format(
                    symbol=price.currency_id.symbol,
                    amount='{:20,.2f}'.format(price.portal_input_price)
                )
            for price in variant.variant_price_ids],
            'vendor_prices': [
                ('{symbol} {amount}' if price.currency_id.position == 'before' else '{amount} {symbol}').format(
                    symbol=price.currency_id.symbol,
                    amount='{:20,.2f}'.format(price.sudo().price_after_margin)
                )
            for price in variant.variant_price_ids],
        } for variant in self.product_variant_ids]

    def get_this_product_values(self):
        """
        The method to retrieve this product values (used for js)

        Returns:
         * dict
           ** id
           ** product_category_id
           ** product_category_ids
           ** product_margin
           ** product_manufacture_code
           ** product_name
           ** product_brand_id
           ** product_brand_ids
           ** product_uom_id
           ** product_uom_ids
           ** product_minimum_quantity
           ** description
           ** product_brand_margin_ids

        Extra info:
         * Expected singleton
        """
        available_uom_ids = self.env['uom.uom'].sudo().search([
            ('category_id.is_available_on_portal', '=', True)
        ])
        available_category_ids = self.env['product.category'].sudo().search([
            ('is_available_on_portal', '=', True)
        ])
        available_brand_margin_ids = self.env['product.brand.margin'].sudo().search([
            ('category_id', 'in', available_category_ids.ids)
        ])
        available_brand_ids = self.env['product.brand'].sudo().search([
            ('id', 'in', self.env.user.partner_id.brand_ids.ids)
        ], order='name')
        consignment_margin = self.env.user.partner_id.consignment_margin
        # if available_brand_ids and available_brand_ids[0].consignment_margin:
        #     consignment_margin = available_brand_ids[0].consignment_margin
        if available_brand_margin_ids and available_brand_margin_ids[0].consignment_margin:
            consignment_margin = available_brand_margin_ids[0].consignment_margin

        available_category_values =  [{
            'id': categ.id,
            'display_name': categ.display_name,
            'consignment_margin': categ.consignment_margin or self.env.user.partner_id.consignment_margin,
        } for categ in available_category_ids]

        available_brand_values =  [{
            'id': brand.id,
            'display_name': brand.display_name,
            'margin': brand.consignment_margin,
        } for brand in available_brand_ids]

        available_brand_margin_values =  [{
            'brand_id': margin.brand_id.id,
            'category_id': margin.category_id.id,
            'margin': margin.consignment_margin
        } for margin in available_brand_margin_ids]

        values = {
            "product_margin": consignment_margin,
            "partner_consignment_margin": self.env.user.partner_id.consignment_margin,
            "product_uom_ids": available_uom_ids.name_get(),
            "product_category_ids": available_category_values,
            "product_brand_ids": available_brand_values,
            "product_brand_margin_ids": available_brand_margin_values,
        }
        if len(self):
            values.update({
                "id": self.id,
                "product_category_id": self.product_category_id.id,
                "product_brand_id": self.product_brand_id.id,
                "product_margin": self.margin_percentage,
                "product_manufacture_code": self.product_manufacture_code,
                "product_name": self.product_name,
                "product_uom_id": self.product_uom_id.id,
                "product_minimum_quantity": self.minimum_quantity,
                "description": self.description,
            })
        return values

    def create_attribute_from_portal(self, attribute_id, value_ids):
        self.ensure_one();
        if len(value_ids) == 0:
            raise UserError('Values attribute can\'t be empty!')
        values = {
                'vendor_product_id': self.id,
                'attribute_id': attribute_id,
                'value_ids': [(6, 0, value_ids)],
        }
        self.env['vendor.product.attr.line'].create(values)
        self.update_product_variant()
        return True

    def delete_attribute_from_portal(self, attribute_id):
        attr_to_delete = self.attribute_line_ids.filtered(lambda attr: attr.id == attribute_id)
        result = attr_to_delete.unlink()
        self.update_product_variant()
        return result or False

    # Please read following url to understand what this method do.
    # https://github.com/odoo/odoo/blob/13.0/addons/product/models/product_template.py#L552
    def update_product_variant(self):
        self.flush()
        Product = self.env["vendor.product.variant"]

        variants_to_create = []
        variants_to_activate = Product
        variants_to_unlink = Product

        for tmpl_id in self:
            lines_without_no_variants = tmpl_id.attribute_line_ids

            all_variants = tmpl_id.with_context(active_test=False).product_variant_ids.sorted(lambda p: (p.active, -p.id))

            current_variants_to_create = []
            current_variants_to_activate = Product

            single_value_lines = lines_without_no_variants.filtered(lambda ptal: len(ptal.value_ids) == 1)
            if single_value_lines:
                for variant in all_variants:
                    combination = variant.attribute_value_ids | single_value_lines.value_ids
                    variant.attribute_value_ids = combination

            existing_variants = {
                variant.attribute_value_ids: variant for variant in all_variants
            }

            all_combinations = itertools.product(*[
                ptal.value_ids for ptal in lines_without_no_variants
            ])
            for combination_tuple in all_combinations:
                combination = self.env['product.attribute.value'].concat(*combination_tuple)
                if combination.ids:
                    if combination in existing_variants:
                        current_variants_to_activate += existing_variants[combination]
                    else:
                        current_variants_to_create.append({
                            'vendor_product_id': tmpl_id.id,
                            'attribute_value_ids': [(6, 0, combination.ids)],
                            'active': tmpl_id.active,
                        })
                        if len(current_variants_to_create) > 1000:
                            raise UserError(_(
                                'The number of variants to generate is too high. '
                                'You should either not generate variants for each combination or generate them on demand from the sales order. '
                                'To do so, open the form view of attributes and change the mode of *Create Variants*.'))
            variants_to_create += current_variants_to_create
            variants_to_activate += current_variants_to_activate

            variants_to_unlink += all_variants - current_variants_to_activate

        if variants_to_activate:
            variants_to_activate.write({'active': True})
        if variants_to_create:
            Product.create(variants_to_create)
        if variants_to_unlink:
            variants_to_unlink.unlink_or_archive()

        self.flush()
        self.invalidate_cache()
        return True

    @api.onchange('product_brand_id', 'product_category_id')
    def _onchange_autonaming(self):
        self.name = ''
        brand = ''
        categ = ''
        if self.product_brand_id:
            brand = self.product_brand_id.code or ''
        if self.product_category_id:
            categ = (self.product_category_id.parent_id.name + ' ' if self.product_category_id.parent_id else '') + self.product_category_id.name
        self.product_name = brand.upper() + ' ' + categ.upper()
