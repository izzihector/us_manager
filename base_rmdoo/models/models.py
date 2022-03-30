# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.tools.misc import clean_context, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError
import calendar, datetime, odoo.addons.decimal_precision as dp
import time
import psycopg2


class IrSequence(models.Model):
    _inherit = 'ir.sequence'
    
    reset = fields.Selection([
        ('yearly', 'Yearly'),
        ('monthly', 'Monthly'),
        ('daily', 'Daily'),
    ], string='Reset', required=False, default='yearly')
    
    def _create_date_range_seq(self, date):
        year = fields.Date.from_string(date).strftime('%Y')
        month = fields.Date.from_string(date).strftime('%m')
        day = fields.Date.from_string(date).strftime('%d')
        if self.reset == 'daily':
            date_from = '{}-{}-{}'.format(year, month, day)
            date_to = '{}-{}-{}'.format(year, month, day)
        elif self.reset == 'monthly':
            date_from = '{}-{}-01'.format(year, month)
            date_to = '{}-{}-{}'.format(year, month, str(calendar.monthrange(int(year), int(month))[1]).zfill(2))
        else:
            date_from = '{}-01-01'.format(year)
            date_to = '{}-12-31'.format(year)
        date_range = self.env['ir.sequence.date_range'].search([('sequence_id', '=', self.id), ('date_from', '>=', date), ('date_from', '<=', date_to)], order='date_from desc', limit=1)
        if date_range:
            date_to = date_range.date_from + datetime.timedelta(days=-1)
        date_range = self.env['ir.sequence.date_range'].search([('sequence_id', '=', self.id), ('date_to', '>=', date_from), ('date_to', '<=', date)], order='date_to desc', limit=1)
        if date_range:
            date_from = date_range.date_to + datetime.timedelta(days=1)
        seq_date_range = self.env['ir.sequence.date_range'].sudo().create({
            'date_from': date_from,
            'date_to': date_to,
            'sequence_id': self.id,
        })
        return seq_date_range


class UnderConstruction(models.Model):
    _name = 'no.content'
    _description = 'Under Construction'
    
    dummy = fields.Char('dummy')
    

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    goods_note = fields.Boolean('Use GRN before invoice')
    group_stock_goods_delivered = fields.Boolean('Goods Stock Delivered', implied_group='base_rmdoo.group_stock_goods_delivered')
    group_stock_goods_received = fields.Boolean('Goods Stock Received', implied_group='base_rmdoo.group_stock_goods_received')
    group_account_user = fields.Boolean('Show Full Accounting Features', implied_group='account.group_account_user')
    
    def set_values(self):
        self.group_stock_goods_delivered = self.goods_note
        self.group_stock_goods_received = self.goods_note
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('invoice.goods_note', self.goods_note and 'True' or 'False')
#         self.create({
#             'group_stock_goods_delivered' : self.goods_note,
#             'group_stock_goods_received' : self.goods_note,
#         }).execute()
        
    def get_values(self):
        ret = super(ResConfigSettings, self).get_values()
        ret.update(goods_note=True if self.env['ir.config_parameter'].sudo().get_param('invoice.goods_note') == 'True' else False)
        return ret
    
    @api.model
    def init_base_rmdoo(self):
        # dp = self.env.ref('product.decimal_discount').id
        # dpo = self.env['decimal.precision'].browse(dp)
        # dpo.write({'digits':14})
        
        self.env['ir.sequence'].browse(self.env.ref('stock.sequence_proc_group').id).write({
            'prefix':'PG%(y)s%(month)s%(day)s-',
            'padding':4,
            'reset':'monthly',
            'use_date_range':True,
        })
        self.env['ir.sequence'].browse(self.env.ref('stock.sequence_stock_scrap').id).write({
            'prefix':'SP%(y)s%(month)s%(day)s-',
            'padding':4,
            'reset':'monthly',
            'use_date_range':True,
        })
        self.env['ir.sequence'].browse(self.env.ref('stock.sequence_mrp_op').id).write({
            'prefix':'OP%(y)s%(month)s%(day)s-',
            'padding':4,
            'reset':'monthly',
            'use_date_range':True,
        })
        
        pick_types = self.env['stock.picking.type'].search([('id', '!=', False)])
        for pick_type in pick_types:
            for seq_id in pick_type.sequence_id:
                if not seq_id.prefix.endswith('%(y)s%(month)s%(day)s-'):
                    if seq_id.prefix.endswith('/'):
                        seq_id.write({
                            'prefix': '%s%s' % (seq_id.prefix[:-1], '%(y)s%(month)s%(day)s-'),
                            'padding':4,
                            'reset':'monthly',
                            'use_date_range':True,
                        })
                    else:
                        seq_id.write({
                            'prefix': '%s/%s' % (seq_id.prefix, '%(y)s%(month)s%(day)s-'),
                            'padding':4,
                            'reset':'monthly',
                            'use_date_range':True,
                        })
                        
        # self.env['ir.actions.report'].search([('attachment_use', '=', True)]).write({'attachment_use':False})
        
        self.create({
            'group_product_variant' : True,
            'group_stock_adv_location' : True,
            'group_stock_multi_locations' : True,
            'group_stock_multi_warehouses' : True,
            'group_stock_packaging' : True,
            'group_stock_production_lot' : True,
            'group_stock_tracking_lot' : True,
            'group_stock_tracking_owner' : True,
            'group_uom' : True,
            'group_warning_stock' : True,
            # 'module_product_expiry' : True,
        }).execute()


class ResDiscount(models.Model):
    _name = 'res.discount'
    _description = 'Discount'
    
    name = fields.Char('Discount Name', required=True)
    discount_type = fields.Selection(string='Discount Type', selection=[
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Value')
    ], required=True, default='percentage', readonly=False)
    value = fields.Float(string='Value', required=True)
    
    @api.constrains('discount_type', 'value')
    def _check_discount(self):
        for line in self:
            if line.discount_type == 'percentage' and line.value > 100:
                raise ValidationError(_('Discount must be lower than 100%'))
            
    _sql_constraints = [
        ('res_discount_name_unique', 'UNIQUE(name)', _('Name value must be unique'))
    ]


