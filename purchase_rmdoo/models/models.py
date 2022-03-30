# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import datetime
import odoo.addons.decimal_precision as dp
# from addons.purchase_requisition.models.purchase_requisition import PURCHASE_REQUISITION_STATES


class ResCompany(models.Model):
    _inherit = 'res.company'

    po_double_validation = fields.Selection([
        ('one_step', 'Confirm purchase orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a purchase order'),
        ('three_step', 'Get 3 levels of approvals to confirm a purchase order'),
        ('four_step', 'Get 4 levels of approvals to confirm a purchase order'),
    ], string="Levels of Approvals", default='one_step', help="Provide a double validation mechanism for purchases")
    po_double_validation2 = fields.Selection([
        ('one_step', 'Confirm purchase orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a purchase order'),
        ('three_step', 'Get 3 levels of approvals to confirm a purchase order'),
        ('four_step', 'Get 4 levels of approvals to confirm a purchase order'),
    ], string="Levels of Approvals", default='one_step', help="Provide a double validation mechanism for purchases")
    po_double_validation_amount = fields.Monetary(string='Double validation amount', default=5000000,
        help="Minimum amount for which a double validation is required")
    po_triple_validation_amount = fields.Monetary(string='Triple validation amount', default=10000000,
        help="Minimum amount for which a triple validation is required")
    po_quadruple_validation_amount = fields.Monetary(string='Quadruple validation amount', default=20000000,
        help="Minimum amount for which a quadruple validation is required")
    department_ga_id = fields.Many2one('hr.department', 'Purchase Department')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    po_order_approval = fields.Boolean("P/O Approval (Manager)", default=lambda self: self.env.user.company_id.po_double_validation in ('two_step', 'three_step', 'four_step'))
    po_double_validation_amount = fields.Monetary(related='company_id.po_double_validation_amount', string="Minimum Amount", currency_field='company_currency_id', readonly=False)
    po_order_approval_triple = fields.Boolean("P/O Approval (Tim Pengadaan)", default=lambda self: self.env.user.company_id.po_double_validation in ('three_step', 'four_step'))
    po_triple_validation_amount = fields.Monetary(related='company_id.po_triple_validation_amount', string="Minimum Amount", currency_field='company_currency_id', readonly=False)
    po_order_approval_quadruple = fields.Boolean("P/O Approval (Tim Lelang)", default=lambda self: self.env.user.company_id.po_double_validation in ('four_step'))
    po_quadruple_validation_amount = fields.Monetary(related='company_id.po_quadruple_validation_amount', string="Minimum Amount", currency_field='company_currency_id', readonly=False)
    pr_combine = fields.Boolean(string="Purchase Request Combine", config_parameter='purchase_rmdoo.default_pr_combine')
    department_ga_id = fields.Many2one(related='company_id.department_ga_id', string='Purchase Department', readonly=False)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.po_order_approval_quadruple:
            self.po_double_validation = 'four_step'
        elif self.po_order_approval_triple:
            self.po_double_validation = 'three_step'
        elif self.po_order_approval:
            self.po_double_validation = 'two_step'
        else:
            self.po_double_validation = 'one_step'
        self.env.user.company_id.po_double_validation2 = self.env.user.company_id.po_double_validation
    
    @api.model
    def init_purchase_rmdoo(self):
        # dp = self.env.ref('product.decimal_discount').id
        dpo = self.env['decimal.precision'].browse(self.env.ref('product.decimal_discount').id)
        dpo.write({'digits':14})
        
        self.env['ir.sequence'].browse(self.env.ref('purchase.seq_purchase_order').id).write({
            'prefix':'PO%(y)s%(month)s%(day)s-',
            'padding':4,
            'reset':'monthly',
            'use_date_range':True,
        })
        self.env['ir.sequence'].browse(self.env.ref('purchase_requisition.seq_purchase_tender').id).write({
            'prefix':'TE%(y)s%(month)s%(day)s-',
            'padding':4,
            'reset':'monthly',
            'use_date_range':True,
        })
        self.env['ir.sequence'].browse(self.env.ref('purchase_requisition.seq_blanket_order').id).write({
            'prefix':'BO%(y)s%(month)s%(day)s-',
            'padding':4,
            'reset':'monthly',
            'use_date_range':True,
        })
        
        self.env.user.company_id.po_double_validation = self.env.user.company_id.po_double_validation2
        self.create({
            # 'group_lot_on_delivery_slip' : True,
            # 'group_warning_purchase' : True,
            # 'module_purchase_requisition' : True,
            # 'module_stock_dropshipping' : True,
            'group_manage_vendor_price' : True,
            'group_warning_purchase' : True,
            'use_po_lead' : True,
        }).execute()
        

