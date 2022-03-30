# -*- coding: utf-8 -*-
# Copyright 2021 Linksoft Mitra Informatika

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError

OPERATION_TYPE_OPTIONS = [
    ('incoming', 'Receipt'),
    ('outgoing', 'Return'),
]

class VendorStockPicking(models.Model):
    _name = 'vendor.stock.picking'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Vendor Stock Picking'
    
    name = fields.Char(string="Name ", default="Draft", required=True,  )
    vendor_move_ids = fields.One2many(comodel_name="vendor.stock.move", inverse_name="vendor_picking_id", string="Vendor Move ", required=False,  )

    state = fields.Selection(string="State ", default="draft", selection=[("draft","Draft "), ("validate","Validated")],  )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Vendor ", required=True,  )
    vendor_location_id = fields.Many2one(comodel_name="vendor.location", string="Vendor Location ", required=True,  )
    vendor_reference = fields.Char(string="Vendor Reference ", required=False,  )
    picking_ids = fields.Many2many(comodel_name="stock.picking", string="Picking ", required=False,  )
    access_url = fields.Char(string="Access Url ", compute="_compute_access_url",  )
    operation_type = fields.Selection(string='Operation Type', default="incoming", selection=OPERATION_TYPE_OPTIONS)


    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError("Sorry you can only delete draft vendor DO.")
        return super(VendorStockPicking, self).unlink()

    def _compute_access_url(self):
        for record in self:
            record.access_url = u'/my/delivery_orders/%s' % record.id

    @api.model
    def create(self, values):
        if values.get('name', 'Draft') == 'Draft':
            sequence_id = self.env.ref('bs_sarinah_portal.seq_vendor_stock_picking')
            values['name'] = sequence_id.sudo().next_by_id()
        return super(VendorStockPicking, self).create(values)

    def get_portal_values(self):
        location_ids = self.env['vendor.location'].search([])
        product_ids = self.env['vendor.product.variant'].search([])
        uom_ids = self.env['uom.uom'].sudo().search([])
        values = {
            'location_ids': location_ids.name_get(),
            'product_ids': product_ids.read(['display_name', 'product_uom_id']),
            'uom_ids': uom_ids.name_get(),
        }
        if self:
            self.ensure_one()
            values.update({
                'reference': self.vendor_reference,
                'location_id': self.vendor_location_id.id,
                'move_ids': self.vendor_move_ids.read(['vendor_product_variant_id', 'quantity', 'product_uom_id']),
            })
        return values

    def create_from_portal(self, values):
        if self and self.state != 'draft':
            return self.access_url
        picking_value = {
            'vendor_reference': values.get('reference'),
            'partner_id': self.env.user.partner_id.id,
            'vendor_location_id': values.get('location_id'),
            'operation_type': values.get('operation_type'),
        }
        if self:
            picking_id = self
            picking_value['operation_type'] = picking_id.operation_type
            picking_id.write(picking_value)
            move_ids = [move.get('id') for move in values.get('move_lines')]
            move_to_delete = picking_id.vendor_move_ids.filtered(lambda move: move.id not in move_ids)
            move_to_delete.unlink()
        else:
            picking_id = self.create(picking_value)
        for move in values.get('move_lines'):
            if move.get('id'):
                self.vendor_move_ids.browse(move['id']).write({
                    'vendor_picking_id': picking_id.id,
                    'vendor_product_variant_id': move.get('vendor_product_variant_id'),
                    'quantity': move.get('quantity'),
                })
            else:
                self.vendor_move_ids.create({
                    'vendor_picking_id': picking_id.id,
                    'vendor_product_variant_id': move.get('vendor_product_variant_id'),
                    'quantity': move.get('quantity'),
                })
        return picking_id.access_url
        
    def delete_from_portal(self):
        if self and self.state != 'draft':
            return self.access_url
        self.unlink()
        return u'/my/delivery_orders'

    def action_open_picking(self):
        self.ensure_one()
        action = {
            'name': 'Stock Receipts',
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

    def action_fill_and_validate(self):
        self.ensure_one()
        action = {
            'name': "Validate %s" % ('Delivery Order' if self.operation_type == 'incoming' else 'DO Return'),
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.vendor.stock.picking',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('bs_sarinah_portal.wizard_vendor_stock_picking').id,
            'target': 'new',
            'context': {
                'default_picking_id': self.id
            }
        }
        return action

    def action_validate(self):
        # Generate picking
        for rec in self:
            if rec.state == 'draft':
                picking_type = self.env['stock.picking.type'].search([
                    ('code', '=', rec.operation_type),
                    ('warehouse_id', '=', rec.vendor_location_id.location_id.get_warehouse().id),
                ], limit=1)
                if not picking_type:
                    picking_type = self.env['purchase.order']._default_picking_type()
                if picking_type.code == 'incoming':
                    location_values = {
                        'location_id': self.env.ref('stock.stock_location_suppliers').id,
                        'location_dest_id': rec.vendor_location_id.location_id.id,
                    }
                elif picking_type.code == 'outgoing':
                    location_values = {
                        'location_id': rec.vendor_location_id.location_id.id,
                        'location_dest_id': self.env.ref('stock.stock_location_suppliers').id,
                    }
                picking_values = {
                    'partner_id': rec.partner_id.id,
                    'picking_type_id': picking_type.id,
                    'owner_id': rec.partner_id.id,
                    'origin': rec.name,
                }
                picking_values.update(location_values)
                picking_id = self.env['stock.picking'].create(picking_values)
                for move_id in rec.vendor_move_ids:
                    product_id = move_id.vendor_product_variant_id.product_id
                    if not product_id:
                        raise UserError('Missing product variant (product.product) at vendor product variant (vendor.product.variant) for product %s.' % move_id.vendor_product_variant_id.display_name)
                    move_values = {
                        'picking_id': picking_id.id,
                        'product_id': product_id.id,
                        'name': move_id.name,
                        'product_uom_qty': move_id.quantity_received,
                        'product_uom': move_id.product_uom_id.id,
                        'picking_type_id': picking_type.id,
                        'origin': rec.name,
                    }
                    move_values.update(location_values)
                    self.env['stock.move'].create(move_values)
                picking_id.action_confirm()
                picking_id.action_assign()
                # Process all the quantities without input move line.
                immidiate_transfer = self.env['stock.immediate.transfer'].create({
                    'pick_ids': [(4, picking_id.id)]
                })
                immidiate_transfer.process()
                rec.picking_ids = [(4, picking_id.id, 0)]
                rec.state = 'validate'


class VendorStockMove(models.Model):
    _name = 'vendor.stock.move'
    _description = 'Vendor Stock Move'
    
    name = fields.Char(string="Name ", required=True,  )
    vendor_picking_id = fields.Many2one(comodel_name="vendor.stock.picking", string="Vendor Picking ", required=True, ondelete="cascade", )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner ", related="vendor_picking_id.partner_id",  )
    vendor_product_id = fields.Many2one(comodel_name="vendor.product", string="Product ", required=False, ondelete="restrict" )
    vendor_product_variant_id = fields.Many2one(comodel_name="vendor.product.variant", string="Vendor Product Variant ", required=False, ondelete="restrict" )
    # price_id = fields.Many2one(comodel_name="product.supplierinfo", string="Price ", required=False, domain=[('id', 'in', product_id.price_ids.ids)])
    quantity = fields.Float(string="Quantity Delivered", required=False,  )
    quantity_received = fields.Float(string="Quantity Received ", required=False,  )
    balance = fields.Float(string="Balance ", compute="_compute_balance",  )
    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure", related="vendor_product_id.product_uom_id",  )

    # EDIT BY : BRATA BAYU
    # EDITED BY : LLH
    @api.model
    def create(self, values):
        if not values.get('name') and values.get('vendor_product_variant_id'):
            product_id = self.env['vendor.product.variant'].browse(values['vendor_product_variant_id'])
            values['name'] = product_id.product_name
        result = super(VendorStockMove, self).create(values)  # edited
        if result.vendor_product_variant_id:  # edited
            result.vendor_product_id = result.vendor_product_variant_id.vendor_product_id.id
        return result
    

    @api.onchange('vendor_product_variant_id', )
    def _onchange_vendor_product_variant_id(self):
        for record in self:
            record.name = record.vendor_product_variant_id.product_name


    @api.depends('quantity', 'quantity_received')
    def _compute_balance(self):
        for record in self:
            balance = record.quantity - record.quantity_received
            record.balance = balance
    
