# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritPosPromotion(models.Model):
    _inherit = 'pos.promotion'

    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor Name',
                                ondelete='set null', index=True, contex={}, domain=[])
    vendor_shared = fields.Float(string='Vendor Shared (%)', digits=(5, 2))
    sarinah_shared = fields.Float(string='Sarinah Shared (%)', digits=(5, 2), readonly=True)

    product_id_qty = fields.Many2many('product.product','pos_product_id_qty_rel', string='Product')

    available_in_pos = fields.Many2many('pos.config', string="POS Config")

    @api.onchange('vendor_shared')
    def _onchange_discount_shared(self):
        self.sarinah_shared = 100 - self.vendor_shared
        if self.sarinah_shared < 0:
            self.sarinah_shared = 0

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        self.pos_condition_ids = None
        self.pos_quntity_ids = None
        self.product_id_qty = None
        self.product_id_amt = None
        self.multi_products_discount_ids = None


class PosConfig(models.Model):
    _inherit = 'pos.config'

    promotion_ids = fields.Many2many('pos.promotion', string="Promotions")


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    custom_promotion_id = fields.Many2one(comodel_name='pos.promotion', string="Custom Promotion")

    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor Name',
                                ondelete='set null', index=True, contex={}, domain=[])
    vendor_shared = fields.Float(string='Vendor Shared (%)', digits=(5, 2))
    sarinah_shared = fields.Float(string='Sarinah Shared (%)', digits=(5, 2), readonly=True)
    fix_amount_discount = fields.Float(string='Fix Amount Discount')

# class PosOrderLine(models.Model):
#     _inherit = 'pos.order.line'
#
#     custom_discount_id = fields.Many2one(comodel_name='pos.custom.discount', string="Custom Discount")