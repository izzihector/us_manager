from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_product_accounts(self):
        res = super(ProductTemplate, self)._get_product_accounts()
        if self.env.context.get('department'):
            department = self.env['hr.department'].browse(self.env.context.get('department'))
            if department:
                income = department.account_income_consign_id if self.is_consignment else department.account_income_depart_id
                expense = department.account_expense_consign_id if self.is_consignment else department.account_expense_depart_id
                res.update({
                    'income': income or self.property_account_income_id or self.categ_id.property_account_income_categ_id,
                    'expense': expense or self.property_account_expense_id or self.categ_id.property_account_expense_categ_id
                })
        return res