class ResDiscountPurchase(models.Model):
    _name = 'res.discount.purchase'
    _description = 'Purchase Discount'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10, required=True)
    discounts = fields.Many2one('res.discount', ondelete='restrict', required=True)
    order_line_id = fields.Many2one('purchase.order.line', required=True, ondelete='cascade')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    def update_price(self):
        return True
    
    @api.depends('order_line.qty_invoiced', 'order_line.qty_received', 'order_line.product_qty')
    def _compute_outstanding(self):
        for line in self:
            line.outstanding_account = False
            line.outstanding_stock = False
            for lines in line.order_line:
                if lines.qty_invoiced < lines.product_qty:
                    line.outstanding_account = True
                if lines.qty_received < lines.product_qty:
                    line.outstanding_stock = True
                    
    @api.depends('origin')
    def _get_replenish(self):
        rep_obj = self.env['product.replenish.request']
        op_obj = self.env['stock.warehouse.orderpoint']
        for record in self:
            origins = [str(origin).strip() for origin in str(record.origin).split(',')]
            record.product_replenish_request_ids = rep_obj.search([
                ('company_id', '=', self.env['res.company']._company_default_get('product.replenish.request').id),
                ('group_id.name', 'in', origins)
            ])
            record.orderpoint_ids = op_obj.search([
                ('company_id', '=', self.env['res.company']._company_default_get('stock.warehouse.orderpoint').id),
                ('name', 'in', origins)
            ])
            replenish_list = []
            for prr_id in record.product_replenish_request_ids:
                if prr_id.replenish_request_id:
                    replenish_list.append(prr_id.replenish_request_id.id)

            record.replenish_request_ids = replenish_list

            if record.replenish_request_ids:
                replenish_request_is_ga = record.replenish_request_ids.mapped('is_ga')
                if True in replenish_request_is_ga:
                    record.is_ga = True
                    record.department_id = record.company_id.department_ga_id.id
                else:
                    record.is_ga = False
                    record.department_id = record.replenish_request_ids[0].request_department_id.id

    # discounts = fields.Many2one('res.discount', string='Discount Total', ondelete='restrict')
    # taxes_id = fields.Many2many('account.tax', 'po_tax', 'po_id', 'tax_id', string='Taxes List')
    confirm4_uid = fields.Many2one('res.users', string='Approved By', readonly=True)
    confirm3_uid = fields.Many2one('res.users', string='Approved By', readonly=True)
    confirm2_uid = fields.Many2one('res.users', string='Approved By', readonly=True)
    confirm_uid = fields.Many2one('res.users', string='Confirmed By', readonly=True)
    outstanding_stock = fields.Boolean(string='Outstanding Stock', compute='_compute_outstanding', store=True)
    outstanding_account = fields.Boolean(string='Outstanding Invoice', compute='_compute_outstanding', store=True)
    po_double_validation = fields.Selection([
        ('one_step', 'Confirm purchase orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a purchase order'),
        ('three_step', 'Get 3 levels of approvals to confirm a purchase order'),
        ('four_step', 'Get 4 levels of approvals to confirm a purchase order'),
    ], string="Levels of Approvals", default='one_step', related='company_id.po_double_validation', help="Provide a double validation mechanism for purchases")
    product_replenish_request_ids = fields.Many2many('product.replenish.request', string='Purchase Request Line', compute='_get_replenish', store=True)
    replenish_request_ids = fields.Many2many('replenish.request', string='Purchase Request', compute='_get_replenish', store=True)
    orderpoint_ids = fields.Many2many('stock.warehouse.orderpoint', string='Reordering Rule', compute='_get_replenish', store=True)
    is_ga = fields.Boolean('Is GA?', store=True)

    def button_split(self):
        if self.ensure_one():
            return {
                'name': 'Split RFQ',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'view_mode': 'form',
                'view_id': self.env.ref('purchase_rmdoo.view_purchase_order_split_form').id,
                'src_model': 'purchase.order',
                'res_model': 'purchase.order.split',
                'context': {
                    'default_po_id': self.id,
                    'default_partner_id': self.partner_id.id,
                    'default_date_planned': self.date_planned,
                    'default_line_ids': [(0, 0, {
                        'po_line_int': line.id,
                        'po_line_id': line.id,
                        'product_uom': line.product_uom.id,
                        'product_qty': line.product_qty,
                        'base_qty': line.product_qty
                    }) for line in self.order_line]
                },
            }
        else:
            return False
    
    
    def button_approve(self, force=False, approve=False):
        if approve:
            super(PurchaseOrder, self).button_approve(force=force)
        else:
            self.button_confirm()
        return {}
    
    
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'to approve']:
                continue
            order._add_supplier_to_product()                
            approve = False
            if order.company_id.po_double_validation == 'four_step':
                if order.amount_total >= self.env.user.company_id.currency_id._convert(order.company_id.po_quadruple_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                    if self.confirm3_uid:
                        if order.user_has_groups('purchase_rmdoo.group_purchase_president'):
                            self.confirm4_uid = self.env.user.id
                            approve = True
                    elif self.confirm2_uid:
                        if order.user_has_groups('purchase_rmdoo.group_purchase_vp'):
                            self.confirm3_uid = self.env.user.id
                    elif self.confirm_uid:
                        if order.user_has_groups('purchase.group_purchase_manager'):
                            self.confirm2_uid = self.env.user.id
                    else:
                        self.confirm_uid = self.env.user.id
                elif order.amount_total >= self.env.user.company_id.currency_id._convert(order.company_id.po_triple_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                    if self.confirm2_uid:
                        if order.user_has_groups('purchase_rmdoo.group_purchase_vp'):
                            self.confirm3_uid = self.env.user.id
                            approve = True
                    elif self.confirm_uid:
                        if order.user_has_groups('purchase.group_purchase_manager'):
                            self.confirm2_uid = self.env.user.id
                    else:
                        self.confirm_uid = self.env.user.id
                elif order.amount_total >= self.env.user.company_id.currency_id._convert(order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                    if self.confirm_uid:
                        if order.user_has_groups('purchase.group_purchase_manager'):
                            self.confirm2_uid = self.env.user.id
                            approve = True
                    else:
                        self.confirm_uid = self.env.user.id
                else:
                    self.confirm_uid = self.env.user.id
                    approve = True
            elif order.company_id.po_double_validation == 'three_step':
                if order.amount_total >= self.env.user.company_id.currency_id._convert(order.company_id.po_triple_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                    if self.confirm2_uid:
                        if order.user_has_groups('purchase_rmdoo.group_purchase_vp'):
                            self.confirm3_uid = self.env.user.id
                            approve = True
                    elif self.confirm_uid:
                        if order.user_has_groups('purchase.group_purchase_manager'):
                            self.confirm2_uid = self.env.user.id
                    else:
                        self.confirm_uid = self.env.user.id
                elif order.amount_total >= self.env.user.company_id.currency_id._convert(order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                    if self.confirm_uid:
                        if order.user_has_groups('purchase.group_purchase_manager'):
                            self.confirm2_uid = self.env.user.id
                            approve = True
                    else:
                        self.confirm_uid = self.env.user.id
                else:
                    self.confirm_uid = self.env.user.id
                    approve = True
            elif order.company_id.po_double_validation == 'two_step':
                if order.amount_total >= self.env.user.company_id.currency_id._convert(order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()):
                    if self.confirm_uid:
                        if order.user_has_groups('purchase.group_purchase_manager'):
                            self.confirm2_uid = self.env.user.id
                            approve = True
                    else:
                        self.confirm_uid = self.env.user.id
                else:
                    self.confirm_uid = self.env.user.id
                    approve = True
            else:
                self.confirm_uid = self.env.user.id
                approve = True
            if approve:
                order.button_approve(approve=approve)
            else:
                order.write({'state': 'to approve'})
        return True


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    # @api.depends('product_qty', 'price_unit', 'discounts', 'discounts.discounts', 'discounts.sequence', 'order_id.discounts')
    # def _get_real_discount(self):
    #     for line in self:
    #         total_discount = 0.0
    #         for line_discounts in line.discounts:
    #             if line_discounts.discounts.discount_type == 'percentage':
    #                 total_discount += (line_discounts.discounts.value * (100.0 - total_discount) / 100.0)
    #             elif line_discounts.discounts.discount_type == 'fixed':
    #                 if line.product_qty != 0 and line.price_unit != 0:
    #                     total_discount += (line_discounts.discounts.value / (line.product_qty * line.price_unit) * 100.0)
    #         if line.order_id.discounts and line.order_id.discounts.discount_type == 'percentage':
    #             total_discount += (line.order_id.discounts.value * (100.0 - total_discount) / 100.0)
    #         elif line.order_id.discounts and line.order_id.discounts.discount_type == 'fixed':
    #             line_count = 0
    #             for line_for_count in line.order_id.order_line:
    #                 if line_for_count.product_qty != 0 and line_for_count.price_unit != 0:
    #                     line_count += 1
    #             if line.product_qty != 0 and line.price_unit != 0 and line_count != 0:
    #                 total_discount += ((line.order_id.discounts.value / line_count) / (line.product_qty * line.price_unit) * 100.0)
    #         line.discount = total_discount
    #
    # @api.depends('discounts', 'discount')
    # def _discount_to_display(self):
    #     for line in self:
    #         display = []
    #         for line_discounts in line.discounts:
    #             display.append(line_discounts.discounts.name)
    #         if line.order_id.discounts and line.order_id.discounts.discount_type == 'percentage':
    #             display.append(line.order_id.discounts.name)
    #         elif line.order_id.discounts and line.order_id.discounts.discount_type == 'fixed':
    #             line_count = 0
    #             for line_for_count in line.order_id.order_line:
    #                 if line_for_count.product_qty != 0 and line_for_count.price_unit != 0:
    #                     line_count += 1
    #             display.append('%.2f' % (line.order_id.discounts.value / line_count))
    #         if display:
    #             line.discount_display = ' + '.join(display)
    #         else:
    #             line.discount_display = ''
                
    @api.depends('product_qty', 'qty_received', 'qty_invoiced')
    def _outstanding_balance(self):
        for line in self:
            line.balance_received = line.product_qty - line.qty_received 
            line.balance_invoiced = line.product_qty - line.qty_invoiced
            line.outstanding_received = line.balance_received != 0
            line.outstanding_invoiced = line.balance_invoiced != 0
    
#     @api.depends('product_qty', 'qty_received')
#     def _balanced_received(self):
#         for line in self:
#             balance = 0
#             line.outstanding = False
#             balance += line.qty_received - line.product_qty
#             if balance == 0 :
#                 line.outstanding = True 
#             line.balanced = balance
    
    @api.depends('date_planned')
    def _overdue_check(self):
        today = datetime.datetime.now().date()
        for check in self:
            if check.date_planned.date() == today:
                check.overdue = True
                check.status_due = 'today'
            elif check.date_planned.date() < today:
                check.overdue = True
                check.status_due = 'overdue'
            else:
                check.overdue = False
                check.status_due = 'progress'
    #
    # @api.depends('price_unit', 'product_uom_qty', 'price_subtotal')
    # def _compute_after_disc(self):
    #     for line in self:
    #         if line.product_uom_qty:
    #             line.price_unit_disc = line.price_subtotal / line.product_uom_qty
    #             line.price_unit_dif = line.price_unit - line.price_unit_disc
    #             line.price_dif = line.price_unit_dif * line.product_uom_qty
    #
    # @api.depends('product_id', 'price_unit', 'order_id', 'product_uom', 'qty_received')
    # def _get_standard_price_unit(self):
    #     for line in self:
    #         try:
    #             line.standard_price_subtotal = line.price_unit * line.qty_received
    #         except Exception as e:
    #             print(e)
    
    # price_unit_disc = fields.Monetary(compute='_compute_after_disc', string='Price After Discount', store=False)
    # price_unit_dif = fields.Monetary(compute='_compute_after_disc', string='Price Difference', store=False)
    # price_dif = fields.Monetary(compute='_compute_after_disc', string='Total Difference', store=False)
    # discounts = fields.One2many('res.discount.purchase', 'order_line_id', ondelete='restrict')
    # discount = fields.Float(string='Discount (%)', digits='Discount', compute='_get_real_discount', store=False)
    # discount_display = fields.Text(string='Discount', compute='_discount_to_display')
    # taxes_id = fields.Many2many('account.tax', 'po_line_tax', 'po_line_id', 'po_line_tax_id', string='Taxes', related='order_id.taxes_id')
#     balanced = fields.Float(string='Balanced', compute='_balanced_received', store=True)
#     outstanding = fields.Boolean(string='Outstanding', compute='_balanced_received', store=True)
    balance_received = fields.Float(string='Balance Received', compute='_outstanding_balance', store=True)
    balance_invoiced = fields.Float(string='Balance Invoiced', compute='_outstanding_balance', store=True)
    outstanding_received = fields.Boolean(string='Outstanding Received', compute='_outstanding_balance', store=True)
    outstanding_invoiced = fields.Boolean(string='Outstanding Invoiced', compute='_outstanding_balance', store=True)
    overdue = fields.Boolean(string='Overdue', compute='_overdue_check', store=False)
    status_due = fields.Selection([
        ('progress', 'Progress'),
        ('today', 'Today'),
        ('overdue', 'Overdue'),
    ], string='Status Due', compute='_overdue_check', store=False)
    user_id = fields.Many2one('res.users', string='Purchase Representative', related='order_id.user_id', store=True)
    standard_price_subtotal = fields.Float(
        'Cost Subtotal', compute='_get_standard_price_unit',
        digits='Product Price',
        groups="base.group_user")
#     price_subtotal_before = fields.Monetary(compute='_compute_amount2', string='Subtotal')


class ReplenishRequest(models.Model):
    _inherit = 'replenish.request'
    _description = 'Purchase Request'
    
    product_note_ids = fields.One2many('replenish.request.note', 'replenish_request_id', track_visibility='onchange')


    def approve(self):
        for record in self:
            if record.state == 'draft':
                if record.request_department_id:
                    if record.request_department_id.manager_id:
                        if record.request_department_id.manager_id.user_id:
                            if record.request_department_id.manager_id.user_id.id == self.env.user.id:
                                if record.product_replenish_ids or record.product_note_ids:
                                    for product in record.product_note_ids:
                                        try:
                                            product.confirm()
                                        except Exception as e:
                                            print(e)
                                    for product in record.product_replenish_ids:
                                        try:
                                            product.approve()
                                        except Exception as e:
                                            print(e)
                                    record.write({
                                        'state':'approve',
                                        'approve_uid':self.env.user.id,
                                    })
                                else:
                                    raise UserError("Request don't have any line to approve")
                            else:
                                raise UserError('You aren\'t manager of this department.')
                        else:
                            raise UserError('Manager of this Department doesn\'t related to any user.')
                    else:
                        raise UserError('This Department doesn\'t have Manager.')
                else:
                    raise UserError('Department is empty.')
#                 managers = self.env.user.groups_id.search([('name', 'ilike', 'manager')])
#                 if managers:
#                     if record.product_replenish_ids or record.product_note_ids:
#                         for product in record.product_note_ids:
#                             try:
#                                 product.confirm()
#                             except Exception as e:
#                                 print(e)
#                         for product in record.product_replenish_ids:
#                             try:
#                                 product.approve()
#                             except Exception as e:
#                                 print(e)
#                         record.write({
#                             'state':'approve',
#                             'approve_uid':self.env.user.id,
#                         })
#                     else:
#                         raise UserError("Request don't have any line to approve")
#                 else:
#                     raise UserError('Request can only approved by Manager')
        return True
    
    
    def launch_replenishment(self):
        for record in self:
            if record.state == 'approve':
                for product in record.product_note_ids:
                    try:
                        product.confirm()
                    except Exception as e:
                        print(e)
                for product in record.product_replenish_ids:
                    if product.state == 'approve':
                        try:
                            context = {'product_id': product.product_id,
                                       'purchase_request_id': record.id}
                            product.with_context(context).launch_replenishment()
                            record.write({
                                'confirm_uid':self.env.user.id,
                            })
                        except Exception as e:
                            if 'Please define a vendor for this product' in str(e):
                                return {
                                    'name': 'Purchase Request Vendor Fill',
                                    'type': 'ir.actions.act_window',
                                    'target': 'new',
                                    'view_mode': 'form',
                                    'view_id': self.env.ref('purchase_rmdoo.view_replenish_request_vendorfill_form').id,
                                    'src_model': 'replenish.request',
                                    'res_model': 'replenish.request.vendorfill',
                                    'context': {
                                        'default_product_replenish_request_id': product.id,
                                        # 'default_partner_id': self.partner_id.id,
                                        # 'default_price_unit': self.date_planned,
                                    },
                                }
                            else:
                                raise e
        return True
    
    
    def cancel(self):
        for line in self:
            for product in line.product_note_ids:
                product.cancel()
        return super(ReplenishRequest, self).cancel()
    
    
    def reopen(self):
        for line in self:
            for product in line.product_note_ids:
                product.write({'state':'draft'})
        return super(ReplenishRequest, self).reopen()

    def add_product(self):
        if self.ensure_one():
            return {
                'name': 'Add Product',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'view_mode': 'form',
                'src_model': 'replenish.request',
                'res_model': 'replenish.request.product',
                'context': {
                    'create': False,
                    'edit': False,
                    'delete': False,
                    'default_replenish_request_id': self.id,
                    'default_is_ga': self.is_ga,
                    'default_currency_id': self.currency_id.id,
                },
            }
        else:
            return False

    
class ProductReplenishRequest(models.Model):
    _inherit = 'product.replenish.request'
    
    @api.depends('product_id')
    def _compute_actual_qty(self):
        pol_obj = self.env['purchase.order.line'].sudo()
        for record in self:
            pqty = rqty = 0.0
            pols = pol_obj.search([
                ('product_id', '=', record.product_id.id),
                ('order_id.state', 'in', ['purchase', 'done'])
            ])
            for pol in pols:
                if record.id in pol.order_id.product_replenish_request_ids.ids:
                    pqty += pol.product_uom_qty
                    rqty += pol.qty_received
            record.qty_purchase = pqty
            record.qty_received = rqty
    
    qty_purchase = fields.Float('Purchased Quantity', compute='_compute_actual_qty', digits='Product Unit of Measure')
    qty_received = fields.Float('Received Quantity', compute='_compute_actual_qty', digits='Product Unit of Measure')


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super(StockRule, self)._make_po_get_domain(company_id, values, partner)

        pr_combine = True if self.env['ir.config_parameter'].sudo().get_param(
            'purchase_rmdoo.default_pr_combine') == 'True' else False

        if "product_id" in self.env.context and "purchase_request_id" in self.env.context:
            product = self.env.context["product_id"]

            if not product.is_ga and pr_combine == False:
                gpo = self.group_propagation_option
                group = (gpo == 'fixed' and self.group_id) or \
                        (gpo == 'propagate' and 'group_id' in values and values['group_id']) or False

                domain = (
                    ('replenish_request_ids', 'in', self.env.context['purchase_request_id']),
                    ('partner_id', '=', partner.id),
                    ('state', '=', 'draft'),
                    ('picking_type_id', '=', self.picking_type_id.id),
                    ('company_id', '=', company_id.id),
                )

                if group:
                    domain += (('group_id', '=', group.id),)
        return domain

class ReplenishRequestNote(models.Model):
    _name = 'replenish.request.note'
    _description = 'Purchase Request Note'
    
    replenish_request_id = fields.Many2one('replenish.request', string='Replenish Request', required=True)
    name = fields.Char('Product', required=True, readonly=True, states={'draft':[('readonly', False)]})
    product_id = fields.Many2one(
        'product.product',
        string='Substitute Product',
        readonly=True,
        states={'approve':[('readonly', False)]},
        domain=lambda self:[('type', '=', 'product')]
    )
    qty = fields.Float('Request Quantity', default=1, required=True, readonly=True, states={'draft':[('readonly', False)]})
    uom_id = fields.Many2one('uom.uom', string='UoM', required=True, readonly=True, states={'draft':[('readonly', False)]})
    uom_category_id = fields.Many2one('uom.category', string='UoM Category', related='uom_id.category_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Canceled'),
        ('approve', 'Approved'),
        ('confirm', 'Requested'),
        ('done', 'Done')
    ], string='Status', required=True, copy=False, default='draft', track_visibility='onchange')
    
    
    def cancel(self):
        for record in self:
            if record.state not in ['confirm', 'done']:
                record.write({'state':'cancel'})
            else:
                raise UserError('Can\'t cancel confirmed/done line.')
        return True
    
    
    def confirm(self):
        rep_obj = self.env['product.replenish.request']
        for record in self:
            if record.state == 'draft':
                record.write({'state':'approve'})
            elif record.state == 'approve':
                if record.product_id:
                    rep_obj.sudo().with_context(
                        default_product_id=record.product_id.id
                    ).create({
                        'state':'approve',
                        'quantity':record.uom_id._compute_quantity(record.qty, record.product_id.uom_id),
                        'replenish_request_id':record.replenish_request_id.id,
                        'date_ordered':record.replenish_request_id.date_ordered,
                        'date_planned':record.replenish_request_id.date_planned,
                        'warehouse_id':record.replenish_request_id.warehouse_id.id,
                        'request_department_id':record.replenish_request_id.request_department_id.id,
                    })
                    record.write({'state':'confirm'})
                else:
                    raise UserError('%s doesn\'t have substitute.' % (record.name))
            else:
                raise UserError('Can\'t approve/confirm line.')
        return True


class ReplenishRequestProduct(models.TransientModel):
    _inherit = 'replenish.request.product'
    _description = 'Purchase Request Product'

    price_estimation = fields.Float(string="Price Estimation")
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency",
                                  compute='compute_currency_id')

    def compute_currency_id(self):
        self.currency_id = self.replenish_request_id.currency_id.id

    def add_product(self):
        if self.ensure_one():
            rep_obj = self.env['product.replenish.request']
            return rep_obj.with_context(
                default_product_id=self.product_id.id
            ).create({
                'quantity': self.quantity,
                'replenish_request_id': self.replenish_request_id.id,
                'date_ordered': self.replenish_request_id.date_ordered,
                'date_planned': self.replenish_request_id.date_planned,
                'warehouse_id': self.replenish_request_id.warehouse_id.id,
                'request_department_id': self.replenish_request_id.request_department_id.id,
                'price_estimation': self.price_estimation,
            })
        else:
            return False


class TotalPurchaseByVendorInquiry(models.TransientModel):
    _name = 'vendor.purchase.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Total Purchase Order By Vendor'
    
#     def _get_partner_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['partner_id'], ['partner_id'])
#         return [line['partner_id'][0] for line in lines]
#     
#     def _get_partner_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_partner_ids_default())
    
    @api.depends('date_from', 'date_to', 'create_uids', 'write_uids', 'partner_ids', 'state')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                '&',
                ('state', '=', line.state) if line.state else ('id', '!=', False),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('partner_id', 'in', [partner_id.id for partner_id in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
                '|',
                '&',
                ('create_date', '>=', line.date_from),
                ('create_date', '<=', line.date_to),
                '&',
                ('date_order', '>=', line.date_from),
                ('date_order', '<=', line.date_to),
            ])
            
    @api.depends('lines')
    def _get_pivot(self):
        super(TotalPurchaseByVendorInquiry, self)._get_pivot(
            renderer='Area Chart',
            rows=['Vendor'],
            cols=['Order Date'],
#             aggregator='Sum',
#             vals=['Total']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('purchase.order')
    
    partner_ids = fields.Many2many('res.partner', string='Vendor', domain=lambda self:self._get_domain('partner_id'))
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status')
    
    
    def pick_print(self):
        return {
            'type': 'ir.actions.report',
            'name': 'Total Purchase by Vendors',
#             'model': self._name,
            'report_type': 'qweb-pdf',
#             'paperformat_id': self.env.ref('base_rmdoo.paperformat_rmdoo_a4_landscape'),
            'report_name' : 'purchase_rmdoo.report_totalbyvendor',
        }


class PurchaseOutstandingInquiry(models.TransientModel):
    _name = 'purchase.outstanding.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Purchase Orders Outstanding'
    
    # custom method
    
#     def _get_product_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['product_id'], ['product_id'])
#         return [line['product_id'][0] for line in lines]
#     
#     def _get_product_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_product_ids_default())
#     
#     def _get_partner_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['partner_id'], ['partner_id'])
#         return [line['partner_id'][0] for line in lines]
#     
#     def _get_partner_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_partner_ids_default())
#     
#     def _get_po_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['order_id'], ['order_id'])
#         return [line['order_id'][0] for line in lines]
#     
#     def _get_po_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_po_ids_default())
    
#     def _get_confirm_uids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False), ('confirm_uid', '!=', False)], ['confirm_uid'], ['confirm_uid'])
#         return [line['confirm_uid'][0] for line in lines]
#     
#     def _get_confirm_uids_domain(self):
#         return "[('id','in',%s)]" % (self._get_confirm_uids_default())
    
    # custom method (compute)
    @api.depends('date_from', 'date_to', 'partner_ids', 'purchase_ids', 'product_ids', 'is_overdue')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                ('outstanding_received', '=', True),
                ('state', 'in', ['purchase']),
                ('date_planned', '>=', line.date_from),
                ('date_planned', '<=', line.date_to),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [product_id.id for product_id in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('order_id', 'in', [order_id.id for order_id in line.purchase_ids]) if line.purchase_ids else ('id', '!=', False),
                ('partner_id', 'in', [partner_id.id for partner_id in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
                ('qty_received', '>=', 1.0),
#                 ('overdue', 'in', line.is_overdue)
#                 ('confirm_uid', 'in', [user.id for user in line.confirm_uids]) if line.confirm_uids else ('id', '!=', False),
#                 ('state', '=', self.state) if self.state else ('id', '!=', False),
            ])
            
    @api.depends('lines')
    def _get_pivot(self):
        super(PurchaseOutstandingInquiry, self)._get_pivot(
            renderer='Table',
            rows=['Partner', 'Product', 'Product Unit of Measure', 'Quantity', 'Received Qty'],
            cols=[''],
            visible_attributes=[
                'Partner', 'Product', 'Product Unit of Measure', 'Balance Received',
                'Quantity', 'Received Qty', 'Order Date', 'Unit Price'
            ],
            aggregator='Sum',
            vals=['Balance Received']
        )

    # overwrite exiting code
#     date_from = fields.Date('Date From', default=lambda self:self._get_daterange(daterange='monthly')[0], required=True)
    date_from = fields.Date('Date From', default=lambda self:self._get_daterange(daterange='yearly')[0], required=True)
     
    # extend fields from inherited model
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('purchase.order.line')
#     lines = fields.Many2many('purchase.order')
    
    # custom field
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    partner_ids = fields.Many2many('res.partner', string='Vendor', domain=lambda self:self._get_domain('partner_id'))
    purchase_ids = fields.Many2many('purchase.order', string='Purchase', domain=lambda self:self._get_domain('order_id'))
    is_overdue = fields.Boolean(string='Overdue only')
#     state = fields.Selection([
#         ('purchase', 'Purchase Order'),
#         ('done', 'Locked'),
#     ], string='Status')
#     status_due = fields.Selection([
#         (1, 'Progress'),
#         (2, 'OverDue'),
#     ], string='Status Due')
#     confirm_uids = fields.Many2many('res.users', '%s_confirm_uids_rel' % (_name.replace('.', '_')), string='Confirmed By', domain=_get_confirm_uids_domain, default=_get_confirm_uids_default)

#     custom inherit method
    
    def list_view(self):
        res = super(PurchaseOutstandingInquiry, self).list_view()
        if res:
            res['name'] = 'Data Outstanding'
            res['view_mode'] = 'tree'
            res['view_id'] = self.env.ref('purchase_rmdoo.view_tree_list_detail_outstanding_inquiry').id
            res['target'] = 'current'
#             dp = self.env.ref('product.decimal_discount').id 
        return res
    
    
    def pick_print(self):
        return {
            'type': 'ir.actions.report',
            'name': 'Purchase Orders Outstanding Inquiries',
#             'model': self._name,
            'report_type': 'qweb-pdf',
#             'paperformat_id': self.env.ref('base_rmdoo.paperformat_rmdoo_a4_landscape'),
            'report_name' : 'purchase_rmdoo.report_purchase_outstanding',
        }
    
#     
#     def pick_print(self):
#         if self.ensure_one():
#             return {
#                 'name': 'Print Outstanding',
#                 'type': 'ir.actions.act_window',
#                 'target': 'new',
#                 'view_id' : self.env.ref('purchase_rmdoo.view_form_print_detail_outstanding_inquiry').id,
#                 'view_mode': 'form',
#                 'res_model': 'purchase.outstanding.inquiry.wizard',
#                 'domain': "[('lines_print','in',%s)]" % ([lines.id for lines in self.lines]),
#             }
#         else:
#             return False

# class PurchaseOutstandingInquiryPrint(models.TransientModel):
#     _name = "purchase.outstanding.inquiry.wizard"
# #     _inherit = "purchase.outstanding.inquiry"
#     _description = "Print Outstanding Inquiry"
#     
#     paper = fields.Many2one('report.paperformat', string="Select Paper")
#     select_print = fields.Selection([
#             ('list', 'Detail'),
#             ('vendor', 'Detail by Vendor'),
# #             ('graph', 'Graph'),
# #             ('pivot', 'Pivot')
#         ], string='Select Data')
#     lines_print = fields.Many2many('purchase.order.line')
# #     line_html = fields.Many2many()
# #     line_pivot = fields.Many2many()
#     
# #     def list_view(self):
# #         res = super(PurchaseOutstandingInquiry, self).list_view()
# #         if res:
# #             res['name'] = 'Data Outstanding'
# #             res['view_mode'] = 'tree'
# #             res['view_id'] = self.env.ref('purchase_rmdoo.view_tree_list_detail_outstanding_inquiry').id
# #             res['target'] = 'current' 
# #         return res
#     
#     
#     def do_print(self):
#         report_obj = self.env[self._name].search([]).ids
#         data = {
#                 'ids': report_obj,
#                 'model' : self._name,
#                 'form' : report_obj,
#             }
#         return {
#             'type' : 'ir.actions.report.xml',
#             'report_name':'purchase_rmdoo.action_report_purchase_outstanding_inquiry',
#             }
# #         return self.env.ref('purchase_rmdoo.report_purchase_outstanding').report_action(self, data=data)
#     
# #     Code Default
# #     
# #     def do_print(self):
# #         res = super()
# #         return {
# #             'type': 'ir.actions.report',
# #             'model': 'purchase.outstanding.inquiry',
# #         }
    

class ReplenishRequestInquiry(models.TransientModel):
    _name = 'replenish.request.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Purchase Request Inquiries'
    
    # custom method
    def _get_replenish_request_ids_default(self):
        lines_obj = self.env[self.lines._name]
        lines = lines_obj.read_group([('id', '!=', False), ('replenish_request_id', '!=', False)], ['replenish_request_id'], ['replenish_request_id'])
        return [line['replenish_request_id'][0] for line in lines]
    
    def _get_replenish_request_ids_domain(self):
        return "[('id','in',%s)]" % (self._get_replenish_request_ids_default())    
    
#     def _get_product_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['product_id'], ['product_id'])
#         return [line['product_id'][0] for line in lines]
#     
#     def _get_product_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_product_ids_default())
#     
#     def _get_warehouse_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['warehouse_id'], ['warehouse_id'])
#         return [line['warehouse_id'][0] for line in lines]
#     
#     def _get_warehouse_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_warehouse_ids_default())
    
    def _get_confirm_uids_default(self):
        lines_obj = self.env[self.lines._name]
        lines = lines_obj.read_group([('id', '!=', False), ('confirm_uid', '!=', False)], ['confirm_uid'], ['confirm_uid'])
        return [line['confirm_uid'][0] for line in lines]
    
    def _get_confirm_uids_domain(self):
        return "[('id','in',%s)]" % (self._get_confirm_uids_default())
            
    # extend exisiting method (compute)
    @api.depends('date_from', 'date_to', 'create_uids', 'write_uids', 'product_ids', 'warehouse_ids', 'confirm_uids', 'state', 'replenish_request_ids')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                '&',
                ('state', '=', line.state) if line.state else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('confirm_uid', 'in', [user.id for user in line.confirm_uids]) if line.confirm_uids else ('id', '!=', False),
                ('product_id', 'in', [product_id.id for product_id in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('warehouse_id', 'in', [warehouse_id.id for warehouse_id in line.warehouse_ids]) if line.warehouse_ids else ('id', '!=', False),
                ('replenish_request_id', 'in', [replenish_request_id.id for replenish_request_id in line.replenish_request_ids]) if line.replenish_request_ids else ('id', '!=', False),
                '|',
                '&',
                ('date_planned', '>=', line.date_from),
                ('date_planned', '<=', line.date_to),
                '&',
                ('create_date', '>=', line.date_from),
                ('create_date', '<=', line.date_to),
                '&',
                ('date_ordered', '>=', line.date_from),
                ('date_ordered', '<=', line.date_to),
            ])
            headers = []
            for line2 in line.lines:
                if line2.replenish_request_id:
                    headers.append(line2.replenish_request_id.id)
            line.headers = list(set(headers))
            
    @api.depends('lines')
    def _get_html(self):
        line_obj = self.env['product.replenish.request']
        for line in self:
            active_ids = [line2.id for line2 in line.lines]
            product_ids = line_obj.read_group(
                [('id', 'in', active_ids)],
                ['product_id', 'product_total:sum(quantity)'],
                ['product_id']
            )
            status = line_obj.read_group(
                [('id', 'in', active_ids)],
                ['state', 'state_total:sum(quantity)'],
                ['state']
            )
            html = """
            <script>
                var data = [{
                    values: %s,
                    labels: %s,
                    type: 'pie'
                }];
                
                Plotly.newPlot('plotly-container', data, {}, {responsive: true});
            </script>
            <div id="plotly-container" class="plotly-container"/>
            """ % (
                [product_id['product_total'] for product_id in product_ids],
                [str(product_id['product_id'][1]) for product_id in product_ids]
            )
            line.html = html
            html2 = """
            <script>
                var data = [{
                    values: %s,
                    labels: %s,
                    type: 'pie'
                }];
                
                Plotly.newPlot('plotly-container2', data, {}, {responsive: true});
            </script>
            <div id="plotly-container2" class="plotly-container"/>
            """ % (
                [state['state_total'] for state in status],
                [dict(line_obj._fields.get('state')._description_selection(self.env)).get(state['state']) or state['state'] for state in status]
            )
            line.html2 = html2
            
    @api.depends('lines')
    def _get_pivot(self):
        super(ReplenishRequestInquiry, self)._get_pivot(
            renderer='Heatmap',
            rows=['product_tmpl_id', 'product_id'],
            cols=['date_ordered'],
            aggregator='Sum',
            vals=['product_uom_qty']
        )
    
    # extend fields from inherited model
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('product.replenish.request')
    
    # custom field
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))  # , default=_get_product_ids_default)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse', domain=lambda self:self._get_domain('warehouse_id'))  # , default=_get_warehouse_ids_default)
    confirm_uids = fields.Many2many('res.users', '%s_confirm_uids_rel' % (_name.replace('.', '_')), string='Confirmed By', domain=_get_confirm_uids_domain)  # , default=_get_confirm_uids_default)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Canceled'),
        ('approve', 'Approved'),
        ('part_confirm', 'Partially Requested'),
        ('confirm', 'Requested'),
#         ('part_done', 'Partially Done'),
#         ('done', 'Done'),
    ], string='Status')
    headers = fields.Many2many('replenish.request', compute='_get_lines')
    replenish_request_ids = fields.Many2many('replenish.request', string='Purchase Request', domain=_get_replenish_request_ids_domain)
    html2 = fields.Html('HTML', sanitize=False, compute='_get_html')
    
    # extend method from inherited model
