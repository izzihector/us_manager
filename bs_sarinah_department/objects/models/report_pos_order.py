# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class ReportPOSOrder(models.Model):
    _inherit = 'report.pos.order'
    _auto = False

    department_id = fields.Many2one('hr.department', 'Department', readonly=True)

    def _select(self):
        res = super(ReportPOSOrder, self)._select()
        res += ', s.department_id as department_id'
        return res

    def _group_by(self):
        res = super(ReportPOSOrder, self)._group_by()
        res += ', s.department_id'
        return res
