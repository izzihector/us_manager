from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_add_tax_amount = fields.Monetary(string="Auto Add WAPU Limit Amount", related='company_id.auto_add_tax_amount',
                                          readonly=False)
    consignment_tax_id = fields.Many2one(comodel_name="account.tax", string="Taxes", readonly=False,
                                         related='company_id.consignment_tax_id')
    auto_add_second_tax_amount = fields.Monetary(string="Auto Add PPH 22 Limit Amount",
                                                 related='company_id.auto_add_second_tax_amount',
                                                 readonly=False)
    consignment_second_tax_id = fields.Many2one(comodel_name="account.tax", string="Taxes", readonly=False,
                                                related='company_id.consignment_second_tax_id')
