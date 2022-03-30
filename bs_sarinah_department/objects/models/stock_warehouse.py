# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", ondelete='restrict')
    allowed_department_ids = fields.Many2many(comodel_name="hr.department", string="Allowed Department(s)")

    @api.model
    def create(self, vals):
        res = super(StockWarehouse, self).create(vals)
        locations = self.env['stock.location'].search([('location_id', 'child_of', res.view_location_id.id)])
        locations.compute_department_id()
        return res

    def write(self, vals):
        res = super(StockWarehouse, self).write(vals)
        for wh in self:
            locations = self.env['stock.location'].search([('location_id', 'child_of', wh.view_location_id.id)])
            locations.compute_department_id()
        return res

    @api.onchange('branch_id')
    def onchange_branch_department(self):
        if self.branch_id:
            self.department_id = self.branch_id.department_id.id
