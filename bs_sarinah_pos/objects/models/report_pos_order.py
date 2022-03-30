# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class ReportPOSOrder(models.Model):
    _inherit = 'report.pos.order'
    _auto = False

    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)
    is_consignment = fields.Boolean(string='Is Consignment', readonly=True)
    payment_type = fields.Selection(string='Payment Type', selection=[
        ('cash', 'Cash'), ('bank', 'Bank'), ('cash_and_bank', 'Cash and Bank')])

    def _select(self):
        res = super(ReportPOSOrder, self)._select()
        res += """
            , s.branch_id as branch_id
            , pt.is_consignment as is_consignment
            , s.payment_type as payment_type
        """
        return res

    def _group_by(self):
        res = super(ReportPOSOrder, self)._group_by()
        res += ', s.branch_id, pt.is_consignment'
        return res
