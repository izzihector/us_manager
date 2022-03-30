# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        return super(SaleAdvancePaymentInv,
                     self.with_context({'department_id': order.department_id.id}))._create_invoice(order=order,
                                                                                                   so_line=so_line,
                                                                                                   amount=amount)
