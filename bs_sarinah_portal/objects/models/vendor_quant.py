# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models
from odoo.exceptions import UserError


class VendorQuant(models.Model):
    _inherit = 'vendor.quant'

    state = fields.Selection(string="Status", selection=[
        ('draft', 'Need to Validate'),
        ('validate', 'Validated')], default='draft')
    validation_method = fields.Char(string="Validation Method ", required=False,  )
    picking_ids = fields.Many2many(comodel_name="stock.picking", string="Picking ", required=False,  )
    inventory_ids = fields.Many2many(comodel_name="stock.inventory", string="Inventory ", required=False,  )

    @api.model
    def return_options(self, productID=False):
        """
        The method to prepare available locations and units of measures

        Methods:
         * name_get of vendor.location
         * name_get of uom.uom

        Returns:
         * dict
          ** location_ids
          ** product_uom_name
        """
        location_ids = self.env["vendor.location"].search([])
        product_id = self.env['vendor.product'].browse(productID)
        return {
            "location_ids": location_ids.name_get(),
            "product_uom_name": product_id.sudo().product_uom_id.name
        }

    def get_this_stock_values(self):
        values = super(VendorQuant, self).get_this_stock_values()
        values.update({
            "product_uom_name": self.vendor_product_id.sudo().product_uom_id.name
        })
        return values

    @api.model
    def create_stock_from_portal(self, values):
        product_id = self.env['vendor.product'].browse(int(values.get('vendor_product_id')))
        values.update({
            "supplier_product_uom_id": product_id.sudo().product_uom_id.id
        })
        return super(VendorQuant, self).create_stock_from_portal(values)

    def write(self, vals):
        for rec in self:
            if rec.state == 'validate' and 'state' not in vals:
                vals['state'] = 'draft'
        return super(VendorQuant, self).write(vals)

    def action_open_picking(self):
        self.ensure_one()
        action = {
            'name': 'Vendor DO',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }
        if len(self.picking_ids) == 1:
            action['res_id'] = self.picking_ids.id
            action['view_mode'] = 'form'
        else:
            action['domain'] = [('id', 'in', self.picking_ids.ids)]
            action['view_mode'] = 'tree,form'
        return action

    def action_open_inventory(self):
        self.ensure_one()
        action = {
            'name': 'Inventory Adjustment',
            'res_model': 'stock.inventory',
            'type': 'ir.actions.act_window',
        }
        if len(self.inventory_ids) == 1:
            action['res_id'] = self.inventory_ids.id
            action['view_mode'] = 'form'
        else:
            action['domain'] = [('id', 'in', self.inventory_ids.ids)]
            action['view_mode'] = 'tree,form'
        return action

    # This action will validate the document by different method according to system parameters.
    def action_validate(self):
        IPC = self.env['ir.config_parameter'].sudo()
        validation_method = IPC.get_param('vendor_portal.quant_validation_method')

        # Set validation method to be goods receipt by default.
        if not validation_method:
            IPC.set_param('vendor_portal.quant_validation_method', 'goods_receipt')
            validation_method = 'goods_receipt'

        # Decide which method to be used.
        if validation_method == 'goods_receipt':
            self._validate_with_goods_receipt()
        elif validation_method == 'inventory_adjustment':
             self._validate_with_inventory_adjustment()
        # To prevent wrong configuration.
        else:
            raise UserError("Please set validation method either using inventory_adjustment or goods_receipt")
        self.write({
            'validation_method': validation_method,
            'state': 'validate'
        })

    def _validate_with_goods_receipt(self):
        for rec in self:
            if rec.state == 'draft':
                if not rec.vendor_location_id.location_id:
                    raise UserError("Please set stock location for vendor location {}.".format(rec.vendor_location_id.name))
                picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', rec.vendor_location_id.location_id.get_warehouse().id)], limit=1)
                if not picking_type:
                    picking_type = self.env['purchase.order']._default_picking_type()
                picking_id = self.env['stock.picking'].create({
                    'partner_id': rec.product_partner_id.id,
                    'picking_type_id': picking_type.id,
                    'location_id': self.env.ref('stock.stock_location_suppliers').id,
                    'location_dest_id': rec.vendor_location_id.location_id.id,
                    'owner_id': rec.product_partner_id.id
                })
                self.env['stock.move'].create({
                    'picking_id': picking_id.id,
                    'product_id': rec.vendor_product_id.product_id.id,
                    'name': rec.vendor_product_id.product_id.display_name,
                    'product_uom_qty': rec.product_quantity,
                    'product_uom': rec.product_uom_id.id,
                    'picking_type_id': picking_type.id,
                    'location_id': self.env.ref('stock.stock_location_suppliers').id,
                    'location_dest_id': rec.vendor_location_id.location_id.id,
                })
                picking_id.action_confirm()
                picking_id.action_assign()
                # Process all the quantities without input move line.
                immidiate_transfer = self.env['stock.immediate.transfer'].create({
                    'pick_ids': [(4, picking_id.id)]
                })
                immidiate_transfer.process()
                rec.picking_ids = [(4, picking_id.id, 0)]


    def _validate_with_inventory_adjustment(self):
        for rec in self:
            if rec.state == 'draft':
                if not rec.vendor_location_id.location_id:
                    raise UserError("Please set stock location for vendor location {}.".format(rec.vendor_location_id.name))
                inventory = self.env['stock.inventory'].create({
                    'name': 'Vendor Stock {} in {} - {} - {}'.format(rec.product_partner_id.name, rec.vendor_location_id.name,
                                                                     rec.product_id.name,
                                                                     rec.write_date.strftime("%d/%m/%Y")),
                    'location_ids': rec.vendor_location_id.location_id.ids,
                    'product_ids': rec.product_id.ids,
                    'branch_id': rec.vendor_location_id.branch_id.id,
                })
                inventory.action_start()
                existing_line = self.env['stock.inventory.line'].search([
                    ('partner_id', '=', rec.product_partner_id.id),
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', '=', rec.vendor_location_id.location_id.id),
                    ('inventory_id', '=', inventory.id)]),
                if existing_line:
                    existing_line.write({
                        'product_qty': rec.product_quantity,
                        'product_uom_id': rec.product_uom_id.id,
                    })
                else:
                    self.env['stock.inventory.line'].create({
                        'inventory_id': inventory.id,
                        'partner_id': rec.product_partner_id.id,
                        'location_id': rec.vendor_location_id.location_id.id,
                        'product_id': rec.product_id.id,
                        'product_qty': rec.product_quantity,
                        'product_uom_id': rec.product_uom_id.id,
                    })
                inventory.action_validate()
                rec.inventory_ids = [(4, inventory.id, 0)]

