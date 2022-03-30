# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department")
    allowed_department_ids = fields.Many2many(comodel_name="hr.department", string="Allowed Department(s)",
                                              compute='compute_department_id', store=True)

    def compute_department_id(self):
        for location in self:
            warehouse = self.env['stock.warehouse'].search([('view_location_id', 'parent_of', self.ids)], limit=1)
            location.department_id = warehouse.department_id.id
            location.allowed_department_ids = warehouse.allowed_department_ids.ids

    @api.model
    def create(self, vals):
        res = super(StockLocation, self).create(vals)
        res.compute_department_id()
        return res

    def write(self, vals):
        res = super(StockLocation, self).write(vals)
        if 'department_id' not in vals and 'allowed_department_ids' not in vals:
            self.compute_department_id()
        return res