#     
#     def list_view(self):
#         ret = super(ReplenishRequestInquiry, self).list_view()
#         if ret:
#             ret['context']['group_by'] = ['warehouse_id', 'product_id']
#         return ret

    # custom method
    
    def pick_print(self):
        return {
            'type': 'ir.actions.report',
            'name': 'Replenish Request Inquiry',
            'report_type': 'qweb-pdf',
            'report_name' : 'purchase_rmdoo.report_purchase_replenish_request',
        }
    
    
    def list_header_view(self):
        ret = super(ReplenishRequestInquiry, self).list_view()
        if ret:
            ret['res_model'] = self.headers._name
            ret['domain'] = "[('id','in',%s)]" % ([header.id for header in self.headers])
        return ret

    
class PurchaseRequisitionInquiry(models.TransientModel):
    _name = 'purchase.requisition.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Purchase Agreement Inquiries'
    
    # custom method
#     def _get_product_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['product_id'], ['product_id'])
#         return [line['product_id'][0] for line in lines]
#     
#     def _get_product_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_product_ids_default())
#     
#     def _get_requisition_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['requisition_id'], ['requisition_id'])
#         return [line['requisition_id'][0] for line in lines]
#      
#     def _get_requisition_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_requisition_ids_default())
    
    def _get_agreement_type_ids_default(self):
        lines_obj = self.env[self.lines.requisition_id._name]
        lines = lines_obj.read_group([('id', '!=', False)], ['type_id'], ['type_id'])
        return [line['type_id'][0] for line in lines]
     
    def _get_agreement_type_ids_domain(self):
        return "[('id','in',%s)]" % (self._get_agreement_type_ids_default())
    
    # extend exisiting method (compute)
    @api.depends('date_from', 'date_to', 'create_uids', 'write_uids', 'state', 'product_ids', 'agreement_type_ids', 'requisition_ids')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                '&',
                ('requisition_id', 'in', [requisition_id.id for requisition_id in line.requisition_ids]) if line.requisition_ids else ('id', '!=', False),
                ('requisition_id.state', '=', line.state) if line.state else ('id', '!=', False),
                ('requisition_id.type_id', 'in', [
                    agreement_type_id.id for agreement_type_id in line.agreement_type_ids
                ]) if line.agreement_type_ids else ('id', '!=', False),
                ('product_id', 'in', [user.id for user in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                '|',
                '&',
                ('create_date', '>=', line.date_from),
                ('create_date', '<=', line.date_to),
                '&',
                ('schedule_date', '>=', line.date_from),
                ('schedule_date', '<=', line.date_to),
            ])
            line.headers = [line2.requisition_id.id for line2 in line.lines]
            
    @api.depends('lines')
    def _get_pivot(self):
        super(PurchaseRequisitionInquiry, self)._get_pivot(
            rows=['Product', 'Quantity', 'Product Unit of Measure'],
            cols=['Purchase Agreement'],
            aggregator='Average',
            vals=['Unit Price']
        )
    
    # extend fields from inherited model
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('purchase.requisition.line')
    
    date_from = fields.Date('Date From', default=lambda self:self._get_daterange(daterange='yearly')[0], required=True)
    date_to = fields.Date('Date To', default=lambda self:self._get_daterange(daterange='yearly')[1], required=True)
    
    # custom field
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'Ongoing'),
        ('in_progress', 'Confirmed'),
        ('open', 'Bid Selection'),
        ('done', 'Closed'),
        ('cancel', 'Cancelled')
    ], 'Status')
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))  # , default=_get_product_ids_default)
    agreement_type_ids = fields.Many2many('purchase.requisition.type', string='Agreement Type', domain=_get_agreement_type_ids_domain)  # , default=_get_agreement_type_ids_default)
    requisition_ids = fields.Many2many('purchase.requisition', string='Purchase Agreement', domain=lambda self:self._get_domain('requisition_id'))  # , default=_get_requisition_ids_default)
    headers = fields.Many2many('purchase.requisition', compute='_get_lines')
    
    # extend method from inherited model
