# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_user_department(self):
        return self._context.get('default_is_internal_consumption') and self.env.user.department_id.id

    is_internal_consumption = fields.Boolean(string='Internal Consumption')
    from_department_id = fields.Many2one(comodel_name='hr.department', string='Dept. From', default=_get_user_department )
    to_department_id = fields.Many2one(comodel_name='hr.department', string='Dept. To', default=_get_user_department )

    

