# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department")

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMove, self).default_get(default_fields)
        if 'department_id' not in res or not res.get('department_id'):
            res.update({
                'department_id' : self.env.user.department_id.id
            })
            if self._context.get('department_id'):
                department_id = self._context.get('department_id')
                res.update({
                    'department_id': department_id
                })
        return res

    @api.onchange('branch_id')
    def onchange_branch_department(self):
        if self.branch_id:
            self.department_id = self.branch_id.department_id.id

    # override to calculate cost of product consignment
    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):

        ''' Prepare values used to create the journal items (account.move.line) corresponding to the Cost of Good Sold
        lines (COGS) for customer invoices.

        Example:

        Buy a product having a cost of 9 being a storable product and having a perpetual valuation in FIFO.
        Sell this product at a price of 10. The customer invoice's journal entries looks like:

        Account                                     | Debit | Credit
        ---------------------------------------------------------------
        200000 Product Sales                        |       | 10.0
        ---------------------------------------------------------------
        101200 Account Receivable                   | 10.0  |
        ---------------------------------------------------------------

        This method computes values used to make two additional journal items:

        ---------------------------------------------------------------
        220000 Expenses                             | 9.0   |
        ---------------------------------------------------------------
        101130 Stock Interim Account (Delivered)    |       | 9.0
        ---------------------------------------------------------------

        Note: COGS are only generated for customer invoices except refund made to cancel an invoice.

        :return: A list of Python dictionary to be passed to env['account.move.line'].create.
        '''
        lines_vals_list = []
        for move in self:
            if not move.is_sale_document(include_receipts=True) or not move.company_id.anglo_saxon_accounting:
                continue

            for line in move.invoice_line_ids:

                # Filter out lines being not eligible for COGS.
                if line.product_id.type != 'product' or line.product_id.valuation != 'real_time':
                    continue

                # Retrieve accounts needed to generate the COGS.
                # add context to send invoice department
                accounts = (
                    line.product_id.product_tmpl_id
                    .with_context(force_company=line.company_id.id, department=move.department_id.id)
                    .get_product_accounts(fiscal_pos=move.fiscal_position_id)
                )
                debit_interim_account = accounts['stock_output']
                credit_expense_account = accounts['expense']
                if not credit_expense_account:
                    if self.type == 'out_refund':
                        credit_expense_account = self.journal_id.default_credit_account_id
                    else: # out_invoice/out_receipt
                        credit_expense_account = self.journal_id.default_debit_account_id
                if not debit_interim_account or not credit_expense_account:
                    continue

                # Compute accounting fields.
                sign = -1 if move.type == 'out_refund' else 1
                if line.product_id.is_consignment:
                    vendor_product = self.env['vendor.product.variant'].sudo().search(
                        [('product_id', '=', line.product_id.id)])
                    if vendor_product:
                        margin = vendor_product.margin_percentage
                    else:
                        margin = line.product_id.owner_id.consignment_margin
                    price_unit = line.price_subtotal / line.quantity * (100-margin) / 100
                    if line.sale_line_ids:
                        credit_expense_account = line.sale_line_ids[0].department_id.account_expense_consign_id or credit_expense_account
                        debit_interim_account = line.sale_line_ids[0].department_id.account_stock_output_consign_id or debit_interim_account
                else:
                    price_unit = line._stock_account_get_anglo_saxon_price_unit()
                balance = sign * line.quantity * price_unit

                # Add interim account line.
                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': price_unit,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'account_id': debit_interim_account.id,
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })

                # Add expense account line.
                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': -price_unit,
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'account_id': credit_expense_account.id,
                    'analytic_account_id': line.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })
        return lines_vals_list

    @api.model
    def create(self, vals_list):
        if self.env.context.get('department_id'):
            vals_list['department_id'] = self.env.context.get('department_id')
        if self.env.context.get('branch_id'):
            vals_list['branch_id'] = self.env.context.get('branch_id')
        return super(AccountMove, self).create(vals_list)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", related='move_id.department_id',
                                    store=True)

    def _get_computed_account(self):
        self.ensure_one()
        res = super(AccountMoveLine, self)._get_computed_account()
        if self.move_id.department_id:
            if self.move_id.is_sale_document(include_receipts=True):
                # Out invoice.
                if self.product_id.is_consignment:
                    return self.move_id.department_id.account_income_consign_id or res
                else:
                    return self.move_id.department_id.account_income_depart_id or res
            elif self.move_id.is_purchase_document(include_receipts=True):
                # In invoice.
                if self.product_id.is_consignment:
                    return self.move_id.department_id.account_expense_consign_id or res
                elif not self.product_id.is_consignment and self.product_id.type != 'product':
                    return self.move_id.department_id.account_expense_depart_id or res
        return res