class ReplenishRequestProduct(models.TransientModel):
    _name = 'replenish.request.product'
    _description = 'Purchase Request Product'
    
    replenish_request_id = fields.Many2one('replenish.request', string='Replenish Request', required=True, readonly=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float('Quantity', default=1, required=True)
    is_ga = fields.Boolean('Is GA?')
    
    def add_product(self):
        if self.ensure_one():
            rep_obj = self.env['product.replenish.request']
            return rep_obj.with_context(
                default_product_id=self.product_id.id
            ).create({
                'quantity':self.quantity,
                'replenish_request_id':self.replenish_request_id.id,
                'date_ordered':self.replenish_request_id.date_ordered,
                'date_planned':self.replenish_request_id.date_planned,
                'warehouse_id':self.replenish_request_id.warehouse_id.id,
                'request_department_id':self.replenish_request_id.request_department_id.id,
            })
        else:
            return False


class ReplenishRequest(models.Model):
    _name = 'replenish.request'
    _description = 'Replenish Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'date_ordered desc'
    
#     def _get_module_category_ids(self):
#         ex_app = self.env.ref('base.module_category_user_type', False)
#         group_list = self.env['res.groups'].sudo().get_groups_by_application()
#         app_list = []
#         for group_id in self.env.user.groups_id:
#             for app, kind, gs in group_list:
#                 if kind == 'selection':
#                     for g in gs:
#                         if (app.id != ex_app.id) and (group_id.id == g.id):
#                             app_list.append(app.id)
#         return list(set(app_list))
#      
#     def _get_request_group_default(self):
#         module = self._get_module_category_ids()
#         if len(module) > 0:
#             return module[0]
#         else:
#             return False
#          
#     def _get_request_group_domain(self):
#         return "[('id','in',%s)]" % (self._get_module_category_ids())
    
    def _get_department_tree(self, dept_id):
        dept_list = []
        if dept_id:
            dept_list.append(dept_id.id)
            if dept_id.child_ids:
                for child_id in dept_id.child_ids:
                    dept_list += self._get_department_tree(child_id)
        return dept_list

    def _get_request_department_id_domain(self):
        dept_list = []
        employee_ids = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        for employee_id in employee_ids:
            dept_list += self._get_department_tree(employee_id.department_id)
        dept_list = list(set(dept_list))
        ret = '[]'
        if dept_list:
            ret = "[('id','in',%s)]" % (dept_list)
        return ret
    
    name = fields.Char('Name', required=True, readonly=True, default=lambda self:'/')
    product_replenish_ids = fields.One2many('product.replenish.request', 'replenish_request_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Canceled'),
        ('approve', 'Approved'),
        ('part_confirm', 'Partially Requested'),
        ('confirm', 'Requested'),
        ('part_done', 'Partially Done'),
        ('done', 'Done'),
    ], string='Status', required=True, copy=False, default='draft', track_visibility='onchange')
    date_ordered = fields.Datetime('Ordered Date', required=True, default=lambda self:datetime.datetime.now(), help="Date at which the replenishment ordered.")
    date_planned = fields.Datetime('Scheduled Date', default=lambda self:(datetime.datetime.now() + datetime.timedelta(days=7)), help="Date at which the replenishment should take place.")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    confirm_uid = fields.Many2one('res.users', string='Confirmed By')
    approve_uid = fields.Many2one('res.users', string='Approved By')
    # request_group = fields.Many2one('ir.module.category', string='Request Group', required=True, default=_get_request_group_default, domain=_get_request_group_domain)
    request_department_id = fields.Many2one('hr.department', string='Request Department', required=True, domain=_get_request_department_id_domain, default=lambda self:False)  # self.env.ref('hr.dep_administration').id)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('replenish.request'))
    note = fields.Text('Internal Note')
    is_ga = fields.Boolean('Is GA?', default=False)
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)


    def open_quant(self):
        if self.ensure_one():
            self.env['stock.quant']._merge_quants()
            self.env['stock.quant']._unlink_zero_quants()
            ret = self.env.ref('stock.location_open_quants').read()[0]
            ret['domain'] = [
                ('product_id', 'in', [product.product_id.id for product in self.product_replenish_ids]),
                ('location_id', 'in', [product.warehouse_id.lot_stock_id.id for product in self.product_replenish_ids])
            ]
            return ret
        else:
            return False
    
    def open_move(self):
        if self.ensure_one():
            ret = self.env.ref('stock.stock_move_action').read()[0]
            ret['domain'] = [
                ('product_id', 'in', [product.product_id.id for product in self.product_replenish_ids]),
                ('location_dest_id', 'in', [product.warehouse_id.lot_stock_id.id for product in self.product_replenish_ids])
            ]
            return ret
        else:
            return False
    
    
    def add_product(self):
        if self.ensure_one():
            return {
                'name': 'Add Product',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'view_mode': 'form',
                'src_model': 'replenish.request',
                'res_model': 'replenish.request.product',
                'context': {
                    'create': False,
                    'edit': False,
                    'delete': False,
                    'default_replenish_request_id': self.id,
                    'default_is_ga': self.is_ga,
                },
            }
        else:
            return False
        
    
    def launch_replenishment(self):
        for line in self:
            if line.state == 'approve':
                for product in line.product_replenish_ids:
                    if product.state == 'approve':
                        product.launch_replenishment()
                        line.write({
                            'confirm_uid':self.env.user.id,
                        })
        return True
    
    
    def cancel(self):
        for line in self:
            confirm = False
            for product in line.product_replenish_ids:
                if product.state in ['draft', 'approve']:
                    product.cancel()
                if product.state in ['confirm', 'done']:
                    confirm = True
            line.state = 'confirm' if confirm else 'cancel'
        return True
    
    
    def approve(self):
        for line in self:
            if line.state == 'draft':
                if line.request_department_id:
                    if line.request_department_id.manager_id:
                        if line.request_department_id.manager_id.user_id:
                            if line.request_department_id.manager_id.user_id.id == self.env.user.id:
                                if line.product_replenish_ids:
                                    for product in line.product_replenish_ids:
                                        product.approve()
                                    line.write({
                                        'state':'approve',
                                        'approve_uid':self.env.user.id,
                                    })
                                else:
                                    raise UserError("Request don't have any line to approve")
                            else:
                                raise UserError('You aren\'t manager of this department.')
                        else:
                            raise UserError('Manager of this Department doesn\'t related to any user.')
                    else:
                        raise UserError('This Department doesn\'t have Manager.')
#                         employee_ids = self.env['hr.employee'].search([('user_id', '=', line.create_uids.id)])
#                         for employee_id in employee_ids:
#                             if employee_id.parent_id:
#                                 if employee_id.parent_id.user_id:
#                                     if employee_id.parent_id.user_id.id == self.env.user.id:
#                                         if line.product_replenish_ids:
#                                             for product in line.product_replenish_ids:
#                                                 product.approve()
#                                             line.write({
#                                                 'state':'approve',
#                                                 'approve_uid':self.env.user.id,
#                                             })
#                                         else:
#                                             raise UserError("Request don't have any line to approve")
                else:
                    raise UserError('Department is empty.')
        return True
    
    
    def reopen(self):
        for line in self:
            partial = False
            for product in line.product_replenish_ids:
                if product.state == 'cancel':
                    product.reopen()
                if product.state in ['confirm', 'done']:
                    partial = True
            line.state = 'part_confirm' if partial else 'draft'
        return True
    
    @api.model
    def default_get(self, fields):
        ret = super(ReplenishRequest, self).default_get(fields)
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if 'warehouse_id' in fields:
            ret['warehouse_id'] = warehouse.id
        if 'request_department_id' in fields:
            for employee_id in self.env.user.employee_ids:
                ret['request_department_id'] = employee_id.department_id and employee_id.department_id.id
        return ret
    
    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        for val in vals_list:
            if val.get('name', '/') == '/':
                if 'company_id' in val:
                    val['name'] = self.env['ir.sequence'].with_context(
                        force_company=val['company_id']).next_by_code('replenish.request') or '/'
                else:
                    val['name'] = self.env['ir.sequence'].next_by_code('replenish.request') or '/'
        return super(ReplenishRequest, self).create(vals_list)


class ProductReplenishRequest(models.Model):
    _name = 'product.replenish.request'
    _description = 'Product Replenish Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'date_ordered desc'
    
    @api.depends('product_id', 'group_id')
    def _get_name(self):
        for line in self:
            line.name = '%s%s' % (line.product_id.name, line.group_id and ' (%s)' % (line.group_id.name) or '')

