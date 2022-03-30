# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=False, ondelete='restrict',
                                    default=lambda self:self.env.user.department_id)
    purchase_type = fields.Selection(string="Purchase Type",
                                     selection=[('niaga', 'Niaga'), ('non_niaga', 'Non Niaga'), ], default="", required=False, )

    @api.onchange('purchase_type')
    def onchange_purchase_type(self):
        if self.purchase_type == 'niaga':
            self.is_ga = False
        elif self.purchase_type == 'non_niaga':
            self.is_ga = True

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
                replenish_request_is_ga = record.replenish_request_ids.sudo().mapped('is_ga')
                if True in replenish_request_is_ga:
                    record.is_ga = True
                    record.purchase_type = 'non_niaga'
                    record.department_id = record.company_id.department_ga_id.id
                else:
                    record.is_ga = False
                    record.purchase_type = 'niaga'
                    record.department_id = record.replenish_request_ids[0].request_department_id.id

    def button_confirm(self):
        for order in self:
            if order.partner_id.denied_purchase:
                raise UserError('Purchase with vendor %s is denied, please select another vendor.' % order.partner_id.name)
            if order.state not in ['draft', 'sent', 'to approve']:
                continue
            order._add_supplier_to_product()
            approve = False
            if order.is_ga == False:
                if self.confirm_uid:
                    if order.user_has_groups('purchase.group_purchase_manager'):
                        self.confirm2_uid = self.env.user.id
                        approve = True
                else:
                    self.confirm_uid = self.env.user.id
            else:
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

    def _add_supplier_to_product(self):
        return super(PurchaseOrder, self.with_context({'department_id': self.department_id.id}))._add_supplier_to_product()

    @api.model
    def create(self, vals):
        if not vals.get('department_id'):
            picking_type = self.env['stock.picking.type'].browse(vals['picking_type_id'])
            vals['department_id'] = picking_type.warehouse_id.department_id.id
        return super(PurchaseOrder, self).create(vals)

    def action_view_invoice(self):
        res = super(PurchaseOrder, self).action_view_invoice()
        if res.get('context'):
            res['context'].update({'default_department_id': self.department_id.id})
        return res

    @api.onchange('branch_id')
    def onchange_branch_department(self):
        if self.branch_id:
            self.department_id = self.branch_id.department_id.id
