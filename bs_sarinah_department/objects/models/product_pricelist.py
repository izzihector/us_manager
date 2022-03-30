# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch", required=False, ondelete='restrict',
                                default=lambda self:self.env.user.branch_id)
    department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=False, ondelete='restrict',
                            default=lambda self:self.env.user.department_id)

    @api.onchange('branch_id')
    def onchange_branch_department(self):
        if self.branch_id:
            self.department_id = self.branch_id.department_id.id
