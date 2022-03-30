# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    # TODO : should be as same as purchase order's department
    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch", required=False, ondelete='restrict',
                                default=lambda self: self.env.user.branch_id)
    department_id = fields.Many2one(comodel_name="hr.department", string="Department")

    @api.model
    def create(self, vals):
        department = self.env.context.get('department_id', False)
        if department:
            vals.update({'department_id': department})
        return super(ProductSupplierInfo, self).create(vals)

    @api.onchange('branch_id')
    def onchange_branch_department(self):
        if self.branch_id:
            self.department_id = self.branch_id.department_id.id
