# -*- coding: utf-8 -*-
# Copyright 2020 Linksoft Mitra Informatika
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    vendor_product_variant_id = fields.Many2one(comodel_name="vendor.product.variant", string="Vendor Product Variant ", required=False, ondelete="restrict" )
    location_id = fields.Many2one(comodel_name="vendor.location", string="Location", required=False)
    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch")
    pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="Sales Pricelist", required=False,
                                   default=lambda self: self.env.ref('product.list0'))
    pricelist_item_id = fields.Many2one(comodel_name="product.pricelist.item", string="Related Pricelist Item")
    state = fields.Selection(string="Status", selection=[
        ('draft', 'Draft'),
        ('to_validate', 'Need to Validate'),
        ('validate', 'Validated')], default='draft')
    portal_input_price = fields.Float(string="Portal Input Price ", required=False,  )
    is_margin_included = fields.Boolean(string="Is Margin Included ", )
    margin_percentage = fields.Float(string="Margin Percentage ", required=False,  )
    price_wo_tax = fields.Float(string='Price Without Tax', compute="_compute_price_wo_tax")
    price_after_margin = fields.Float(string='Price After Margin', compute="_compute_price_wo_tax")

    def name_get(self):
        return [(record.id, record.vendor_product_id.product_name) for record in self]

    def write(self, values):
        for rec in self:
            if rec.state == 'validate' and 'state' not in values and rec.vendor_product_variant_id.product_id:
                values['state'] = 'to_validate'
        res = super(ProductSupplierInfo, self).write(values)
        for rec in self:
            if rec.pricelist_item_id:
                rec.pricelist_item_id.sudo().write({
                    'active': rec.active
                })
        return res

    def unlink(self):
        for rec in self:
            if rec.pricelist_item_id:
                rec.sudo().pricelist_item_id.unlink()
        return super(ProductSupplierInfo, self).unlink()

    @api.onchange('location_id')
    @api.depends('location_id')
    def onchange_vendor_location(self):
        for rec in self:
            rec.branch_id = rec.location_id.branch_id.id

    @api.depends('portal_input_price', 'vendor_product_id.sale_tax_id')
    def _compute_price_wo_tax(self):
        for record in self:
            taxes = record.vendor_product_id.sale_tax_id.compute_all(record.portal_input_price)
            record.price_wo_tax = taxes['total_excluded']
            record.price_after_margin = record.price_wo_tax * (100 - record.margin_percentage) / 100

    def action_create_pricelist(self):
        for rec in self:
            if not rec.pricelist_id:
                raise UserError("Please select sales pricelist before confirm prices.")
            if rec.vendor_product_variant_id:
                
                # EDIT By : Luki 07-02-2022. Tambahan kondisi cek variant nya punya product_id.
                if rec.vendor_product_variant_id.product_id:
                    rec.product_id = rec.vendor_product_variant_id.product_id.id
                    vals = {
                        'pricelist_id': rec.pricelist_id.id,
                        'applied_on': '0_product_variant',
                        'vendor_product_id': rec.vendor_product_id.id,
                        'product_id': rec.product_id.id,
                        'product_tmpl_id': rec.product_tmpl_id.id,
                        'min_quantity': rec.min_qty,
                        'date_start': rec.date_start,
                        'date_end': rec.date_end,
                        'compute_price': 'fixed',
                        # EDIT By : Brata Bayu 28-01-2022
                        'fixed_price': rec.portal_input_price
                        # =================================================
                        # 'fixed_price': (rec.vendor_product_id.margin_percentage + 100) / 100 * rec.price
                    }
                    if rec.pricelist_item_id:
                        rec.pricelist_item_id.write(vals)
                    else:
                        new_pl_item = self.env['product.pricelist.item'].create(vals)
                        rec.pricelist_item_id = new_pl_item.id
                    rec.state = 'validate'

    @api.model
    def create_price_from_portal(self, values):
        """
        The method to create product.supplierinfo from values and prepare defaults

        Returns:
          * success string
        """
        partner_id = self.env.user.partner_id.commercial_partner_id
        vendor_product_id = self.env['vendor.product'].browse(values.get('vendor_product_id')).sudo()
        values.update({
            "name": partner_id.id,
            "is_margin_included": partner_id.is_price_include_consignment_margin,
            "margin_percentage": vendor_product_id.margin_percentage,
        })
        portal_input_price = float(values.get('portal_input_price', '0'))
        if partner_id.is_price_include_consignment_margin:
            values['price'] = 100/(100+vendor_product_id.margin_percentage)*portal_input_price
        else:
            values['price'] = portal_input_price

        try:
            values.update({"date_start": fields.Date.from_string(values.get("date_start"))})
        except:
            values.update({"date_start": False})
        try:
            values.update({"date_end": fields.Date.from_string(values.get("date_end"))})
        except:
            values.update({"date_end": False})
        price_id = self.create(values)
        if price_id.location_id:
            vals = {
                'branch_id': price_id.location_id.branch_id.id,
                'pricelist_id': price_id.location_id.branch_id.default_pricelist_id.id or self.env.ref('product.list0').id
            }
            if price_id.vendor_product_id.state == 'validate' and price_id.vendor_product_variant_id.product_id:
                vals['state'] = 'to_validate'
            price_id.write(vals)
        return _("The price has been successfully registered")

    def write_price_from_portal(self, values):
        """
        The method to write product.supplierinfo from values

        Returns:
          * success string

        Extra info:
         * Expected singleton
        """
        try:
            values.update({"date_start": fields.Date.from_string(values.get("date_start"))})
        except:
            values.update({"date_start": False})
        try:
            values.update({"date_end": fields.Date.from_string(values.get("date_end"))})
        except:
            values.update({"date_end": False})
        portal_input_price = float(values.get('portal_input_price', '0'))
        if self.is_margin_included:
            values['price'] = 100/(100+self.margin_percentage)*portal_input_price
        else:
            values['price'] = portal_input_price
        price_id = self.write(values)

        if self.location_id:
            vals = {
                'branch_id': self.location_id.branch_id.id,
                'pricelist_id': self.location_id.branch_id.default_pricelist_id.id
            }
            if self.vendor_product_id.state == 'validate' and self.vendor_product_variant_id.product_id:
                vals['state'] = 'to_validate'
            self.write(vals)
        return _("The price has been successfully updated")

    @api.model
    def return_locations(self):
        """
        The method to return list of partner locations

        Returns:
         * dict
        """
        location_ids = self.env["vendor.location"].search([])
        return {"location_ids": location_ids.name_get()}

    @api.model
    def get_dialog_options(self, product_id):
        """
        The method to return options for portal dialog

        Methods:
         * return_currencies
         * return_locations

        Returns:
         * dict
        """
        vendor_product_id = self.env['vendor.product'].browse(product_id).sudo()
        if vendor_product_id:
            res = {
                "product_margin": vendor_product_id.margin_percentage or 0,
                "is_margin_included": vendor_product_id.partner_id.is_price_include_consignment_margin,
            }
            res.update(self.return_currencies())
            res.update(self.return_locations())
            return res
        return False

    def get_this_price_values(self):
        """
        The method to retrieve this supplierinfo values (used for js)

        Methods:
         * return_currencies
         * return_locations

        Returns:
         * dict
           ** id
           ** portal_input_price
           ** is_margin_included
           ** min_qty
           ** date_start
           ** date_end
           ** product_margin
           ** state

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        res = {
            "id": self.id,
            "portal_input_price": self.portal_input_price,
            "is_margin_included": self.is_margin_included,
            "min_qty": self.min_qty,
            "date_start": self.date_start,
            "date_end": self.date_end,
            "vendor_product_id": self.vendor_product_id.id,
            "currency_id": self.currency_id.id,
            "location_id": self.location_id.id,
            "product_margin": self.margin_percentage,
            "state": self.state,
        }
        res.update(self.return_currencies())
        res.update(self.return_locations())
        return res

    @api.onchange('portal_input_price')
    def onchange_portal_input_price(self):
        if self.name.is_price_include_consignment_margin:
            self.price = 100/(100+self.vendor_product_id.margin_percentage)*self.portal_input_price
        else:
            self.price = self.portal_input_price
