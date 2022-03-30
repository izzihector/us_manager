from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    pr_double_validation = fields.Selection([
        ('one_step', 'Confirm purchase request in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a purchase request'),
        ('three_step', 'Get 3 levels of approvals to confirm a purchase request'),
        ('four_step', 'Get 4 levels of approvals to confirm a purchase request'),
    ], string="Levels of Approvals Purchase Request", default='one_step', help="Provide a double validation mechanism for purchases request")
    pr_double_validation_amount = fields.Monetary(string='Double validation amount', default=5000000,
                                                  help="Minimum amount for which a double validation is required")
    pr_triple_validation_amount = fields.Monetary(string='Triple validation amount', default=10000000,
                                                  help="Minimum amount for which a triple validation is required")
    pr_quadruple_validation_amount = fields.Monetary(string='Quadruple validation amount', default=20000000,
                                                     help="Minimum amount for which a quadruple validation is required")