#     def _get_module_category_ids(self):
#         ex_app = self.env.ref('base.module_category_user_type', False)
#         group_list = self.env['res.groups'].sudo().get_groups_by_application()
#         app_list = []
#         for group_id in self.env.user.groups_id:
#             for app, kind, gs in group_list:
#                 if kind == 'selection':
#                     for g in gs:
#                         if (app.id != ex_app.id) and (group_id.id == g.id):
#                             app_list.append(app.id)
#         return list(set(app_list))
#      
#     def _get_request_group_default(self):
#         module = self._get_module_category_ids()
#         if len(module) > 0:
#             return module[0]
#         else:
#             return False
#          
#     def _get_request_group_domain(self):
#         return "[('id','in',%s)]" % (self._get_module_category_ids())
     
    @api.onchange('product_id')
    def get_product_tmpl_id(self):
        if self.product_id:
            self.product_tmpl_id = self.product_id.product_tmpl_id

    def _get_department_tree(self, dept_id):
        dept_list = []
        if dept_id:
            dept_list.append(dept_id.id)
            if dept_id.child_ids:
                for child_id in dept_id.child_ids:
                    dept_list += self._get_department_tree(child_id)
        return dept_list

    def _get_request_department_id_domain(self):
        dept_list = []
        employee_ids = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        for employee_id in employee_ids:
            dept_list += self._get_department_tree(employee_id.department_id)
        ret = "[('id','in',%s)]" % (list(set(dept_list)))
        return ret
    
    @api.depends('product_uom_id', 'quantity', 'product_id', 'product_id.uom_id')
    def _compute_product_uom_qty(self):
        for line in self:
            if line.product_id.uom_id != line.product_uom_id:
                line.product_uom_qty = line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            else:
                line.product_uom_qty = line.quantity
            line.amount_estimation = line.price_estimation * line.quantity
    
    name = fields.Char('name', compute='_get_name')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_tmpl_id = fields.Many2one('product.template', String='Product Template', required=True)
    product_has_variants = fields.Boolean('Has variants', default=False, required=True)
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id', readonly=True, required=True)
    product_uom_id = fields.Many2one('uom.uom', string='UoM', required=True)
    quantity = fields.Float('Request Quantity', default=1, required=True)
    product_uom_qty = fields.Float(string='Total Quantity', compute='_compute_product_uom_qty', store=False)
    price_estimation = fields.Float(string='Price Estimation', digits='Product Price')
    amount_estimation = fields.Float(string='Amount Estimation', compute='_compute_product_uom_qty', store=False, digits='Product Price')
    date_ordered = fields.Datetime('Ordered Date', required=True, default=lambda self:datetime.datetime.now(), help="Date at which the replenishment ordered.")
    date_planned = fields.Datetime('Scheduled Date', default=lambda self:(datetime.datetime.now() + datetime.timedelta(days=7)), help="Date at which the replenishment should take place.")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    route_ids = fields.Many2many('stock.location.route', string='Preferred Routes', help="Apply specific route(s) for the replenishment instead of product's default routes.")
    group_id = fields.Many2one('procurement.group', string='Procurement Group')
    confirm_uid = fields.Many2one('res.users', string='Confirmed By')
    approve_uid = fields.Many2one('res.users', string='Approved By')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Canceled'),
        ('approve', 'Approved'),
        ('confirm', 'Requested'),
        ('done', 'Done')
    ], string='Status', required=True, copy=False, default='draft', track_visibility='onchange')
    # module_category_ids = fields.Many2many('ir.module.category', string='Groups', compute='_get_module_category_ids')
    # request_group = fields.Many2one('ir.module.category', string='Request Dept', required=True, default=_get_request_group_default, domain=_get_request_group_domain)
    request_department_id = fields.Many2one('hr.department', string='Request Department', required=True, domain=_get_request_department_id_domain, default=lambda self:False)  # self.env.ref('hr.dep_administration').id)
    replenish_request_id = fields.Many2one('replenish.request', string='Replenish Request')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('product.replenish.request'))
    note = fields.Text('Internal Note')
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency",
                                  related='replenish_request_id.currency_id')
    def open_quant(self):
        if self.ensure_one():
            self.env['stock.quant']._merge_quants()
            self.env['stock.quant']._unlink_zero_quants()
            ret = self.env.ref('stock.location_open_quants').read()[0]
            ret['domain'] = [
                ('product_id', '=', self.product_id.id),
                ('location_id', '=', self.warehouse_id.lot_stock_id.id)
            ]
            return ret
        else:
            return False
    
    def open_move(self):
        if self.ensure_one():
            ret = self.env.ref('stock.stock_move_action').read()[0]
            ret['domain'] = [
                ('product_id', '=', self.product_id.id),
                ('location_dest_id', '=', self.warehouse_id.lot_stock_id.id)
            ]
            return ret
        else:
            return False

    @api.model
    def default_get(self, fields):
        res = super(ProductReplenishRequest, self).default_get(fields)
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        product_tmpl_id = False
        if 'product_id' in fields:
            if self.env.context.get('default_product_id'):
                product_id = self.env['product.product'].browse(self.env.context['default_product_id'])
                product_tmpl_id = product_id.product_tmpl_id
                res['product_tmpl_id'] = product_id.product_tmpl_id.id
                res['product_id'] = product_id.id
            elif self.env.context.get('default_product_tmpl_id'):
                product_tmpl_id = self.env['product.template'].browse(self.env.context['default_product_tmpl_id'])
                res['product_tmpl_id'] = product_tmpl_id.id
                res['product_id'] = product_tmpl_id.product_variant_id.id
                if len(product_tmpl_id.product_variant_ids) > 1:
                    res['product_has_variants'] = True 
        if 'product_uom_id' in fields:
            res['product_uom_id'] = product_tmpl_id.uom_id.id
        if 'warehouse_id' in fields:
            res['warehouse_id'] = warehouse.id
        if 'date_planned' in fields:
            res['date_planned'] = datetime.datetime.now() + datetime.timedelta(days=7)
        if 'date_ordered' in fields:
            res['date_ordered'] = datetime.datetime.now()
        if 'request_department_id' in fields:
            for employee_id in self.env.user.employee_ids:
                res['request_department_id'] = employee_id.department_id and employee_id.department_id.id
        return res

    def launch_replenishment(self):
        if self.ensure_one():
            uom_reference = self.product_id.uom_id
            self.write({
                'quantity':self.product_uom_id._compute_quantity(self.quantity, uom_reference),
                'confirm_uid':self.env.user.id,
            })
            try:
                values = self._prepare_run_values()
                self.env['procurement.group'].with_context(clean_context(self.env.context)).run([self.env['procurement.group'].Procurement(
                    self.product_id,
                    self.quantity,
                    uom_reference,
                    self.warehouse_id.lot_stock_id,
                    values['group_id'].name,  # Name
                    values['group_id'].name,  # Origin
                    self.env.company,
                    values  # Values
                )])

                self.state = 'confirm'
                if self.replenish_request_id:
                    part_confirm = False
                    for product in self.replenish_request_id.product_replenish_ids:
                        if product.state == 'draft':
                            part_confirm = True
                    self.replenish_request_id.write({
                        'confirm_uid':self.env.user.id,
                        'state':'part_confirm' if part_confirm else 'confirm'
                    })
            except UserError as error:
                raise UserError(error)
        return True

    def _prepare_run_values(self):
        if self.state != 'approve':
            raise UserError('Request already confirmed')
        self.group_id = self.env['procurement.group'].create({
            'partner_id': self.product_id.responsible_id.partner_id.id,
        })
        values = {
            'warehouse_id': self.warehouse_id,
            'route_ids': self.route_ids,
            'date_planned': self.date_planned or fields.Datetime.now(),
            'group_id': self.group_id,
        }
        return values
    
    
    def cancel(self):
        for line in self:
            if line.state == 'draft':
                line.write({'state':'cancel'})
        return True
    
    
    def reopen(self):
        for line in self:
            if line.state == 'cancel':
                line.write({'state':'draft'})
        return True
    
    
    def approve(self):
        for line in self:
            if line.state == 'draft':
                if line.request_department_id:
                    if line.request_department_id.manager_id:
                        if line.request_department_id.manager_id.user_id:
                            if line.request_department_id.manager_id.user_id.id == self.env.user.id:
                                line.write({
                                    'state':'approve',
                                    'approve_uid':self.env.user.id,
                                })
                            else:
                                raise UserError('You aren\'t manager of this department.')
                        else:
                            raise UserError('Manager of this Department doesn\'t related to any user.')
                    else:
                        raise UserError('This Department doesn\'t have Manager.')
