# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _create_out_svl(self, forced_quantity=None):
        return super(StockMove, self.with_context({
            'department_id': self[0].location_id.department_id.id,
            'branch_id': self[0].location_id.branch_id.id,
        }))._create_out_svl(forced_quantity=forced_quantity)

    def _create_in_svl(self, forced_quantity=None):
        return super(StockMove, self.with_context({
            'department_id': self[0].location_dest_id.department_id.id,
            'branch_id': self[0].location_dest_id.branch_id.id,
        }))._create_in_svl(forced_quantity=forced_quantity)
