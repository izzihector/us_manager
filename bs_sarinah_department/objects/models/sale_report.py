# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'
    _auto = False

    department_id = fields.Many2one('hr.department', 'Department', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['department_id'] = ', s.department_id as department_id'
        groupby += ', s.department_id'
        res = super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
        return res
