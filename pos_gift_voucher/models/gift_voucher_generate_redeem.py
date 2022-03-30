# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


class pos_order(models.Model):
    _inherit = "pos.order"

    omset_voucher = fields.Float()

    batch_qty_values = fields.Char('Batch No.', size=128)

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        """Create account.bank.statement.lines from the dictionary given to the parent function.

        If the payment_line is an updated version of an existing one, the existing payment_line will first be
        removed before making a new one.
        :param pos_order: dictionary representing the order.
        :type pos_order: dict.
        :param order: Order object the payment lines should belong to.
        :type order: pos.order
        :param pos_session: PoS session the order was created in.
        :type pos_session: pos.session
        :param draft: Indicate that the pos_order is not validated yet.
        :type draft: bool.
        """
        prec_acc = order.pricelist_id.currency_id.decimal_places

        order_bank_statement_lines = self.env['pos.payment'].search([('pos_order_id', '=', order.id)])
        order_bank_statement_lines.unlink()
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
                order.add_payment(self._payment_fields(order, payments[2]))

        order.amount_paid = sum(order.payment_ids.mapped('amount'))

        if not draft and not float_is_zero(pos_order['amount_return'], prec_acc):
            cash_payment_method = pos_session.payment_method_ids.filtered(
                lambda payment_method: payment_method.is_cash_count and not payment_method.for_gift_coupens)[:1]
            if not cash_payment_method:
                raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
            return_payment_vals = {
                'name': _('return'),
                'pos_order_id': order.id,
                'amount': -pos_order['amount_return'],
                'payment_date': fields.Date.context_today(self),
                'payment_method_id': cash_payment_method.id,
            }
            order.add_payment(return_payment_vals)

    @api.model
    def create_from_ui(self, orders, draft=False):
        order_ids = super(pos_order, self).create_from_ui(orders, draft)
        data = orders[0]['data']
        if 'coupon_redeemed' in data and data['coupon_redeemed']:
            i = 0
            while (i < len(data['coupon_redeemed'])):
                iddd = self.env['gift.voucher'].search([('voucher_serial_no', '=', data['coupon_redeemed'][i])])
                self._cr.commit()
                iddd.write({'redeemed_in': True})
                i = i + 1

        if 'coupon_name' in data and data['coupon_name'] == True:
            coup_id = data['coupon_id']
            c_unique_no = data['coupon_unique_no']
            print("coupon_id:::::::::", coup_id)
            print("c_unique_no::::::", c_unique_no)
            i = 0
            while (i < len(c_unique_no)):
                coupon = self.env['product.product'].browse(int(coup_id[i]))
                validity_in_days = coupon.validity
                order_date = datetime.strptime(str(datetime.today().date()), '%Y-%m-%d')
                exp_date = order_date + timedelta(days=validity_in_days)
                self.env['gift.voucher'].create({
                    'voucher_name': coupon.name,
                    'qty': 1.0,
                    'uom': coupon.uom_id.id,
                    'company_id': data['company'],
                    'date': order_date,
                    'voucher_serial_no': data['coupon_unique_no'][i],
                    'source': data['name'],
                    'redeemed_out': True,
                    'amount': coupon.list_price,
                    'voucher_validity': validity_in_days,
                    'last_date': exp_date,
                    'product_id': coupon.id,
                    'remaining_amt': coupon.list_price,
                    'used_amt': 0,
                })
                i = i + 1
        return order_ids
