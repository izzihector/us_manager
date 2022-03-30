# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", compute='compute_department_id', store=True)

    @api.depends('stock_move_id')
    def compute_department_id(self):
        for rec in self:
            dest_department = rec.stock_move_id.location_dest_id.department_id
            if dest_department:
                rec.department_id = dest_department.id
            else:
                rec.department_id = rec.stock_move_id.location_id.department_id

    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.context.get('department'):
            args.append(('department_id', '=', self.env.context['department']))
        return super(StockValuationLayer, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
