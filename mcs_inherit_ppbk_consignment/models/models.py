# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    def get_ppbk(self):
        end_date = self.consignment_date_end + relativedelta(days=1)

        data = self.env['ppbk.report'].with_context({'partner_id': self.partner_id.id, 'branch_id': self.branch_id.id,
                                                     'start_date': str(self.consignment_date_start),
                                                     'end_date': str(end_date)}).get_report_data()

        print(data)
        return data

