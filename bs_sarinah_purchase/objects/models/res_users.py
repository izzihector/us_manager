from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_tim_pengadaan = fields.Boolean(string="Tim Pengadaan?", compute='compute_user_tim', store=True)
    is_tim_lelang = fields.Boolean(string="Tim Lelang?", compute='compute_user_tim', store=True)

    @api.depends('groups_id')
    @api.onchange('groups_id')
    def compute_user_tim(self):
        for user in self:
            user.is_tim_pengadaan = user.has_group('bs_sarinah_purchase.group_purchase_request_tim_pengadaan')
            user.is_tim_lelang = user.has_group('bs_sarinah_purchase.group_purchase_request_tim_lelang')
