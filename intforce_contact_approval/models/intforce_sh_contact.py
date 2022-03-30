# -*- coding: utf-8 -*-
# Copyright (C) Intforce Software Private Limited

from odoo import models,fields,api,_
from odoo.exceptions import UserError

class ShContacts(models.Model):
    _inherit='res.partner'
    
    state = fields.Selection([('draft','Draft'),('under_approval','Under Approval'),('approved','Approved'),('not_approved','Not Approved')],default='draft',string="State",required=True)
    
    @api.model
    def create(self,vals):
        res = super(ShContacts,self).create(vals)
        res.active=False
        res.state='under_approval'
        return res
    
    def write(self,vals):
        if self:
            if vals.get('state') in ['under_approval','not_approved'] and self.state in ['draft','approved','under_approval','not_approved'] and self.active==True:
                vals.update({
                    'active':False
                    })
            elif vals.get('state') in ['approved'] and self.state in ['draft','under_approval','not_approved'] and self.active==False:
                vals.update({
                    'active':True
                    })
        return super(ShContacts,self).write(vals)
    
    
    def intforce_approve_contact(self):
        user_id = self.env['res.users'].sudo().search([('id','=',self.env.user.id)],limit=1)
        if user_id.has_group('intforce_contact_approval.intforce_contact_approve_manager'):
            for rec in self:
                if rec.state in ['draft','not_approved','under_approval'] and rec.active==False:
                    rec.state = 'approved'
                    rec.active=True
        else:
            raise UserError("You are not Contact Manager")   
    
    def intforce_not_approve_contact(self):
        user_id = self.env['res.users'].sudo().search([('id','=',self.env.user.id)],limit=1)
        if user_id.has_group('intforce_contact_approval.intforce_contact_approve_manager'):
            for rec in self:
                if rec.state in ['draft','under_approval','approved'] and rec.active==True:
                    rec.state = 'not_approved'
                    rec.active=False
        else:
            raise UserError("You are not Contact Manager")
    
