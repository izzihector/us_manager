from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pr_approval_double = fields.Boolean("Purchase Request Approval (Kepala Bidang)",
                                       default=lambda self: self.env.user.company_id.pr_double_validation in (
                                           'two_step', 'three_step', 'four_step'))
    pr_double_validation_amount = fields.Monetary(related='company_id.pr_double_validation_amount',
                                                  string="Minimum Amount", currency_field='company_currency_id',
                                                  readonly=False)
    pr_approval_triple = fields.Boolean("Purchase Request Approval (Tim Pengadaan)",
                                              default=lambda self: self.env.user.company_id.pr_double_validation in (
                                                  'three_step', 'four_step'))
    pr_triple_validation_amount = fields.Monetary(related='company_id.pr_triple_validation_amount',
                                                  string="Minimum Amount", currency_field='company_currency_id',
                                                  readonly=False)
    pr_approval_quadruple = fields.Boolean("Purchase Request Approval (Tim Lelang)",
                                                 default=lambda self: self.env.user.company_id.pr_double_validation in (
                                                     'four_step'))
    pr_quadruple_validation_amount = fields.Monetary(related='company_id.pr_quadruple_validation_amount',
                                                     string="Minimum Amount", currency_field='company_currency_id',
                                                     readonly=False)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.pr_approval_quadruple:
            self.pr_double_validation = 'four_step'
        elif self.pr_approval_triple:
            self.pr_double_validation = 'three_step'
        elif self.pr_approval_double:
            self.pr_double_validation = 'two_step'
        else:
            self.pr_double_validation = 'one_step'
        self.env.user.company_id.pr_double_validation = self.pr_double_validation
