# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class Employee(models.Model):
    _inherit = "hr.employee"

    is_user = fields.Boolean('Is a user', groups="hr.group_hr_user")
    user_archived = fields.Boolean('User link archived', groups="hr.group_hr_user")

    # @api.multi
    def link_to_user(self):
        self.ensure_one()
        user_val = {
            'active': True,
            'is_employee': True,
            'employee_id': self.id,
            'login': self.work_email,
            'name': self.name,
            'image_1920': self.image_1920
        }
        user_obj = self.env['res.users']
        user_created = user_obj.sudo().create(user_val)
        if user_created:
            self.write({'is_user': True})
            if not self.address_id:
                self.address_id = user_created.partner_id.id
                self.address_id.email = self.work_email
                self.address_id.mobile = self.mobile_phone
                self.address_id.phone = self.work_phone
            if not self.user_id:
                self.user_id = user_created.id

    # @api.multi
    def archive_user_link(self):
        self.ensure_one()
        user_obj = self.env['res.users'].search([('employee_id', '=', self.id)], limit=1)
        if user_obj:
            user_obj.write({'active': False})
            user_obj.partner_id.write({'active': False})
            self.write({'is_user': False, 'user_archived': True, 'address_id': False})
            if self.address_id and self.address_id.id == user_obj.partner_id.id:
                self.write({'address_id': False})
            if self.user_id and self.user_id.id == user_obj.id:
                self.write({'user_id': False})

    # @api.multi
    def active_user_link(self):
        self.ensure_one()
        user_obj = self.env['res.users'].search([('employee_id', '=', self.id), ('active', '=', False)], limit=1)
        if user_obj:
            user_obj.write({'active': True})
            user_obj.partner_id.write({'active': True})
            self.write({'is_user': True, 'user_archived': False})
            if not self.address_id:
                self.write({'address_id': user_obj.partner_id.id})
            if not self.user_id:
                self.write({'user_id': user_obj.id})

# class Employee_Public(models.Model):
#     _inherit = "hr.employee.public"
#
#     is_user = fields.Boolean('Is a user')
#     user_archived = fields.Boolean('User link archived')