#                         employee_ids = self.env['hr.employee'].search([('user_id', '=', line.create_uids.id)])
#                         for employee_id in employee_ids:
#                             if employee_id.parent_id:
#                                 if employee_id.parent_id.user_id:
#                                     if employee_id.parent_id.user_id.id == self.env.user.id:
#                                         line.write({
#                                             'state':'approve',
#                                             'approve_uid':self.env.user.id,
#                                         })
                else:
                    raise UserError('Department is empty.')
        return True

    
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    def action_replenish_request(self):
        form_view_ref = self.env.ref('base_rmdoo.view_product_replenish_request', False)
        tree_view_ref = self.env.ref('base_rmdoo.view_product_replenish_request_tree', False)
        return  {
            'name': 'Replenish',
            'res_model': 'product.replenish.request',
            'src_model': 'product.replenish.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('product_id','=',%s)]" % (self.id),
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')]
        }

#     def _default_code(self):
#         prods = self.env['product.product'].search(['|', ('default_code', '=', False), ('default_code', '=', '/')])
#         for prod in prods:
#             prod.write({
#                 'default_code':self.env['ir.sequence'].next_by_code('internal.ean13')
#             })
#         prodts = self.env['product.template'].search(['|', ('default_code', '=', False), ('default_code', '=', '/')])
#         for prodt in prodts:
#             prodt.write({
#                 'default_code':self.env['ir.sequence'].next_by_code('internal.ean13')
#             })
#         return '/'
    
#     @api.depends('default_code')
#     def _get_default_code_qr(self):
#         # http://localhost:8069/report/barcode/?type=QR&value=okky&width=200&height=200
#         pass

    @api.depends()
    def _compute_qty_reserved(self):
        move_obj = self.env['stock.move']
        for record in self:
            count_in = count_out = 0.0
            in_moves = move_obj.search([
                ('product_id', '=', record.id),
                ('location_dest_id.usage', '=', 'internal'),
                ('state', 'not in', ['draft', 'cancel', 'done'])
            ])
            out_moves = move_obj.search([
                ('product_id', '=', record.id),
                ('location_id.usage', '=', 'internal'),
                ('state', 'not in', ['draft', 'cancel', 'done'])
            ])
            for in_move in in_moves:
                count_in += in_move.reserved_availability
            for out_move in out_moves:
                count_out += out_move.reserved_availability
            record.qty_reserved = count_in - count_out
            
    @api.depends()
    def _get_product_location(self):
        move_obj = self.env['stock.move']
        locations = self.env['stock.location'].search([('usage', '=', 'internal')])
        for record in self:
            vlocs = []
            vnlocs = []
            for location in locations:
                count = 0.0
                counts_in = move_obj.read_group([
                    ('product_id', '=', record.id),
                    ('location_dest_id', '=', location.id),
                    ('state', '=', 'done')
                ], ['count_in:sum(product_qty)'], ['product_id'])
                counts_out = move_obj.read_group([
                    ('product_id', '=', record.id),
                    ('location_id', '=', location.id),
                    ('state', '=', 'done')
                ], ['count_out:sum(product_qty)'], ['product_id'])
                for count_in in counts_in:
                    count += (count_in and count_in['count_in'] or 0.0)
                for count_out in counts_out:
                    count -= (count_out and count_out['count_out'] or 0.0)
                if count > 0.0:
                    vlocs.append(location.id)
                elif count < 0.0:
                    vnlocs.append(location.id)
            record.location_ids = vlocs
            record.negative_location_ids = vnlocs
    
    default_code = fields.Char('Internal Reference', index=True, default=lambda self:'/', store=True)
    tmpl_company_id = fields.Many2one('res.company', 'Company', related='product_tmpl_id.company_id', default=lambda self: self.env['res.company']._company_default_get('product.template'), store=True)
    qty_reserved = fields.Float('Reserved Quantity', compute='_compute_qty_reserved', digits='Product Unit of Measure')
    orderpoint_ids = fields.One2many('stock.warehouse.orderpoint', 'product_id', string='Order Point')
    location_ids = fields.Many2many('stock.location', string='Location', compute='_get_product_location')
    negative_location_ids = fields.Many2many('stock.location', string='Negative Location', compute='_get_product_location')
    
#     @api.constrains('default_code')
#     def _default_code(self):
#         for record in self:
#             if record.default_code == '/':
#                 record.default_code = self.env['ir.sequence'].next_by_code('internal.ean13')
    
    # @api.model_create_multi
    # @api.returns('self', lambda value:value.id)
    # def create(self, vals_list):
    #     try:
    #         for val in vals_list:
    #             if val.get('default_code', '/') == '/':
    #                 val['default_code'] = self.env['ir.sequence'].next_by_code('internal.ean13')
    #         return super(ProductProduct, self).create(vals_list)
    #     except psycopg2.Error:
    #         for val in vals_list:
    #             val['default_code'] = self.env['ir.sequence'].next_by_code('internal.ean13')
    #         return super(ProductProduct, self).create(vals_list)

#
#     def write(self, vals):
#         if vals.get('default_code', '/') == '/':
#             vals['default_code'] = self.env['ir.sequence'].next_by_code('internal.ean13')
#         return super(ProductProduct, self).write(vals)

#     @api.model
#     def default_get(self, fields):
#         res = super(ProductProduct, self).default_get(fields)
#         res['default_code'] = self.env['ir.sequence'].next_by_code('internal.ean13')
#         return res

    def action_open_reserved(self):
        return super(ProductProduct, self).action_open_quants()

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code,tmpl_company_id)', "An internal reference can only be assigned to one product per company !"),
    ]

    
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def action_replenish_request(self):
        form_view_ref = self.env.ref('base_rmdoo.view_product_replenish_request', False)
        tree_view_ref = self.env.ref('base_rmdoo.view_product_replenish_request_tree', False)
        return  {
            'name': 'Replenish',
            'res_model': 'product.replenish.request',
            'src_model': 'product.replenish.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('product_tmpl_id','=',%s)]" % (self.id),
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')]
        }
        
    
    def _compute_qty_reserved(self):
        move_obj = self.env['stock.move']
        for record in self:
            count_in = count_out = 0.0
            in_moves = move_obj.search([
                ('product_id.product_tmpl_id', '=', record.id),
                ('location_dest_id.usage', '=', 'internal'),
                ('state', 'not in', ['draft', 'cancel', 'done'])
            ])
            out_moves = move_obj.search([
                ('product_id.product_tmpl_id', '=', record.id),
                ('location_id.usage', '=', 'internal'),
                ('state', 'not in', ['draft', 'cancel', 'done'])
            ])
            for in_move in in_moves:
                count_in += in_move.reserved_availability
            for out_move in out_moves:
                count_out += out_move.reserved_availability
            record.qty_reserved = count_in - count_out

    def _set_default_code(self):
        if len(self.product_variant_ids) == 1:
            if self.default_code == '/':
                self.default_code = self.env['ir.sequence'].next_by_code('internal.ean13')
            self.product_variant_ids.default_code = self.default_code
        
#     default_code = fields.Char(default=lambda self:'/')
    default_code = fields.Char('Internal Reference', compute='_compute_default_code', inverse='_set_default_code', default=lambda self:'/', store=True)
    qty_reserved = fields.Float('Reserved Quantity', compute='_compute_qty_reserved', digits='Product Unit of Measure')
    is_ga = fields.Boolean('Product Non Niaga?', default=False)

