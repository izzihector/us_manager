# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=True, ondelete='restrict',
                                    default=lambda self: self.env.user.department_id)

    @api.onchange('branch_id')
    def onchange_branch_department(self):
        if self.branch_id:
            self.department_id = self.branch_id.department_id.id

    def _prepare_invoice(self):
        self.ensure_one()
        res = super(SaleOrder, self)._prepare_invoice()
        res['department_id'] = self.department_id.id
        return res
