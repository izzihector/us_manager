from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

class ReplenishRequest(models.Model):
    _inherit = 'replenish.request'

    name = fields.Char(copy=False)
    total_amount_estimation = fields.Float(string="Total Amount Estimation",  required=False, readonly=True,
                                           compute="_compute_total_amount_estimation")
    pengadaan_user_ids = fields.Many2many(comodel_name="res.users", relation="replenish_request_user_pengadaan_rel",
                                          column1="request_id", column2="user_id", string="Tim Pengadaan")
    lelang_user_ids = fields.Many2many(comodel_name="res.users", relation="replenish_request_user_lelang_rel",
                                       column1="request_id", column2="user_id", string="Tim Lelang")
    confirm4_uid = fields.Many2one('res.users', string='Approved By (Tim Lelang)', readonly=True, copy=False)
    confirm3_uid = fields.Many2one('res.users', string='Approved By (Tim Pengadaan)', readonly=True, copy=False)
    confirm2_uid = fields.Many2one('res.users', string='Approved By (Kepala Bidang)', readonly=True, copy=False)
    state = fields.Selection(string="Status", selection=[
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled'),
    ], default='draft', copy=False, readonly=True, tracking=True)
    approval_state = fields.Selection(string="Approval Status", selection=[
        ('approve_1', 'Need to Approve by Kepada Bidang'),
        ('approve_2', 'Need to Approve by Tim Pengadaan'),
        ('approve_3', 'Need to Approve by Tim Lelang'),
        ('Approved', 'Approved'),
    ], default='approve_1', copy=False, readonly=True, tracking=True)

    def action_submit(self):
        for rec in self:
            if rec.state == 'draft':
                if rec.create_uid != self.env.user:
                    raise UserError("Sorry you can only submit your own request.")
                rec.write({
                    'state': 'to_approve',
                    'approval_state': 'approve_1'
                })

    def action_cancel(self):
        for rec in self:
            if rec.state == 'draft':
                if rec.create_uid != self.env.user.id:
                    raise UserError("Sorry you can only cancel your own request.")
                rec.write({
                    'state': 'reject',
                })

    def check_approval_access(self):
        approval_state = self.approval_state
        user = self.env.user
        if approval_state == 'approve_1':
            if user.has_group('bs_sarinah_purchase.group_purchase_request_manager') and (self.sudo().request_department_id.manager_id.user_id == user):
                return True
            else:
                raise UserError('Sorry you are not allowed to approve/reject this request')
        elif approval_state == 'approve_2':
            if user.has_group('bs_sarinah_purchase.group_purchase_request_tim_pengadaan') and (user.id in self.pengadaan_user_ids.ids):
                return True
            else:
                raise UserError('Sorry you are not allowed to approve/reject this request')
        elif approval_state == 'approve_3':
            if user.has_group('bs_sarinah_purchase.group_purchase_request_tim_lelang') and (user.id in self.lelang_user_ids.ids):
                return True
            else:
                raise UserError('Sorry you are not allowed to approve/reject this request')

    def action_reject(self):
        for rec in self:
            rec.check_approval_access()
            rec.write({
                'state': 'reject'
            })

    def action_launch(self):
        for rec in self:
            if rec.product_replenish_ids or rec.product_note_ids:
                for product in rec.product_note_ids:
                    product.confirm()
                for product in rec.product_replenish_ids:
                    product.write({
                        'state': 'approve',
                        'approve_uid': self.env.user.id,
                    })
                    product.approve()
                rec.write({
                    'state': 'approve',
                    'approve_uid': self.env.user.id,
                })
                rec.launch_replenishment()
            else:
                raise UserError("Request don't have any line to approve")

    def action_approve(self):
        for rec in self:
            if rec.state != 'to_approve':
                raise UserError('Sorry only request with status To Approve can be proceed.')
            if not rec.request_department_id.manager_id:
                raise UserError('This Department doesn\'t have Manager.')
            rec.check_approval_access()
            if not rec.is_ga:
                rec.action_launch()
            else:
                pr_quadruple_validation_amount = rec.company_id.currency_id._convert(
                    rec.company_id.pr_quadruple_validation_amount, rec.currency_id, rec.company_id,
                    rec.date_ordered or fields.Date.today())
                pr_triple_validation_amount = rec.company_id.currency_id._convert(
                    rec.company_id.pr_triple_validation_amount, rec.currency_id, rec.company_id,
                    rec.date_ordered or fields.Date.today())
                if rec.approval_state == 'approve_1':
                    if rec.total_amount_estimation >= pr_triple_validation_amount:
                        rec.write({
                            'confirm2_uid': self.env.user.id,
                            'approval_state': 'approve_2',
                        })
                    else:
                        rec.write({
                            'confirm2_uid': self.env.user.id,
                            'confirm3_uid': self.env.user.id,
                            'confirm4_uid': self.env.user.id,
                            'approval_state': 'approve_3',
                        })
                        rec.action_launch()
                elif rec.approval_state == 'approve_2':
                    if rec.total_amount_estimation >= pr_quadruple_validation_amount:
                        rec.write({
                            'confirm3_uid': self.env.user.id,
                            'approval_state': 'approve_3',
                        })
                    else:
                        rec.write({
                            'confirm3_uid': self.env.user.id,
                            'confirm4_uid': self.env.user.id,
                            'approval_state': 'approve_3',
                        })
                        rec.action_launch()
                elif rec.approval_state == 'approve_3':
                    rec.write({
                        'confirm4_uid': self.env.user.id,
                    })
                    rec.action_launch()

    @api.depends('product_replenish_ids.amount_estimation')
    def _compute_total_amount_estimation(self):
        self.total_amount_estimation = sum(self.product_replenish_ids.mapped('amount_estimation'))

    # def multi_approve(self):
    #     for record in self:
    #         approve = False
    #         pr_quadruple_validation_amount = self.env.user.company_id.currency_id._convert(
    #             record.company_id.pr_quadruple_validation_amount, record.company_id.currency_id, record.company_id,
    #             record.date_ordered or fields.Date.today())
    #         pr_triple_validation_amount = self.env.user.company_id.currency_id._convert(
    #             record.company_id.pr_triple_validation_amount, record.company_id.currency_id, record.company_id,
    #             record.date_ordered or fields.Date.today())
    #
    #         is_manager = False
    #         is_tim_pengadaan = False
    #         is_tim_lelang = False
    #
    #         if record.user_has_groups('bs_sarinah_purchase.group_purchase_request_tim_lelang'):
    #             is_tim_lelang = True
    #         if record.user_has_groups('bs_sarinah_purchase.group_purchase_request_tim_pengadaan'):
    #             is_tim_pengadaan = True
    #         if record.user_has_groups('bs_sarinah_purchase.group_purchase_request_manager'):
    #             if not is_tim_lelang and not is_tim_pengadaan \
    #                     and not record.request_department_id.manager_id.user_id.id == self.env.user.id:
    #                 raise UserError('You aren\'t manager of this department.')
    #             is_manager = True
    #
    #         if not is_manager and not is_tim_pengadaan and not is_tim_lelang:
    #             raise UserError('You are not allowed to approve this document.')
    #
    #         if record.company_id.pr_double_validation == 'four_step':
    #             if record.total_amount_estimation >= pr_quadruple_validation_amount:
    #                 if record.confirm3_uid:
    #                     if is_tim_lelang:
    #                         record.confirm3_uid = self.env.user.id
    #                         approve = True
    #                 elif self.confirm2_uid:
    #                     if is_tim_pengadaan:
    #                         record.confirm3_uid = self.env.user.id
    #                 else:
    #                     if is_manager:
    #                         record.confirm2_uid = self.env.user.id
    #             elif record.total_amount_estimation >= pr_triple_validation_amount:
    #                 if self.confirm2_uid:
    #                     if is_tim_pengadaan:
    #                         record.confirm3_uid = self.env.user.id
    #                         approve = True
    #                 else:
    #                     if is_manager:
    #                         record.confirm2_uid = self.env.user.id
    #             else:
    #                 if is_manager:
    #                     record.confirm2_uid = self.env.user.id
    #                     approve = True
    #         elif record.company_id.pr_double_validation == 'three_step':
    #             if record.total_amount_estimation >= pr_triple_validation_amount:
    #                 if self.confirm2_uid:
    #                     if is_tim_pengadaan:
    #                         record.confirm3_uid = self.env.user.id
    #                         approve = True
    #                 else:
    #                     if is_manager:
    #                         record.confirm2_uid = self.env.user.id
    #             else:
    #                 if is_manager:
    #                     record.confirm2_uid = self.env.user.id
    #                     approve = True
    #         elif record.company_id.pr_double_validation == 'two_step':
    #             if is_manager:
    #                 record.confirm2_uid = self.env.user.id
    #                 approve = True
    #         else:
    #             approve = True
    #     return approve

    # def approve(self):
    #     for record in self:
    #         if not record.state == 'draft':
    #             raise UserError('Only document with state Draft can be proceed.')
    #         if not record.request_department_id.manager_id:
    #             raise UserError('This Department doesn\'t have Manager.')
    #         if not record.request_department_id.manager_id.user_id:
    #             raise UserError('Manager of this Department doesn\'t related to any user.')
    #
    #         if record.multi_approve():
    #             if record.product_replenish_ids or record.product_note_ids:
    #                 for product in record.product_note_ids:
    #                     product.confirm()
    #                 for product in record.product_replenish_ids:
    #                     product.approve()
    #                 record.write({
    #                     'state': 'approve',
    #                     'approve_uid': self.env.user.id,
    #                 })
    #                 record.launch_replenishment()
    #             else:
    #                 raise UserError("Request don't have any line to approve")
    #
    #     return True