#     @api.model_create_multi
#     @api.returns('self', lambda value:value.id)
#     def create(self, vals_list):
#         for val in vals_list:
#             if val.get('default_code', '/') == '/':
#                 val['default_code'] = self.env['ir.sequence'].next_by_code('internal.ean13')
#         return super(ProductTemplate, self).create(vals_list)
     
#     
#     def write(self, vals):
#         if vals.get('default_code', '/') == '/':
#             vals['default_code'] = self.env['ir.sequence'].next_by_code('internal.ean13')
#         return super(ProductTemplate, self).write(vals)
    
    def action_open_reserved(self):
        return super(ProductTemplate, self).action_open_quants()


# class AccountInvoice(models.Model):
#     _inherit = "account.invoice"
#
# #     def _use_goods_note(self):
# #         for line in self:
# #             line.use_goods_note = True if self.env['ir.config_parameter'].sudo().get_param('invoice.goods_note') == 'True' else False
#
#     goods_note = fields.Char(string='Goods Note', index=True, readonly=True, required=True, default=lambda self:'/', states={'draft': [('readonly', False)]})
#     use_goods_note = fields.Boolean('Use Goods Note', readonly=True)  # , compute='_use_goods_note', store=True)
#
#     @api.model
#     def default_get(self, fields):
#         res = super(AccountInvoice, self).default_get(fields)
#         res['use_goods_note'] = True if self.env['ir.config_parameter'].sudo().get_param('invoice.goods_note') == 'True' else False
#         return res
#
#     @api.model_create_multi
#     @api.returns('self', lambda value:value.id)
#     def create(self, vals):
#         if self.env['ir.config_parameter'].sudo().get_param('invoice.goods_note') == 'True':
#             for val in vals:
#                 if val.get('goods_note', '/') == '/':
#                     if 'company_id' in val:
#                         if val.get('type') == 'in_invoice':
#                             val['goods_note'] = self.env['ir.sequence'].with_context(force_company=val['company_id']).next_by_code('account.grn') or '/'
# #                         elif val.get('type') == 'out_invoice':
# #                             val['goods_note'] = self.env['ir.sequence'].with_context(force_company=val['company_id']).next_by_code('account.gdn') or '/'
#                     else:
#                         if val.get('type') == 'in_invoice':
#                             val['goods_note'] = self.env['ir.sequence'].next_by_code('account.grn') or '/'
# #                         elif val.get('type') == 'out_invoice':
# #                             val['goods_note'] = self.env['ir.sequence'].next_by_code('account.gdn') or '/'
#         return super(AccountInvoice, self).create(vals)

    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends('quantity', 'product_uom_id')
    def _get_view_qty(self):
        for record in self:
            record.view_quantity = record.quantity
            record.view_uom_id = record.product_uom_id.id

    # state = fields.Selection('Status', related='invoice_id.state', required=True, store=True)
    view_quantity = fields.Float(string='Qty', digits='Product Unit of Measure', compute='_get_view_qty')
    view_uom_id = fields.Many2one('uom.uom', string='UoM', compute='_get_view_qty')

    
class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'mail.thread', 'mail.activity.mixin', 'portal.mixin']
    
    @api.depends('line_ids')
    def _compute_debit_credit_amount(self):
        for record in self:
            debit = credit = 0.0
            for aml in record.line_ids:
                debit += aml.debit
                credit += aml.credit
            record.debit = debit
            record.credit = credit
            
    debit = fields.Monetary(default=0.0, currency_field='currency_id', compute='_compute_debit_credit_amount')
    credit = fields.Monetary(default=0.0, currency_field='currency_id', compute='_compute_debit_credit_amount')

    goods_note = fields.Char(string='Goods Note', index=True, readonly=True, required=True, default=lambda self: '/',
                             states={'draft': [('readonly', False)]})
    use_goods_note = fields.Boolean('Use Goods Note', readonly=True)  # , compute='_use_goods_note', store=True)

    @api.model
    def default_get(self, fields):
        res = super(AccountMove, self).default_get(fields)
        res['use_goods_note'] = True if self.env['ir.config_parameter'].sudo().get_param(
            'invoice.goods_note') == 'True' else False
        return res

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if self.env['ir.config_parameter'].sudo().get_param('invoice.goods_note') == 'True':
            for val in vals:
                if val.get('goods_note', '/') == '/':
                    if 'company_id' in val:
                        if val.get('type') == 'in_invoice':
                            val['goods_note'] = self.env['ir.sequence'].with_context(
                                force_company=val['company_id']).next_by_code('account.grn') or '/'
                    else:
                        if val.get('type') == 'in_invoice':
                            val['goods_note'] = self.env['ir.sequence'].next_by_code('account.grn') or '/'
        return super(AccountMove, self).create(vals)

    
class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    def _get_sequence_values(self):
        values = super(StockWarehouse, self)._get_sequence_values()
        values.update({
            'in_type_id': {
                'name': self.name + ' ' + _('Sequence in'),
                'prefix': self.code + '/IN%(y)s%(month)s%(day)s-',
                'padding':4,
                'reset':'monthly',
                'use_date_range':True,
                'company_id': self.company_id.id,
            },
            'out_type_id': {
                'name': self.name + ' ' + _('Sequence out'),
                'prefix': self.code + '/OUT%(y)s%(month)s%(day)s-',
                'padding':4,
                'reset':'monthly',
                'use_date_range':True,
                'company_id': self.company_id.id,
            },
            'pack_type_id': {
                'name': self.name + ' ' + _('Sequence packing'),
                'prefix': self.code + '/PACK%(y)s%(month)s%(day)s-',
                'padding':4,
                'reset':'monthly',
                'use_date_range':True,
                'company_id': self.company_id.id,
            },
            'pick_type_id': {
                'name': self.name + ' ' + _('Sequence picking'),
                'prefix': self.code + '/PICK%(y)s%(month)s%(day)s-',
                'padding':4,
                'reset':'monthly',
                'use_date_range':True,
                'company_id': self.company_id.id,
            },
            'int_type_id': {
                'name': self.name + ' ' + _('Sequence internal'),
                'prefix': self.code + '/INT%(y)s%(month)s%(day)s-',
                'padding':4,
                'reset':'monthly',
                'use_date_range':True,
                'company_id': self.company_id.id,
            },
        })
        return values
    
    
class StockLocation(models.Model):
    _inherit = "stock.location"
    
    department_id = fields.Many2one('hr.department', 'Department')
    
    
class StockMove(models.Model):
    _inherit = 'stock.move'
    
    @api.depends('product_id', 'product_qty')
    def _get_valuation(self):
        for record in self:
            sys_end = record.product_id.with_context(
                to_date=str(
                    self.env.context.get(
                        'to_date',
                        datetime.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
                    )
                ) + ' 23:59:59'
            )
            unit_cost = (sys_end.stock_value / sys_end.qty_at_date) if sys_end.qty_at_date else 0.0
            record.valuation = record.product_qty * unit_cost
    
    valuation = fields.Float('Valuation', compute='_get_valuation')
    
    
class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"
    
    code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        # ('internal', 'Internal')
    ], 'Type of Operation')

    
class Employee(models.Model):
    _inherit = "hr.employee"
    
    department_id = fields.Many2one('hr.department', 'Department', required=False)
    parent_id = fields.Many2one('hr.employee', 'Supervisor')

    