#     
#     def list_view(self):
#         ret = super(PurchaseRequisitionInquiry, self).list_view()
#         if ret:
#             ret['context']['group_by'] = ['requisition_id']
#         return ret
    
    # custom method
    
    def pick_print(self):
        return {
            'type': 'ir.actions.report',
            'name': 'Purchase Agreement Inquiry',
            'report_type': 'qweb-pdf',
            'report_name' : 'purchase_rmdoo.report_purchase_agreement',
        }
    
    
    def list_header_view(self):
        ret = super(PurchaseRequisitionInquiry, self).list_view()
        if ret:
            ret['res_model'] = self.headers._name
            ret['domain'] = "[('id','in',%s)]" % ([header.id for header in self.headers])
        return ret

    
class PriceHistoryInquiry(models.TransientModel):
    _name = 'price.history.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Price History by P/O'
    
    def _get_purchase_ids_default(self):
        try:
            lines_obj = self.env[self.lines._name]
            lines = lines_obj.read_group([('move_ids', '!=', False), ('state', 'in', ['purchase', 'done']), ('id', '!=', False)], ['order_id'], ['order_id'])
            return [line['order_id'][0] for line in lines]
        except:
            return []
    
    def _get_purchase_ids_domain(self):
        return "[('id','in',%s)]" % (self._get_purchase_ids_default())
    
    def _get_product_ids_default(self):
        try:
            lines_obj = self.env[self.lines._name]
            lines = lines_obj.read_group([('move_ids', '!=', False), ('state', 'in', ['purchase', 'done']), ('id', '!=', False)], ['product_id'], ['product_id'])
            return [line['product_id'][0] for line in lines]
        except:
            return []
    
    def _get_product_ids_domain(self):
        return "[('id','in',%s)]" % (self._get_product_ids_default())
    
    def _get_partner_ids_default(self):
        try:
            lines_obj = self.env[self.lines._name]
            lines = lines_obj.read_group([('move_ids', '!=', False), ('state', 'in', ['purchase', 'done']), ('id', '!=', False)], ['partner_id'], ['partner_id'])
            return [line['partner_id'][0] for line in lines]
        except:
            return []
    
    def _get_partner_ids_domain(self):
        return "[('id','in',%s)]" % (self._get_partner_ids_default())
    
    def _get_user_ids_default(self):
        try:
            lines_obj = self.env[self.lines._name]
            lines = lines_obj.read_group([('move_ids', '!=', False), ('state', 'in', ['purchase', 'done']), ('id', '!=', False)], ['user_id'], ['user_id'])
            return [line['user_id'][0] for line in lines]
        except:
            return []
    
    def _get_user_ids_domain(self):
        return "[('id','in',%s)]" % (self._get_user_ids_default())
    
    @api.depends('date_from', 'date_to', 'create_uids', 'write_uids', 'product_ids', 'purchase_ids', 'partner_ids', 'user_ids')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                '&',
                ('move_ids', '!=', False),
                ('order_id.state', 'in', ['purchase', 'done']),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [user.id for user in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('order_id', 'in', [purchase_id.id for purchase_id in line.purchase_ids]) if line.purchase_ids else ('id', '!=', False),
                ('partner_id', 'in', [partner_id.id for partner_id in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
                ('user_id', 'in', [user_id.id for user_id in line.user_ids]) if line.user_ids else ('id', '!=', False),
                '|',
                '&',
                ('create_date', '>=', line.date_from),
                ('create_date', '<=', line.date_to),
                '&',
                ('date_order', '>=', line.date_from),
                ('date_order', '<=', line.date_to),
            ])
            # line.headers = [line2.order_id.id for line2 in line.lines]
            
    @api.depends('lines')
    def _get_html(self):
        line_obj = self.env['purchase.order.line']
        for line in self:
            active_ids = [line2.id for line2 in line.lines]
            product_ids = line_obj.read_group(
                [('id', 'in', active_ids)],
                ['product_id'],
                ['product_id']
            )
            var_data = ''
            for product_id in product_ids:
                prod_id, prod_name = product_id['product_id']
                plines = line_obj.search([('id', 'in', active_ids), ('product_id', '=', prod_id)])
                var_data += """
                    var data%s = {
                        x: %s,
                        y: %s,
                        name: '%s',
                        type: 'scatter',
                        fill: 'tozeroy',
                        connectgaps: true,
                        mode: 'lines+markers'
                    };
                """ % (
                    prod_id,
                    [pline.date_order.strftime(DEFAULT_SERVER_DATETIME_FORMAT) for pline in plines],
                    [pline.price_unit for pline in plines],
                    prod_name
                )
            var_data += """
                var data = [%s];
            """ % (','.join(['data%s' % (product_id['product_id'][0]) for product_id in product_ids]))
            html = """
            <script>
                %s
                
                Plotly.newPlot('plotly-container', data, {}, {responsive: true});
            </script>
            <div id="plotly-container" class="plotly-container"/>
            """ % (var_data)
            line.html = html
            
    @api.depends('lines')
    def _get_pivot(self):
        if self.env.context.get('default_name') == 'P/O Discount Accumulation':
            super(PriceHistoryInquiry, self)._get_pivot(
                rows=['Purchase Representative'],
                cols=['Order Date'],
                aggregator='Sum',
                vals=['Total Difference']
            )
        else:
            super(PriceHistoryInquiry, self)._get_pivot(
                rows=['Product'],
                cols=['Order Date'],
                aggregator='Average',
                vals=['Unit Price']
            )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('purchase.order.line')
    
    product_ids = fields.Many2many('product.product', string='Product', domain=_get_product_ids_domain)  # , default=_get_product_ids_default)
    purchase_ids = fields.Many2many('purchase.order', string='Purchase Order', domain=_get_purchase_ids_domain)
    partner_ids = fields.Many2many('res.partner', string='Vendor', domain=_get_partner_ids_domain)
    user_ids = fields.Many2many('res.users', string='Purchase Repr', domain=_get_user_ids_domain)
    
    # custom method
    
    def pick_print(self):
        return {
            'type': 'ir.actions.report',
            'name': 'Purchase History by P/O',
            'report_type': 'qweb-pdf',
            'report_name' : 'purchase_rmdoo.report_purchase_history',
        }


class PurchaseAccByItem(models.TransientModel):
    _name = 'purchase.acc.item'
    _inherit = 'inquiry.report'
    _description = 'Purchase Accumulated by Product'
    
#     def _get_product_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['product_id'], ['product_id'])
#         return [line['product_id'][0] for line in lines]
#     
#     def _get_product_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_product_ids_default())
#     
#     def _get_partner_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['partner_id'], ['partner_id'])
#         return [line['partner_id'][0] for line in lines]
#     
#     def _get_partner_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_partner_ids_default())
    
    @api.depends('date_from', 'date_to', 'create_uids', 'write_uids', 'product_ids', 'partner_ids', 'state')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                '&',
                ('state', '=', line.state) if line.state else ('id', '!=', False),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [user.id for user in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('partner_id', 'in', [partner_id.id for partner_id in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
                '|',
                '&',
                ('create_date', '>=', line.date_from),
                ('create_date', '<=', line.date_to),
                '&',
                ('date_order', '>=', line.date_from),
                ('date_order', '<=', line.date_to),
            ])
            
    @api.depends('lines')
    def _get_pivot(self):
        super(PurchaseAccByItem, self)._get_pivot(
            renderer='Heatmap',
            rows=['Product (Category)', 'Product', 'Quantity'],
            cols=[],
            visible_attributes=[
                'Partner', 'Product', 'Product Unit of Measure', 'Balance Received', 'Subtotal',
                'Quantity', 'Received Qty', 'Order Date', 'Unit Price', 'Cost Subtotal'
            ],
            aggregator='Sum',
            vals=['Subtotal']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('purchase.order.line')
    
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    partner_ids = fields.Many2many('res.partner', string='Vendor', domain=lambda self:self._get_domain('partner_id'))
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status')
    

class PurchaseAccByVendor(models.TransientModel):
    _name = 'purchase.acc.vendor'
    _inherit = 'inquiry.report'
    _description = 'Purchase Accumulated by Vendors'
    
#     def _get_product_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['product_id'], ['product_id'])
#         return [line['product_id'][0] for line in lines]
#     
#     def _get_product_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_product_ids_default())
#     
#     def _get_partner_ids_default(self):
#         lines_obj = self.env[self.lines._name]
#         lines = lines_obj.read_group([('id', '!=', False)], ['partner_id'], ['partner_id'])
#         return [line['partner_id'][0] for line in lines]
#     
#     def _get_partner_ids_domain(self):
#         return "[('id','in',%s)]" % (self._get_partner_ids_default())
    
    @api.depends('date_from', 'date_to', 'create_uids', 'write_uids', 'product_ids', 'partner_ids', 'state')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                '&',
                ('state', '=', line.state) if line.state else ('id', '!=', False),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [user.id for user in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('partner_id', 'in', [partner_id.id for partner_id in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
                '|',
                '&',
                ('create_date', '>=', line.date_from),
                ('create_date', '<=', line.date_to),
                '&',
                ('date_order', '>=', line.date_from),
                ('date_order', '<=', line.date_to),
            ])
            
    @api.depends('lines')
    def _get_pivot(self):
        super(PurchaseAccByVendor, self)._get_pivot(
            renderer='Heatmap',
            rows=['Partner'],
            cols=[],
            visible_attributes=[
                'Partner', 'Product', 'Product Unit of Measure', 'Balance Received', 'Subtotal',
                'Quantity', 'Received Qty', 'Order Date', 'Unit Price', 'Cost Subtotal'
            ],
            aggregator='Sum',
            vals=['Subtotal']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('purchase.order.line')
    
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    partner_ids = fields.Many2many('res.partner', string='Vendor', domain=lambda self:self._get_domain('partner_id'))
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status')
    
    
class InventoryPurchaseReceivedInquiry(models.TransientModel):
    _name = 'inventorypurchasereceived.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Inventory Purchase Received'
    
    @api.depends(
        'date_from',
        'date_to',
        'create_uids',
        'write_uids',
        'product_ids',
        'location_ids',
        'location_dest_ids',
        'purchase_line_ids',
        'partner_ids',
        'state'
    )
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                ('state', '=', line.state),
                ('picking_type_id.code', '=', 'incoming'),
                ('purchase_line_id', '!=', False),
                ('date', '>=', line.date_from),
                ('date', '<=', line.date_to),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [product.id for product in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('location_id', 'in', [location.id for location in line.location_ids]) if line.location_ids else ('id', '!=', False),
                ('location_dest_id', 'in', [location.id for location in line.location_dest_ids]) if line.location_dest_ids else ('id', '!=', False),
                ('purchase_line_id', 'in', [purchase_line.id for purchase_line in line.purchase_line_ids]) if line.purchase_line_ids else ('id', '!=', False),
                ('partner_id', 'in', [partner.id for partner in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
            ])
            
    @api.depends('lines', 'is_value')
    def _get_pivot(self):
        super(InventoryPurchaseReceivedInquiry, self)._get_pivot(
            rows=[
                'partner_id',
                'Product',
            ],
            cols=[
                'Destination Location'
            ] if self.is_value else [
                'Destination Location',
                'Unit of Measure'
            ],
            aggregator='Sum',
            vals=['valuation'] if self.is_value else ['product_uom_qty']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('stock.move')
    
    is_value = fields.Boolean('Valuation', default=lambda self:True)
    
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    partner_ids = fields.Many2many('res.partner', string='Vendor', domain=lambda self:self._get_domain('partner_id'))
    location_ids = fields.Many2many('stock.location', relation="location_id_inv_purchase_received_inquiry", column1="location_id", column2="inv_purchase_received_inquiry",
                                    string='Source Location', domain=lambda self:self._get_domain('location_id'))
    location_dest_ids = fields.Many2many('stock.location', relation="location_dest_id_inv_purchase_received_inquiry", column1="location_dest_id", column2="inv_purchase_received_inquiry",
                                         string='Destination Location', domain=lambda self:self._get_domain('location_dest_id'))
    purchase_line_ids = fields.Many2many('purchase.order.line', string='Purchase Order', domain=lambda self:self._get_domain('purchase_line_id'))
    state = fields.Selection([('draft', 'New'), ('cancel', 'Cancelled'), ('waiting', 'Waiting Another Move'), ('confirmed', 'Waiting Availability'), ('partially_available', 'Partially Available'), ('assigned', 'Available'), ('done', 'Done')], string='Status', default='done', required=True)


class InventoryPurchaseReturnInquiry(models.TransientModel):
    _name = 'inventorypurchasereturn.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Inventory Purchase Return'
    
    @api.depends(
        'date_from',
        'date_to',
        'create_uids',
        'write_uids',
        'product_ids',
        'location_ids',
        'location_dest_ids',
        'purchase_line_ids',
        'partner_ids',
        'state'
    )
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                ('state', '=', line.state),
                ('picking_type_id.code', '=', 'outgoing'),
                ('purchase_line_id', '!=', False),
                ('date', '>=', line.date_from),
                ('date', '<=', line.date_to),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [product.id for product in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('location_id', 'in', [location.id for location in line.location_ids]) if line.location_ids else ('id', '!=', False),
                ('location_dest_id', 'in', [location.id for location in line.location_dest_ids]) if line.location_dest_ids else ('id', '!=', False),
                ('purchase_line_id', 'in', [purchase_line.id for purchase_line in line.purchase_line_ids]) if line.purchase_line_ids else ('id', '!=', False),
                ('partner_id', 'in', [partner.id for partner in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
            ])
            
    @api.depends('lines', 'is_value')
    def _get_pivot(self):
        super(InventoryPurchaseReturnInquiry, self)._get_pivot(
            rows=[
                'Source Location',
                'Product',
            ],
            cols=[
                'partner_id'
            ] if self.is_value else [
                'partner_id',
                'Unit of Measure'
            ],
            aggregator='Sum',
            vals=['valuation'] if self.is_value else ['product_uom_qty']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('stock.move')
    
    is_value = fields.Boolean('Valuation', default=lambda self:True)
    
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    partner_ids = fields.Many2many('res.partner', string='Vendor', domain=lambda self:self._get_domain('partner_id'))
    location_ids = fields.Many2many('stock.location', relation="location_id_inv_purchase_return_inquiry", column1="location_id", column2="inv_purchase_return_inquiry",
                                    string='Source Location', domain=lambda self:self._get_domain('location_id'))
    location_dest_ids = fields.Many2many('stock.location', relation="location_id_inv_purchase_return_inquiry", column1="location_id", column2="inv_purchase_return_inquiry",
                                         string='Destination Location', domain=lambda self:self._get_domain('location_dest_id'))
    purchase_line_ids = fields.Many2many('purchase.order.line', string='Purchase Order', domain=lambda self:self._get_domain('purchase_line_id'))
    state = fields.Selection([('draft', 'New'), ('cancel', 'Cancelled'), ('waiting', 'Waiting Another Move'), ('confirmed', 'Waiting Availability'), ('partially_available', 'Partially Available'), ('assigned', 'Available'), ('done', 'Done')], string='Status', default='done', required=True)
    
    
class POvsReceiptInquiries(models.TransientModel):     
    _name = 'purchase.povsreceipt.inquiry'
    _inherit = 'inquiry.report'
    _description = 'P/O vs Receipt'
    
    @api.depends('date_from', 'date_to', 'partner_ids', 'purchase_ids', 'product_ids')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
#                 ('outstanding_received', '=', True),
                ('state', 'in', ['purchase']),
                ('date_planned', '>=', line.date_from),
                ('date_planned', '<=', line.date_to),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [product_id.id for product_id in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('order_id', 'in', [order_id.id for order_id in line.purchase_ids]) if line.purchase_ids else ('id', '!=', False),
                ('partner_id', 'in', [partner_id.id for partner_id in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
#                 ('balance_invoiced', '<=', 0.0),
#                 ('confirm_uid', 'in', [user.id for user in line.confirm_uids]) if line.confirm_uids else ('id', '!=', False),
#                 ('state', '=', self.state) if self.state else ('id', '!=', False),
            ])
    
#     Unfinished Jobs
    @api.depends('lines')
    def _get_html(self):
        for line in self:
            datax = []
            datay1 = []
            datay2 = []
            ord_obj = self.env['sale.order.line']
            ord_ids = [l.order_id.id for l in line.lines]
            products = self.env['product.product'].search([('id', 'in', False)])
#             users = self.env['res.users'].search([('id', '!=', False)])
            # datas = fc_obj.read_group([('id', 'in', fc_ids)], ['user_id'], ['user_id'])
            for product in products:
#                 if user.has_group('sales_team.group_sale_salesman'):
                ords = ord_obj.search([
                    '&',
                    ('id', 'in', ord_ids),
                    ('state', '=', 'sale'),
                    '|',
                    ('product_id', '=', product.id),
                    ('product_id', '=', False)
                ])
                
                datapr = []
                for ord in ords:
                    datapr.append(ord_line)
                if datapr:
                    datax.append(str(datapr.name))
                    datay1.append(int(float(sum(datapr.product_qty))))
                    datay2.append(int(float(sum(datapr.qty_received))))
#                     avg_data = []
#                     for ord in ords:
#                         for ord_line in ord.forecast_lines:
#                             avg_data.append(ord_line.realization)
#                     if avg_data:
#                         avg = int(round(float(sum(avg_data)) / float(len(avg_data)), 0))
#                         datax.append(str(user.name))
#                         datay1.append(avg)
#                         datay2.append(100 - avg)
            line.html = """
            <script>
                var data = [{
                    x: %s,
                    y: %s,
                    name: 'Total Received',
                    type: 'bar'
                }, {
                    x: %s,
                    y: %s,
                    name: 'Total Ordered',
                    type: 'bar'
                }];

                Plotly.newPlot('plotly-container', data, {barmode:'stack'}, {responsive:true});
            </script>
            <div id="plotly-container" class="plotly-container"/>
            """ % (
                datax,
                datay1,
                datax,
                datay2
            )
    
    @api.depends('lines')
    def _get_pivot(self):
        super(POvsReceiptInquiries, self)._get_pivot(
            renderer='Heatmap',
            rows=['Order Reference', 'Product', 'Quantity', 'Received Qty'],
            cols=[],
            visible_attributes=[
                'Partner', 'Product', 'Product Unit of Measure', 'Balance Received',
                'Balance Invoiced', 'Subtotal', 'Billed Qty', 'Order Reference',
                'Quantity', 'Received Qty', 'Order Date', 'Unit Price', 'Cost Subtotal'
            ],
            aggregator='Sum',
            vals=['Balance Received']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('purchase.order.line')
    
    # custom field
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    partner_ids = fields.Many2many('res.partner', string='Vendor', domain=lambda self:self._get_domain('partner_id'))
    purchase_ids = fields.Many2many('purchase.order', string='PO Number', domain=lambda self:self._get_domain('order_id'))

    
class ReceivedNotYetBilledInquiries(models.TransientModel):
    _name = 'receivednotbill.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Received Not Yet Billed'
    
    @api.depends('date_from', 'date_to', 'partner_ids', 'purchase_ids', 'product_ids')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
#                 ('outstanding_received', '=', True),
                ('state', 'in', ['purchase']),
                ('date_planned', '>=', line.date_from),
                ('date_planned', '<=', line.date_to),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [product_id.id for product_id in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('order_id', 'in', [order_id.id for order_id in line.purchase_ids]) if line.purchase_ids else ('id', '!=', False),
                ('partner_id', 'in', [partner_id.id for partner_id in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
                ('balance_invoiced', '<=', 0.0),
                ('qty_invoiced', '<=', line.lines.product_qty),
#                 ('confirm_uid', 'in', [user.id for user in line.confirm_uids]) if line.confirm_uids else ('id', '!=', False),
#                 ('state', '=', self.state) if self.state else ('id', '!=', False),
            ])
    
    @api.depends('lines')
    def _get_pivot(self):
        super(ReceivedNotYetBilledInquiries, self)._get_pivot(
            renderer='Heatmap',
            rows=['Order Reference', 'Product', 'Quantity', 'Received Qty', 'Billed Qty', 'Unit Price'],
            cols=[],
            visible_attributes=[
                'Partner', 'Product', 'Product Unit of Measure', 'Balance Received',
                'Balance Invoiced', 'Subtotal', 'Billed Qty', 'Order Reference',
                'Quantity', 'Received Qty', 'Order Date', 'Unit Price', 'Cost Subtotal'
            ],
            aggregator='Sum',
            vals=['Subtotal']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('purchase.order.line')
    
    # custom field
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    partner_ids = fields.Many2many('res.partner', string='Vendor', domain=lambda self:self._get_domain('partner_id'))
    purchase_ids = fields.Many2many('purchase.order', string='PO Number', domain=lambda self:self._get_domain('order_id'))
