# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    _auto = False

    department_id = fields.Many2one('hr.department', 'Department', readonly=True)

    def _select(self):
        res = super(PurchaseReport, self)._select()
        res += ', po.department_id as department_id'
        return res

    def _group_by(self):
        res = super(PurchaseReport, self)._group_by()
        res += ', po.department_id'
        return res
