# -*- coding: utf-8 -*-

from odoo import _, models, fields
from odoo.exceptions import UserError


class res_users(models.Model):
    """
    Re write to change user role
    """
    _inherit = "res.users"

    def _inverse_security_role_ids(self):
        """
        Inverse method for security_role_ids
        """
        access_settings_group = self.env.ref("base.group_erp_manager")
        # Custom by MCS (temporary)
        # if self.env.user.has_group("base.group_erp_manager"):
        for user in self:
            if user.security_role_ids:
                all_groups = user.security_role_ids.mapped("group_ids")
                if self.env.user == user and access_settings_group not in (all_groups + all_groups.implied_ids):
                    raise UserError(_("""
                        This operation is not possible since after that your user would not have
                        rights to change user access rights."""))
                else:
                    user.sudo().groups_id = [(6, 0, all_groups.ids)]
        # else:
        #     raise UserError(_("Sorry you are not allowed to change this role"))

    security_role_ids = fields.Many2many(
        "security.role",
        "security_role_res_users_rel_table",
        "security_role_id",
        "res_users_id",
        string="Roles",
        inverse=_inverse_security_role_ids,
    )

    def action_create_role(self):
        """
        The method to open a role form view with pre-filled groups

        Returns:
         * ir.actions.window

        Extra info:
         * Expected singletom
        """
        self.ensure_one()
        action = self.env.ref("security_user_roles.security_role_action_form_only").read()[0]
        action["context"] = {"default_group_ids": [(6, 0, self.groups_id.ids)]}
        return action
