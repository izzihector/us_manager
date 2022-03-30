# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    allow_salesperson = fields.Boolean('Allow Salesperson')
    salesperson_ids = fields.Many2many(comodel_name='res.users', string="Allowed Salesperson")

    def get_salesperson(self, c_id):
        list_data = []
        config = self.env['pos.config'].search([('id', '=', c_id)])
        for z in config.salesperson_ids:
            role = "cashier"
            if z.has_group('point_of_sale.group_pos_manager'):
                role = "manager"
            list_data.append({
                'id': z.id,
                'name': z.partner_id.name,
                'company_id': [z.company_id.id, z.company_id.name],
                'role': role,
                'group_id': [g.id for g in z.groups_id]
            })
        return list_data
