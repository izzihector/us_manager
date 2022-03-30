# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    account_income_depart_id = fields.Many2one('account.account', string="Income Account", company_dependent=True,
                                               domain="[('deprecated', '=', False)]",
                                               help="This account will be used when validating a customer invoice.")
    account_expense_depart_id = fields.Many2one('account.account', company_dependent=True,
                                                string="Expense Account",
                                                domain="[('deprecated', '=', False)]",
                                                help="The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation.")
    account_discount_depart_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Discount Account",
                                                 domain="[('deprecated', '=', False)]")
    account_income_consign_id = fields.Many2one('account.account', string="Income Account (Consignment)", company_dependent=True,
                                                domain="[('deprecated', '=', False)]",
                                                help="This account will be used when validating a customer invoice.")
    account_expense_consign_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Expense Account (Consignment)",
                                                 domain="[('deprecated', '=', False)]",
                                                 help="The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation.")
    account_discount_consign_id = fields.Many2one('account.account', company_dependent=True,
                                                  string="Discount Account (Consignment)",
                                                  domain="[('deprecated', '=', False)]")
    account_stock_output_consign_id = fields.Many2one('account.account', company_dependent=True,
                                                      string="Stock Output Account (Consignment)",
                                                      domain="[('deprecated', '=', False)]")

    @api.model
    def create(self, vals):
        res = super(HrDepartment, self).create(vals)
        users = self.env['res.users'].sudo().search([])
        users.sudo().compute_all_department()
        return res

    def write(self, vals):
        res = super(HrDepartment, self).write(vals)
        if vals.get('parent_id'):
            users = self.env['res.users'].sudo().search([])
            users.sudo().compute_all_department()
        return res
