# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo.exceptions import UserError
from odoo import models, fields, api, _


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _accumulate_amounts(self, data):
        data = super(PosSession, self)._accumulate_amounts(data)

        amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}

        stock_expense = defaultdict(amounts)
        stock_output = defaultdict(amounts)

        for order in self.order_ids:
            if not order.is_invoiced:
                for order_line in order.lines:
                    if order_line.fix_discount > 0 or order_line.discount > 0:
                        if order_line.fix_discount > 0:
                            amount_disc = round(order_line.fix_discount / 1.1)
                        elif order_line.fix_amount_discount > 0:
                            amount_disc = round(order_line.fix_amount_discount / 1.1)
                        else:
                            amount_disc = round(((order_line.price_unit * order_line.qty) / 1.1)) - order_line.price_subtotal
                        # line = self._prepare_line(order_line)
                        if order_line.product_id.is_consignment:
                            account = order_line.order_id.config_id.department_id.account_discount_consign_id.id
                            if not account:
                                raise UserError(_('Please define discount account for this POS'))
                        else:
                            account = order_line.order_id.config_id.department_id.account_discount_depart_id.id
                            if not account:
                                raise UserError(_('Please define discount account for this POS'))

                        # discount
                        sale_key = (
                            # account
                            account,
                            # sign
                            2,
                            # for taxes
                            (),
                            (),
                        )
                        line = self._prepare_line(order_line)

                        data['sales'][sale_key] = self._update_amounts(data['sales'][sale_key], {'amount': -1 * amount_disc}, line['date_order'])

                        # Combine income + discount
                        sale_key = (
                            # account
                            line['income_account_id'],
                            # sign
                            -1 if line['amount'] < 0 else 1,
                            # for taxes
                            tuple((tax['id'], tax['account_id'], tax['tax_repartition_line_id']) for tax in line['taxes']),
                            line['base_tags'],
                        )
                        data['sales'][sale_key] = self._update_amounts(data['sales'][sale_key], {'amount': amount_disc},
                                                               line['date_order'])

                if self.company_id.anglo_saxon_accounting and order.picking_id.id:
                    # Combine stock lines
                    order_pickings = self.env['stock.picking'].search([
                        '|',
                        ('origin', '=', '%s - %s' % (self.name, order.name)),
                        ('id', '=', order.picking_id.id)
                    ])
                    stock_moves = self.env['stock.move'].search([
                        ('picking_id', 'in', order_pickings.ids),
                        ('company_id.anglo_saxon_accounting', '=', True),
                        ('product_id.categ_id.property_valuation', '=', 'real_time')
                    ])
                    for move in stock_moves:
                        # get expense and stock output account from department
                        if move.product_id.is_consignment:
                            output_account = self.config_id.department_id.account_expense_consign_id
                            account = self.config_id.department_id.account_stock_output_consign_id
                        else:
                            account = self.config_id.department_id.account_expense_depart_id
                            output_account = move.product_id.categ_id.property_stock_account_output_categ_id
                        exp_key = account or move.product_id.property_account_expense_id or move.product_id.categ_id.property_account_expense_categ_id
                        out_key = output_account or move.product_id.categ_id.property_stock_account_output_categ_id
                        amount = -sum(move.sudo().stock_valuation_layer_ids.mapped('value'))
                        if move.product_id.is_consignment:
                            vendor_product = self.env['vendor.product.variant'].sudo().search([('product_id', '=', move.product_id.id)])
                            if vendor_product:
                                margin = vendor_product.margin_percentage
                            else:
                                margin = move.product_id.owner_id.consignment_margin
                            orderlines = order.lines.filtered(lambda l: l.product_id == move.product_id)
                            # By Matrica - LLha

                            subtotal = sum(orderlines.mapped('price_subtotal')) / sum(orderlines.mapped('qty'))
                            if orderlines.fix_discount > 0 or orderlines.discount > 0:
                                if order_line.fix_discount > 0:
                                    amount_disc = round(order_line.fix_discount / 1.1)
                                elif order_line.fix_amount_discount > 0:
                                    amount_disc = round(order_line.fix_amount_discount / 1.1)
                                else:
                                    amount_disc = round(
                                        ((orderlines.price_unit * orderlines.qty) / 1.1)) - orderlines.price_subtotal
                                amount_disc = amount_disc / orderlines.qty if orderlines.qty != 0 else 0

                                subtotal += amount_disc

                            price = subtotal * ((100 - margin) / 100)

                            amount = -price * move.quantity_done

                            if orderlines.fix_discount > 0 or orderlines.discount > 0:
                                if order_line.fix_discount > 0:
                                    amount_disc = round(order_line.fix_discount / 1.1)
                                elif order_line.fix_amount_discount > 0:
                                    amount_disc = round(order_line.fix_amount_discount / 1.1)
                                else:
                                    amount_disc = round(
                                        ((orderlines.price_unit * orderlines.qty) / 1.1)) - orderlines.price_subtotal
                                vshared = 1
                                if orderlines.custom_discount_id:
                                    if orderlines.custom_discount_id:
                                        vshared = orderlines.custom_discount_id.vendor_shared / 100
                                    else:
                                        vshared = orderlines.vendor_shared / 100
                                amount_disc = amount_disc * vshared

                                amount += amount_disc

                            # price = sum(orderlines.mapped('price_subtotal')) / sum(orderlines.mapped('qty')) * (
                            #             (100 - margin) / 100)
                            # amount = -price * move.quantity_done

                            # !By Matrica - LLha
                        stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                        stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
        data.update({
            'stock_expense': stock_expense,
            'stock_output': stock_output,
        })
        return data


    def _get_sale_vals(self, key, amount, amount_converted):
        account_id, sign, tax_keys, base_tag_ids = key
        res = super(PosSession, self)._get_sale_vals(key, amount, amount_converted)
        if sign == 2:
            name = 'Discount untaxed'
            res.update({
                'name': name
            })
        return res