class ProductReplenishRequest(models.Model):
    _inherit = 'product.replenish.request'

    def launch_replenishment(self):
        if self.ensure_one():
            uom_reference = self.product_id.uom_id
            self.write({
                'quantity': self.product_uom_id._compute_quantity(self.quantity, uom_reference),
                'confirm_uid': self.env.user.id,
            })
            try:
                values = self._prepare_run_values()
                self.env['procurement.group'].with_context(clean_context(self.env.context)).run([self.env['procurement.group'].Procurement(
                    self.product_id,
                    self.quantity,
                    uom_reference,
                    self.warehouse_id.lot_stock_id,
                    values['group_id'].name,  # Name
                    values['group_id'].name,  # Origin
                    self.env.company,
                    values  # Values
                )])
                self.state = 'confirm'
            except UserError as error:
                raise UserError(error)
        return True

    # def approve(self):
    #     for line in self:
    #
    #         if not line.state == 'draft':
    #             raise UserError('Only document with state Draft can be proceed.')
    #         if not line.request_department_id.manager_id:
    #             raise UserError('This Department doesn\'t have Manager.')
    #         if not line.request_department_id.manager_id.user_id:
    #             raise UserError('Manager of this Department doesn\'t related to any user.')
    #
    #         if line.replenish_request_id.multi_approve():
    #             line.write({
    #                 'state': 'approve',
    #                 'approve_uid': self.env.user.id,
    #             })