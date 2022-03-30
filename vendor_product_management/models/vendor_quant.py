#coding: utf-8

from odoo import _, api, fields, models


class vendor_quant(models.Model):
    """
    The model to keep supplier stocks
    """
    _name = "vendor.quant"
    _description = "Vendor Stocks"
    _rec_name = "product_name"

    @api.depends("supplier_quantity", "supplier_product_uom_id", "vendor_product_id.product_id.uom_po_id")
    def _compute_product_quantity(self):
        """
        Compute method for product_uom_id, product_quantity

        Methods:
         * _compute_quantity of uom.uom
        """
        for quant in self:
            product_quantity = quant.supplier_quantity
            uom_error = False
            product_uom_id = False
            if quant.vendor_product_id.product_id and quant.supplier_product_uom_id:
                product_uom_id = quant.vendor_product_id.product_id.uom_po_id
                product_uom_id = product_uom_id
                try:
                    product_quantity = quant.supplier_product_uom_id._compute_quantity(
                        qty=quant.supplier_quantity,
                        to_unit=product_uom_id or product_uom_id,
                    )
                except:
                    product_quantity = quant.supplier_quantity
                    uom_error = _("Vendor unit of measure is from different category than our product UoM")
            elif not quant.vendor_product_id.product_id:
                uom_error = _("No product is assigned for related vendor product")
            else:
                uom_error = _("Vendor unit of measure is not defined")
            quant.product_quantity = product_quantity
            quant.uom_error = uom_error
            quant.product_uom_id = product_uom_id

    @api.onchange("vendor_product_id")
    def _onchange_vendor_product_id(self):
        """
        Onchange method for vendor_product_id

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        domain = []
        value = {}
        if self.vendor_product_id:
            domain = ["|", ("partner_id", "=", self.vendor_product_id.partner_id.id), ("partner_id", "=", False)]
            if self.vendor_location_id and self.vendor_location_id.partner_id \
                    and self.vendor_location_id.partner_id != self.vendor_product_id.partner_id:
                value = {"vendor_location_id": False}
        return {
            "domain": {"vendor_location_id": domain},
            "value": value,
        }

    @api.onchange("vendor_location_id")
    def _onchange_vendor_location_id(self):
        """
        Onchange method for vendor_location_id

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        domain = []
        value = {}
        if self.vendor_location_id and self.vendor_location_id.partner_id:
            domain = [("partner_id", "=", self.vendor_location_id.partner_id.id)]
            if self.vendor_product_id  and self.vendor_location_id.partner_id != self.vendor_product_id.partner_id:
                value = {"vendor_product_id": False}
        return {
            "domain": {"vendor_product_id": domain},
            "value": value,
        }

    vendor_product_id = fields.Many2one(
        "vendor.product",
        string="Vendor Product",
        ondelete='cascade',
        required=True,
    )
    vendor_location_id = fields.Many2one(
        "vendor.location",
        string="Vendor Location",
        ondelete='cascade',
        required=True,
    )
    supplier_quantity = fields.Float(
        string="Vendor Quantity",
    )
    supplier_product_uom_id = fields.Many2one(
        'uom.uom',
        'Vendor Unit of Measure',
        help="if not set, default product purchase unit of measure would be used",
    )
    product_quantity = fields.Float(
        string="Quantity",
        compute=_compute_product_quantity,
        compute_sudo=True,
        store=True,
        help="in default product unit of measure",
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        'Unit of Measure',
        compute=_compute_product_quantity,
        compute_sudo=True,
        store=True,
    )
    write_date = fields.Datetime(
        string="Last Update",
    )
    uom_error = fields.Char(
        string="UoM Warning",
        compute=_compute_product_quantity,
        compute_sudo=True,
        store=True,
    )
    # Related fields for views
    partner_id = fields.Many2one(
        related="vendor_location_id.partner_id",
        compute_sudo=True,
        store=True,
        string="Location Vendor",
    )
    product_partner_id = fields.Many2one(
        related="vendor_product_id.partner_id",
        compute_sudo=True,
        store=True,
        string="Vendor",
    )
    delivery_time = fields.Integer(
        related="vendor_location_id.delivery_time",
        compute_sudo=True,
        store=True,
    )
    product_name = fields.Char(
        related="vendor_product_id.product_name",
        compute_sudo=True,
        store=True,
    )
    product_code = fields.Char(
        related="vendor_product_id.product_code",
        compute_sudo=True,
        store=True,
    )
    product_id = fields.Many2one(
        related="vendor_product_id.product_id",
        compute_sudo=True,
        store=True,
        string="Product Variant",
    )
    product_tmpl_id = fields.Many2one(
        related="vendor_product_id.product_tmpl_id",
        compute_sudo=True,
        store=True,
        string="Product Template",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )


    _sql_constraints = [
        (
            'supplier_quantity_check',
            'check (supplier_quantity>=0)',
             _('Inventory can not be negative!')
        ),
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        """
        Overwrite to trigger recalc on variants and templates
        The problem is that the decorator 'api depends' does not work correctly for o2m creates

        Methods:
         * _compute_vendor_quantity pf product.product and product.template
        """
        quants = super(vendor_quant, self).create(vals_list)
        vendor_products = quants.mapped("vendor_product_id")
        templates = vendor_products.mapped("product_tmpl_id")
        variants = vendor_products.mapped("product_id")
        templates.sudo()._compute_vendor_quantity()
        variants.sudo()._compute_vendor_quantity()
        return quants    
    
    def name_get(self):
        """
        Overloading the method, to reflect parent's name recursively
        """
        result = []
        for product in self:
            name = u"[{}] {}".format(
                product.product_code and product.product_code or '',
                product.product_name and product.product_name or '',
                # product.partner_id and product.partner_id.name or '',
            )
            result.append((product.id, name))
        return result

    @api.model
    def _find_quant(self, product, location):
        """
        The method to find vendor product by code and name

        Args:
         * product - int - vendor.product id
         * location - int - vendor.location id

        Returns:
         * int - vendor.product id
         * False if any not found
        """
        quants = self._search([
            ("vendor_product_id", "=", product),
            ("vendor_location_id", "=", location),
            "|",
                ("active", "=", True),
                ("active", "=", False),
        ], limit=1)
        return quants and quants[0] or False
