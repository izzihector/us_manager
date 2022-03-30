############################################################################
#  Module Name: pos
#  Kelas: discount_sharing
#  File Name: pos_custom_discount_inherit.py
#  Created On: 19/11/2021, 09.43
#  Description:  Sharing Discount
#  Author: Matrica Consulting - (teguh)
#  Snipet: tp_model_inherit_extend
############################################################################
# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
# from odoo import exceptions, _
# from datetime import date
# from datetime import timedelta
# import logging

class discountSharingInherit(models.Model):
    """
    `1 '.' (child: line_ids)
    """
    # ORM ------------------------------------------------------------------------------------ ORM #
    _inherit = ['pos.custom.discount']              # model diextend

    sequence_number = fields.Char(string='Sequence #', readonly=True, required=True, copy=False, default='New')

    # Sequence Number Method
    @api.model
    def create(self, vals):
        vals['sequence_number'] = self.env['ir.sequence'].next_by_code('pos.custom.discount') or _('New')
        return super(discountSharingInherit, self).create(vals)

    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor Name',
                                ondelete='set null', index=True, contex={}, domain=[])
    vendor_shared = fields.Float(string='Vendor Shared (%)', digits=(5, 2))
    sarinah_shared = fields.Float(string='Sarinah Shared (%)', digits=(5, 2), readonly=True)

    active = fields.Boolean(string="Aktif?", default=True)
    apply_on = fields.Selection(default='product')

    @api.onchange('vendor_shared')
    def _onchange_discount_shared(self):
        self.sarinah_shared = 100 - self.vendor_shared
        if self.sarinah_shared < 0:
            self.sarinah_shared = 0

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        self.product_ids = None
        # if self.vendor_id:
        #     return {'domain': {'product_ids': [('owner_id', '=', self.vendor_id.id)]}}
        # else:
        #     return {'domain': {'product_ids': []}}

