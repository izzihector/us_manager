from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    warehouse_ga_id = fields.Many2one(comodel_name="stock.warehouse", string="Purchase Warehouse", required=False,
                                      related="company_id.warehouse_ga_id", readonly=False)
    partner_receivable_account_id = fields.Many2one(comodel_name="account.account", string="Default Receivable Account",
                                                    domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",)
    partner_payable_account_id = fields.Many2one(comodel_name="account.account", string="Default Payable Account",
                                                 domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        receivable_field = self.env.ref('account.field_res_partner__property_account_receivable_id')
        receivable_property = self.env['ir.property'].sudo().search([('company_id', '=', self.env.company.id),
                                                          ('name', '=', 'property_account_receivable_id'),
                                                          ('res_id', '=', False),
                                                          ('fields_id', '=', receivable_field.id)])
        if receivable_property:
            try:
                account = self.env['account.account'].sudo().browse(int(receivable_property.value_reference.split(',')[1]))
                res.update(
                    partner_receivable_account_id=account.id
                )
            except Exception:
                pass

        payable_field = self.env.ref('account.field_res_partner__property_account_payable_id')
        payable_property = self.env['ir.property'].sudo().search([('company_id', '=', self.env.company.id),
                                                          ('name', '=', 'property_account_payable_id'),
                                                          ('res_id', '=', False),
                                                          ('fields_id', '=', payable_field.id)])
        if payable_property:
            try:
                account = self.env['account.account'].sudo().browse(int(payable_property.value_reference.split(',')[1]))
                res.update(
                    partner_payable_account_id=account.id
                )
            except Exception:
                pass
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        property_obj = self.env['ir.property'].sudo()
        if self.partner_receivable_account_id:
            receivable_field = self.env.ref('account.field_res_partner__property_account_receivable_id')
            receivable_property = property_obj.search([('company_id', '=', self.env.company.id),
                                                       ('name', '=', 'property_account_receivable_id'),
                                                       ('res_id', '=', False),
                                                       ('fields_id', '=', receivable_field.id)])
            if receivable_property:
                receivable_property.sudo().write({
                    'value_reference': 'account.account,{}'.format(self.partner_receivable_account_id.id)
                })
            else:
                property_obj.create({
                    'company_id': self.env.company.id,
                    'name': 'property_account_receivable_id',
                    'fields_id': receivable_field.id,
                    'res_id': False,
                    'type': 'many2one',
                    'value_reference': 'account.account,{}'.format(self.partner_receivable_account_id.id)
                })
        if self.partner_payable_account_id:
            payable_field = self.env.ref('account.field_res_partner__property_account_payable_id')
            payable_property = property_obj.search([('company_id', '=', self.env.company.id),
                                                       ('name', '=', 'property_account_payable_id'),
                                                       ('res_id', '=', False),
                                                       ('fields_id', '=', payable_field.id)])
            if payable_property:
                payable_property.sudo().write({
                    'value_reference': 'account.account,{}'.format(self.partner_payable_account_id.id)
                })
            else:
                property_obj.create({
                    'company_id': self.env.company.id,
                    'name': 'property_account_payable_id',
                    'fields_id': payable_field.id,
                    'res_id': False,
                    'type': 'many2one',
                    'value_reference': 'account.account,{}'.format(self.partner_payable_account_id.id)
                })