class ProductInquiry(models.TransientModel):
    _name = 'product.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Pivot Product'
    
    @api.depends(
        'create_uids',
        'write_uids',
        'product_name',
        'categ_ids',
        'type',
        'negative_location',
        'negative_on_hand',
        'negative_forecast'
    )
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            lines = lines_obj.search([
                ('type', '=', line.type) if line.type else ('id', '!=', False),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('name', 'ilike', '%s' % ('%' + line.product_name + '%')) if line.product_name else ('id', '!=', False),
                ('categ_id', 'in', [categ.id for categ in line.categ_ids]) if line.categ_ids else ('id', '!=', False),
            ])
            line_ids = lines.ids
            if line.negative_location:
                for l in lines:
                    if (l.id in line_ids) and (not l.negative_location_ids):
                        line_ids.remove(l.id)
            if line.negative_on_hand:
                for l in lines:
                    if (l.id in line_ids) and l.qty_available >= 0:
                        line_ids.remove(l.id)
            if line.negative_forecast:
                for l in lines:
                    if (l.id in line_ids) and l.virtual_available >= 0:
                        line_ids.remove(l.id)
            line.lines = line_ids
    
    @api.depends('lines', 'is_value')
    def _get_pivot(self):
        super(ProductInquiry, self)._get_pivot(
            renderer='Table With Subtotal',
            rows=[
                'Product (Category)',
                'Product',
                'Product (Variant)',
            ] if self.type else [
                'Product Type',
                'Product (Category)',
                'Product',
                'Product (Variant)',
            ],
            cols=[] if self.is_value else ['Unit of Measure'],
            aggregator='Sum',
            vals=['Value'] if self.is_value else ['Quantity On Hand']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('product.product')
    
    is_value = fields.Boolean('Valuation', default=lambda self:True)
    
    product_name = fields.Char('Product Name')
    categ_ids = fields.Many2many('product.category', string='Product Category', domain=lambda self:self._get_domain('categ_id'))
    type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Storable Product')
    ], string='Product Type', default='product', required=False)
    negative_location = fields.Boolean('Negative Location')
    negative_on_hand = fields.Boolean('Negative on Hand')
    negative_forecast = fields.Boolean('Negative Forecast')
    

