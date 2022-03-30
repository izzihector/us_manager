# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", related='order_id.department_id')

    def write(self, vals):
        if self.env.context.get('purchase_request_id'):
            if self[0].order_id.is_ga:
                return super(PurchaseOrderLine, self.sudo()).write(vals)
        return super(PurchaseOrderLine, self).write(vals)
