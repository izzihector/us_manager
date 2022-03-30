from odoo import api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_default_country(self):
        return self.env.ref('base.id')

    country_id = fields.Many2one(comodel_name='res.country', default=_get_default_country)

    @api.model
    def create(self, values):
        mobile_value = values.get('mobile', '')
        if isinstance(mobile_value, str):
            if '+' in mobile_value:
                raise UserError('Mobile field should not contains "+".')
            if mobile_value.startswith('0'):
                raise UserError('Mobile field should start with country code.')
        return super(ResPartner, self).create(values)
    
    def write(self, values):
        mobile_value = values.get('mobile', '')
        if isinstance(mobile_value, str):
            if '+' in mobile_value:
                raise UserError('Mobile field should not contains "+".')
            if mobile_value.startswith('0'):
                raise UserError('Mobile field should start with country code.')
        return super(ResPartner, self).write(values)

    @api.onchange('l10n_id_pkp')
    def onchange_id_pkp(self):
        if self.l10n_id_pkp:
            self.property_account_position_id = False
        else:
            self.property_account_position_id = self.env['account.fiscal.position'].search([('name', '=', 'Non PKP')],
                                                                                           limit=1).id or False