class StockMovesInquiry(models.TransientModel):
    _name = 'stock.move.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Stock Moves Inquiries'
    
    @api.depends('lines')
    def _get_pivot(self):
        super(StockMovesInquiry, self)._get_pivot(
            rows=[
                'Product Type',
                'Product'
            ],
            cols=['Destination Location'],
            aggregator='Sum',
            visible_attributes=[
                'Product', 'Reference', 'Status', 'Unit Price', 'Unit of Measure',
                'Warehouse', 'Date', 'Creation Date', 'Expected Date', 'Initial Demand'
                'Landed Cost', 'Real Quantity', 'Quantity Done', 'Quantity Reserved',
                'Destination Location', 'Source Location', 'Initial Demand'
            ],
            vals=['Initial Demand']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('stock.move')


class ProductMovesInquiry(models.TransientModel):
    _name = 'product.move.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Product Moves Inquiries'
    
    @api.depends('lines')
    def _get_pivot(self):
        super(ProductMovesInquiry, self)._get_pivot(
            rows=[
                'Product Type',
                'Product'
            ],
            cols=[
                'Status'
                ],
            aggregator='Sum',
            visible_attributes=[
                'Product', 'Reference', 'Status', 'From', 'To', 'Unit of Measure',
#                 'Warehouse', 'Date', 'Creation Date', 'Expected Date', 'Initial Demand'
                'Real Reserved Quantity', 'Reserved', 'Source Package', 'Done'
#                 'Destination Location', 'Source Location', 'Initial Demand'
            ],
            vals=['Real Reserved Quantity']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('stock.move.line')

    
class InventoryInquiry(models.TransientModel):
    _name = 'inventory.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Pivot Inventory Stocks'
    
    @api.depends('lines')
    def _get_pivot(self):
        super(InventoryInquiry, self)._get_pivot(
            rows=[
                'Product', 'Product (Variant)'
            ],
            cols=[
                'Location',
                'Quantity',
            ],
            aggregator='Sum',
#             visible_attributes=[
#                 'Product (Category)', 'Product', 'Product (Variant)',
#                 'Create On', 'Incoming Date', 'Removal Date',
#                 'Lot/Serial Number', 'Location', 'Package',
#                 'Quantity', 'Reserved Quantity'
#             ],
            vals=['Quantity']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('stock.quant')

    
class TransfersInquiry(models.TransientModel):
    _name = 'transfer.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Pivot Transfers'
    
    @api.depends('lines')
    def _get_pivot(self):
        super(TransfersInquiry, self)._get_pivot(
            rows=[
                'Product', 'Product (Variant)'
            ],
            cols=[
                 'Location', 'Quantity'
            ],
            aggregator='Sum',
#             visible_attributes=[
#                 'Product (Category)', 'Product (Template)', 'Product',
#                 'Create On', 'Incoming Date', 'Removal Date',
#                 'Lot/Serial Number', 'Location', 'Package',
#                 'Quantity', 'Reserved Quantity'
#             ],
            vals=['Quantity']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('stock.picking')
    
# class GPInvTrfInquiry(models.TransientModel):
#     _name = 'gpinvtrf.inquiry'
#     _inherit = 'inquiry.report'
#     _description = 'GP by Invetory Transfer'
#     
#     name = fields.Char(default=_description)
#     create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
#     write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
#     lines = fields.Many2many('stock.move')

# class InventoryCostPricelistInquiry (models.TransientModel):
#     _name = 'costpricelist.inquiry'
#     _description = 'Inventory Cost & Pricelist Inquiries'
#     
#     def _get_daterange(self, date=datetime.datetime.now(), daterange='monthly'):
#         year = fields.Date.from_string(date).strftime('%Y')
#         month = fields.Date.from_string(date).strftime('%m')
#         day = fields.Date.from_string(date).strftime('%d')
#         if daterange == 'daily':
#             date_from = '{}-{}-{}'.format(year, month, day)
#             date_to = '{}-{}-{}'.format(year, month, day)
#         elif daterange == 'monthly':
#             date_from = '{}-{}-01'.format(year, month)
#             date_to = '{}-{}-{}'.format(year, month, str(calendar.monthrange(int(year), int(month))[1]).zfill(2))
#         else:
#             date_from = '{}-01-01'.format(year)
#             date_to = '{}-12-31'.format(year)
#         return date_from, date_to
#     
#     name = fields.Char('Name', default=_description, readonly=True)
#     date_from = fields.Date('From', default=lambda self:self._get_daterange(daterange='monthly')[0], required=True)
#     date_to = fields.Date('To', default=lambda self:self._get_daterange(daterange='monthly')[1], required=True)
#     product_ids = fields.Many2many('product.product', string='Product')
#     location_ids = fields.Many2many('stock.location', string='Location')
#     
#     
#     def print_pricelist(self):
#         return {
#             'type': 'ir.actions.report',
#             'name': 'Inventory Cost & Pricelist',
#             'model': self._name,
#             'report_type': 'qweb-html',
# #             'paperformat_id': self.env.ref('base_rmdoo.paperformat_rmdoo_a4_portrait'),
#             'report_name' : 'action_print_costpricelist',
#         }

# class SalesInquiry(models.TransientModel):
#     _name = 'inventory.sale.inquiry'
#     _inherit = 'inquiry.report'
#     _description = 'Pivot Sales'
#     
# #     @api.depends('date_from', 'date_to', 'create_uids', 'write_uids', 'product_ids', 'sale_ids', 'partner_ids', 'user_ids')
#     @api.depends('date_from', 'date_to', 'create_uids', 'write_uids', 'user_ids')
#     def _get_lines(self):
#         for line in self:
#             lines_obj = self.env[line.lines._name]
#             line.lines = lines_obj.search([
#                 ('date_order', '>=', line.date_from),
#                 ('date_order', '<=', line.date_to),
#                 ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
#                 ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
# #                 ('product_id', 'in', [product_id.id for product_id in line.product_ids]) if line.product_ids else ('id', '!=', False),
# #                 ('partner_id', 'in', [partner_id.id for partner_id in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
# #                 ('order_id', 'in', [order_id.id for order_id in line.sale_ids]) if line.sale_ids else ('id', '!=', False),
#                 ('user_id', 'in', [user_id.id for user_id in line.user_ids]) if line.user_ids else ('id', '!=', False),
#             ])
#     
#     @api.depends('lines')
#     def _get_pivot(self):
#         super(SalesInquiry, self)._get_pivot(
#             rows=[
#                 'Product (Category)', 'Product'
#             ],
#             cols=[],
#             aggregator='Sum',
# #             visible_attributes=[
# #                 'Product (Category)', 'Product (Template)', 'Product',
# #                 'Date Order', 'Date Order (Year)', 'Date Order (Month)',
# #                 'Location', 'Salesperson', 'Customer', 'Quantity', 'Price Unit'
# #                 'Subtotal', 'Total'
# #             ],
#             vals=['Total']
#         )
#     
#     name = fields.Char(default=_description)
#     create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
#     write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
#     lines = fields.Many2many('inventory.pivot.sales', compute='_get_lines')
#     
#     user_ids = fields.Many2many('res.users', string='Salesperson', domain=lambda self:self._get_domain('user_id'))
    
# class PivotSales(models.Model):
#     _name = 'inventory.pivot.sales'
#     _inherit = 'report.all.channels.sales'
#     _description = 'Model Pivot Sales'
#     
#     name = fields.Char('Order Reference', readonly=True)
#     location_id = fields.Many2one('stock.location', string='Location')
#     partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
#     company_id = fields.Many2one('res.company', 'Company', readonly=True)
#     product_id = fields.Many2one('product.product', string='Product', readonly=True)
#     product_tmpl_id = fields.Many2one('product.template', 'Product Template', readonly=True)
#     date_order = fields.Datetime(string='Date Order', readonly=True)
#     user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
#     categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
#     price_total = fields.Float('Total', readonly=True)
#     price_unit = fields.Float('Price Unit', readonly=True)
#     pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', readonly=True)
#     state_id = fields.Many2one('res.country.state', 'Customer State', readonly=True)
#     country_id = fields.Many2one('res.country', 'Customer Country', readonly=True)
#     price_subtotal = fields.Float(string='Subtotal', readonly=True)
#     product_qty = fields.Float('Quantity', readonly=True)
#     analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
#     team_id = fields.Many2one('crm.team', 'Sales Team', readonly=True)
#     
#     def _so(self):
#         so_str = """
#                 SELECT sol.id AS id,
#                     so.name AS name,
#                     sp.location_id AS location_id,
#                     so.partner_id AS partner_id,
#                     sol.product_id AS product_id,
#                     pro.product_tmpl_id AS product_tmpl_id,
#                     so.date_order AS date_order,
#                     so.user_id AS user_id,
#                     pt.categ_id AS categ_id,
#                     so.company_id AS company_id,
#                     sol.price_total / CASE COALESCE(so.currency_rate, 0) WHEN 0 THEN 1.0 ELSE so.currency_rate END AS price_total,
#                     sol.price_unit AS price_unit,
#                     so.pricelist_id AS pricelist_id,
#                     rp.state_id AS state_id,
#                     rp.country_id AS country_id,
#                     sol.price_subtotal / CASE COALESCE(so.currency_rate, 0) WHEN 0 THEN 1.0 ELSE so.currency_rate END AS price_subtotal,
#                     (sol.product_uom_qty / u.factor * u2.factor) as product_qty,
#                     so.analytic_account_id AS analytic_account_id,
#                     so.team_id AS team_id
# 
#             FROM sale_order_line sol
#                     JOIN sale_order so ON (sol.order_id = so.id)
#                     JOIN stock_picking sp ON (so.name = sp.origin)
#                     LEFT JOIN product_product pro ON (sol.product_id = pro.id)
#                     JOIN res_partner rp ON (so.partner_id = rp.id)
#                     LEFT JOIN product_template pt ON (pro.product_tmpl_id = pt.id)
#                     LEFT JOIN product_pricelist pp ON (so.pricelist_id = pp.id)
#                     LEFT JOIN uom_uom u on (u.id = sol.product_uom)
#                     LEFT JOIN uom_uom u2 on (u2.id = pt.uom_id)
#             WHERE so.state in ('sale','done')
#         """
#         return so_str
# 
#     def _from(self):
#         return """(%s)""" % (self._so())
#     
#     def get_main_request(self):
#         request = """
#             CREATE or REPLACE VIEW %s AS
#                 SELECT id AS id,
#                     name,
#                     location_id,
#                     partner_id,
#                     product_id,
#                     product_tmpl_id,
#                     date_order,
#                     user_id,
#                     categ_id,
#                     company_id,
#                     price_total,
#                     price_unit,
#                     pricelist_id,
#                     analytic_account_id,
#                     state_id,
#                     country_id,
#                     team_id,
#                     price_subtotal,
#                     product_qty
#                 FROM %s
#                 AS foo""" % (self._table, self._from())
#         return request
#     
#     @api.model_cr
#     def init(self):
#         tools.drop_view_if_exists(self.env.cr, self._table)
#         self.env.cr.execute(self.get_main_request())


class InventoryInternalTransferInquiry(models.TransientModel):
    _name = 'inventoryinternaltransfer.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Inventory Internal Transfer'
    
    @api.depends(
        'date_from',
        'date_to',
        'create_uids',
        'write_uids',
        'product_ids',
        'location_ids',
        'location_dest_ids',
        'state'
    )
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                ('state', '=', line.state),
                ('picking_type_id.code', '=', 'internal'),
                ('date', '>=', line.date_from),
                ('date', '<=', line.date_to),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [product.id for product in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('location_id', 'in', [location.id for location in line.location_ids]) if line.location_ids else ('id', '!=', False),
                ('location_dest_id', 'in', [location.id for location in line.location_dest_ids]) if line.location_dest_ids else ('id', '!=', False),
            ])
            
    @api.depends('lines')
    def _get_pivot(self):
        super(InventoryInternalTransferInquiry, self)._get_pivot(
            rows=[
                'Source Location',
                'Product',
            ],
            cols=[
                'Destination Location',
                'Unit of Measure'
            ],
            aggregator='Sum',
            vals=['product_uom_qty']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('stock.move')
    
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    location_ids = fields.Many2many('stock.location', relation='location_id_inv_int_trans', column1='location_id', column2='inv_int_trans_inquiry_id',
                                    string='Source Location', domain=lambda self:self._get_domain('location_id'))
    location_dest_ids = fields.Many2many('stock.location', relation='location_dest_id_inv_int_trans', column1='location_dest_id', column2='inv_int_trans_inquiry_id',
                                         string='Destination Location', domain=lambda self:self._get_domain('location_dest_id'))
    state = fields.Selection([
        ('draft', 'New'),
        ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')
    ], string='Status', default='done', required=True)
    
    
class InventoryWHTransferInquiry(models.TransientModel):
    _name = 'inventorywhtransfer.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Inventory Warehouse Transfer'
    
    @api.depends(
        'date_from',
        'date_to',
        'create_uids',
        'write_uids',
        'product_ids',
        'location_ids',
        'location_dest_ids',
        'partner_ids',
        'state'
    )
    def _get_lines(self):
        sale_module = self.env['ir.module.module'].sudo().search([('name', '=', 'sale'), ('state', '=', 'installed')])
        purchase_module = self.env['ir.module.module'].sudo().search([('name', '=', 'purchase'), ('state', '=', 'installed')])
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                ('state', '=', line.state),
                ('picking_type_id.code', 'in', ['incoming', 'outgoing']),
                ('sale_line_id', '=', False) if sale_module else ('id', '!=', False),
                ('purchase_line_id', '=', False) if purchase_module else ('id', '!=', False),
                ('date', '>=', line.date_from),
                ('date', '<=', line.date_to),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [product.id for product in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('location_id', 'in', [location.id for location in line.location_ids]) if line.location_ids else ('id', '!=', False),
                ('location_dest_id', 'in', [location.id for location in line.location_dest_ids]) if line.location_dest_ids else ('id', '!=', False),
                ('partner_id', 'in', [partner.id for partner in line.partner_ids]) if line.partner_ids else ('id', '!=', False),
            ])
            
    @api.depends('lines')
    def _get_pivot(self):
        super(InventoryWHTransferInquiry, self)._get_pivot(
            rows=[
                'Source Location',
                'Product',
            ],
            cols=[
                'Destination Location',
                'partner_id',
                'Unit of Measure'
            ],
            aggregator='Sum',
            vals=['product_uom_qty']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('stock.move')
    
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    partner_ids = fields.Many2many('res.partner', string='Partner', domain=lambda self:self._get_domain('partner_id'))
    location_ids = fields.Many2many('stock.location', relation='location_id_inv_wh_trans', column1='location_id', column2='inv_wh_trans_inquiry_id',
                                    string='Source Location', domain=lambda self:self._get_domain('location_id'))
    location_dest_ids = fields.Many2many('stock.location', relation='location_dest_id_inv_wh_trans', column1='location_dest_id', column2='inv_wh_trans_inquiry_id',
                                         string='Destination Location', domain=lambda self:self._get_domain('location_dest_id'))
    state = fields.Selection([
        ('draft', 'New'),
        ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')
    ], string='Status', default='done', required=True)


class InventoryAdjustmentInquiry(models.TransientModel):
    _name = 'inventoryadjustment.inquiry'
    _inherit = 'inquiry.report'
    _description = 'Inventory Adjustment'
    
    @api.depends(
        'date_from',
        'date_to',
        'create_uids',
        'write_uids',
        'product_ids',
        'location_ids',
        'location_dest_ids',
        'state'
    )
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                ('state', '=', line.state),
                ('picking_type_id', '=', False),
                ('date', '>=', line.date_from),
                ('date', '<=', line.date_to),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
                ('product_id', 'in', [product.id for product in line.product_ids]) if line.product_ids else ('id', '!=', False),
                ('location_id', 'in', [location.id for location in line.location_ids]) if line.location_ids else ('id', '!=', False),
                ('location_dest_id', 'in', [location.id for location in line.location_dest_ids]) if line.location_dest_ids else ('id', '!=', False),
            ])
            
    @api.depends('lines', 'is_value')
    def _get_pivot(self):
        super(InventoryAdjustmentInquiry, self)._get_pivot(
            rows=[
                'Source Location',
                'Product',
            ],
            cols=[
                'Destination Location'
            ] if self.is_value else [
                'Destination Location',
                'Unit of Measure'
            ],
            aggregator='Sum',
            vals=['valuation'] if self.is_value else ['product_uom_qty']
        )
    
    name = fields.Char(default=_description)
    create_uids = fields.Many2many(relation='%s_create_uids_rel' % (_name.replace('.', '_')))
    write_uids = fields.Many2many(relation='%s_write_uids_rel' % (_name.replace('.', '_')))
    lines = fields.Many2many('stock.move')
    
    is_value = fields.Boolean('Valuation', default=lambda self:True)
    
    product_ids = fields.Many2many('product.product', string='Product', domain=lambda self:self._get_domain('product_id'))
    location_ids = fields.Many2many('stock.location', relation='location_id_inv_adjustment', column1='location_id', column2='inv_adjustment_inquiry_id',
                                    string='Source Location', domain=lambda self:self._get_domain('location_id'))
    location_dest_ids = fields.Many2many('stock.location', relation='location_dest_id_inv_adjustment', column1='location_dest_id', column2='inv_adjustment_inquiry_id',
                                         string='Destination Location', domain=lambda self:self._get_domain('location_dest_id'))
    state = fields.Selection([
        ('draft', 'New'),
        ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')
    ], string='Status', default='done', required=True)


class DevStockInventory(models.TransientModel):
    _name = 'dev.stock.inventory'
    _description = 'Dev Stock Inventory'
    _inherit = ['dev.stock.inventory', 'inquiry.abstract']
        
    
    def generate(self):
        self.result = """
        <div style="padding:16px;padding-top:0px;" id="result%s">
            <div style="text-align:center">
                <img src="/base_rmdoo/static/src/img/ajax-loader.gif"/>
            </div>
        </div>
        <script type="text/javascript">
        $(function () {
            $.get('/report/html/dev_stock_inventory_report.stock_inventory_template?options={"form":%s}', function (data) {
                data = data.substr(data.indexOf('<main class="container">') + 25, data.lastIndexOf('</main>'));
                $('#result%s').html(data);
                $('#result%s').focus();
            });
        });
        </script>
        """ % (self.id, self.id, self.id, self.id)
        self.is_result = True
        return True


class StockMoveClose(models.TransientModel):
    _name = 'stock.move.close'
    _description = 'Stock Move Closing'
    
    date = fields.Date('Closing Date', required=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super(StockMoveClose, self).default_get(fields_list)
        res['date'] = datetime.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        return res
    
    
    def do_close(self):
        if self.ensure_one():
            self.env['ir.rule'].browse(self.env.ref('base_rmdoo.stock_move_close').id).write({
                'domain_force':"[('date','>','%s'),('date_expected','>','%s')]" % (self.date, self.date)
            })
        return True

    
# class OpenAccountChart(models.TransientModel):
#     _name = 'account.open.chart'
#     _inherit = ['account.open.chart', 'inquiry.abstract']
#
#     name = fields.Char('Name', readonly=True, default='Chart of Account Hierarchy')
#
#     @api.model
#     def default_get(self, fields_list):
#         res = super(OpenAccountChart, self).default_get(fields_list)
#         res['date_from'], res['date_to'] = self._get_daterange(daterange='yearly')
#         return res
#
#     def get_plain_html(self, wiz_id):
#         lines = self.with_context(print_mode=True).get_pdf_lines(wiz_id)
#         user_context = self.browse(wiz_id)._build_contexts()
#         heading = self.env['res.company'].browse(user_context.get('company_id')).display_name
#         base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
#         rcontext = {
#             'mode': 'print',
#             'base_url': base_url,
#         }
#         user_context.update(rcontext)
#         self = self.with_context(user_context)
#         body = self.env['ir.ui.view'].render_template(
#             "account_parent.report_coa_heirarchy_print",
#             values=dict(
#                 rcontext,
#                 lines=lines,
#                 heading=heading,
#                 user_data=user_context,
#                 time=time,
#                 context_timestamp=lambda t: fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), t),
#                 report=self,
#                 context=self
#             ),
#         )
#
#         return body
#
#
#     def generate(self):
#         for record in self:
#             result = record.get_plain_html(record.id).decode('utf-8')
#             result = result[result.find('<main class="container">') + len('<main class="container">'):result.rfind('</main>')]
#             result = result[result.find('<main class="container">') + len('<main class="container">'):result.rfind('</main>')]
#             record.result = result
#             record.is_result = True
#         return True
