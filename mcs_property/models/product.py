from odoo import models, fields, api
import string
import random
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade')

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    is_property = fields.Boolean(track_visibility=True)

    product_id = fields.Many2one(
        'product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='cascade', check_company=True)  

    rent_price          = fields.Float(string="Rent. Price/m2")
    rent_price_month    = fields.Float(string="Price Monthly")
    service_charge_price          = fields.Float(string="Rent. Price/m2")
    service_charge_price_month    = fields.Float(string="Price Monthly")

class StockMove(models.Model):
    _inherit = 'stock.move'

    product_id = fields.Many2one(
        'product.product', 'Product',
        check_company=True,
        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", index=True, required=True,
        ondelete='cascade', states={'done': [('readonly', True)]})

# class ProductProduct(models.Model):
#     _inherit = 'product.product'

#     def name_get(self):
#         result = []
#         for record in self:
#             isDefault = True

#             if record.product_tmpl_id:
#                 product_tmpl_id = record.product_tmpl_id
#                 if product_tmpl_id.is_property is True:
#                     isDefault = False

#             if isDefault is False:
#                 name = record.name
#                 if record.product_tmpl_id:
#                     product_tmpl_id = record.product_tmpl_id
#                     name = product_tmpl_id.name
#                     if product_tmpl_id.parent_id and product_tmpl_id.is_property is True:
#                         if product_tmpl_id.is_contract_item is True:
#                             location_name = product_tmpl_id.location_id.name if product_tmpl_id.location_id is not False else ''
#                             property_space = product_tmpl_id.property_space if product_tmpl_id.property_space is not False else ''
#                             property_code = product_tmpl_id.property_code if product_tmpl_id.property_code is not False else ''

#                             name = '%s - %s - %s' % ((location_name), (property_space), (property_code))
#                         else:
#                             name = '%s / %s' % (product_tmpl_id.parent_id.name, product_tmpl_id.name)
#                 result.append((record.id, name))
#             else:
#                 # TDE: this could be cleaned a bit I think
#                 def _name_get(d):
#                     name = d.get('name', '')
#                     code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
#                     if code:
#                         name = '[%s] %s' % (code,name)
#                     return (d['id'], name)

#                 partner_id = self._context.get('partner_id')
#                 if partner_id:
#                     partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
#                 else:
#                     partner_ids = []
#                 company_id = self.env.context.get('company_id')

#                 # all user don't have access to seller and partner
#                 # check access and use superuser
#                 self.check_access_rights("read")
#                 self.check_access_rule("read")

#                 result = []

#                 # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
#                 # Use `load=False` to not call `name_get` for the `product_tmpl_id`
#                 self.sudo().read(['name', 'default_code', 'product_tmpl_id'], load=False)

#                 product_template_ids = self.sudo().mapped('product_tmpl_id').ids

#                 if partner_ids:
#                     supplier_info = self.env['product.supplierinfo'].sudo().search([
#                         ('product_tmpl_id', 'in', product_template_ids),
#                         ('name', 'in', partner_ids),
#                     ])
#                     # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
#                     # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
#                     supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
#                     supplier_info_by_template = {}
#                     for r in supplier_info:
#                         supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
#                 for product in self.sudo():
#                     variant = product.product_template_attribute_value_ids._get_combination_name()

#                     name = variant and "%s (%s)" % (product.name, variant) or product.name
#                     sellers = []
#                     if partner_ids:
#                         product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
#                         sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
#                         if not sellers:
#                             sellers = [x for x in product_supplier_info if not x.product_id]
#                         # Filter out sellers based on the company. This is done afterwards for a better
#                         # code readability. At this point, only a few sellers should remain, so it should
#                         # not be a performance issue.
#                         if company_id:
#                             sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
#                     if sellers:
#                         for s in sellers:
#                             seller_variant = s.product_name and (
#                                 variant and "%s (%s)" % (s.product_name, variant) or s.product_name
#                                 ) or False
#                             mydict = {
#                                     'id': product.id,
#                                     'name': seller_variant or name,
#                                     'default_code': s.product_code or product.default_code,
#                                     }
#                             temp = _name_get(mydict)
#                             if temp not in result:
#                                 result.append(temp)
#                     else:
#                         mydict = {
#                                 'id': product.id,
#                                 'name': name,
#                                 'default_code': product.default_code,
#                                 }
#                         result.append(_name_get(mydict))
#         return result

class Product(models.Model):
    _inherit = 'product.template'

    # def name_get(self):
    #     isDefault = True
    #     result = []

    #     for record in self:
    #         product_tmpl_id = record
    #         if product_tmpl_id.is_property is True:
    #             isDefault = False

    #         if isDefault is False:
    #             name = record.name
    #             if record.parent_id and record.is_property is True:
    #                 if record.is_contract_item is True:
    #                     location_name = record.location_id.name if record.location_id is not False else ''
    #                     property_space = record.property_space if record.property_space is not False else ''
    #                     property_code = record.property_code if record.property_code is not False else ''

    #                     name = '%s - %s - %s' % ((location_name), (property_space), (property_code))
    #                 else:
    #                     name = '%s / %s' % (record.parent_id.name, record.name)
    #             result.append((record.id, name))
    #         else:
    #             product = self.env['product.product'].search([('product_tmpl_id', '=', record.id)], limit=1)
    #             result.append((record.id, 'product.name'))

    #     return result

    version = fields.Integer()

    old_product_id = fields.Many2one('product.template')

    is_property = fields.Boolean(track_visibility=True)

    is_contract_item = fields.Boolean(track_visibility=True, string="Is Unit")

    revenue_sharing_or_minimum_rental = fields.Float(string="Minimum Rental / Revenue Sharing")
    revenue_sharing_plus_minimum_rental = fields.Float(string="Minimum Rental + Revenue Sharing")
    revenue_sharing = fields.Float(string="Reveue Sharing")
    minimum_rental = fields.Float(string="Minimum Rental", related='contract_price')

    @api.onchange('parent_id')
    def _get_lat_long_parent(self):
        for record in self:
            if record.is_property is True:
                record.latitude = record.parent_id.latitude
                record.longitude = record.parent_id.longitude
                if record.parent_id.location_id:
                    record.location_id = record.parent_id.location_id.id
        
    available           = fields.Boolean(track_visibility=True)
    recurring_type      = fields.Selection([('Harian', 'Harian'), ('Bulanan', 'Bulanan'), ('Tahunan', 'Tahunan')], default='Bulanan',track_visibility=True)
    recurring_value     = fields.Integer(default=1)

    # ===== BRATA
    space_rent_out      = fields.Integer(string="Rent. Out/m2")
    rent_price          = fields.Float(string="Rent. Price/m2")
    rent_price_month    = fields.Float(string="Price Monthly")
    service_charge_price          = fields.Float(string="Rent. Price/m2")
    service_charge_price_month    = fields.Float(string="Price Monthly")

    @api.onchange('total_large','rent_price','service_charge_price')
    def _onchange_price(self):
        if self.category == 'Property':
            self.rent_price_month           = self.rent_price*self.total_large
            self.service_charge_price_month = self.service_charge_price*self.total_large
            self.contract_price             = self.rent_price_month + self.service_charge_price_month
    # ===========

    tenant_large    = fields.Float(track_visibility=True)
    latitude        = fields.Float(string='Geo Latitude', digits=(16, 5), track_visibility=True)
    longitude = fields.Float(string='Geo Longitude', digits=(16, 5), track_visibility=True)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', track_visibility=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]", track_visibility=True)
    city = fields.Char(track_visibility=True)
    zip = fields.Char(change_default=True, track_visibility=True)
    street = fields.Char(track_visibility=True)
    street2 = fields.Char(track_visibility=True)

    existing_product = fields.Selection([
        ('','Existing'),
        ('Historical','Historical'),
    ])

    historical_product_id = fields.Many2one('product.template')

    service_uom_id = fields.Many2one('uom.uom', 'Service Unit of Measure', track_visibility=True)

    location_id = fields.Many2one('mcs_property.location', store='True', string="Location")


    # ===== hs 
    # 22 01 24
    # onchange to triggering property name changes
    @api.onchange('have_parent', 'parent_id', 'category', 'is_contract_item', 'location_id', 'property_space', 'property_code')
    def _change_property_name(self):
        for record in self:
            if record.category == 'Property' and record.is_contract_item == True:
                record.property_space = record.parent_id.name
                record.name = "%s / %s / %s " % (record.location_id.name or "Location Name", record.property_space or "Space", record.property_code or "Code")
    # ======


    def _default_uom(self):
        uom = self.env['uom.uom'].search(
            [('name', '=', 'm2')], limit=1)
        return uom.id

    total_large = fields.Float('Total Space/m2')
    total_large_uom_id = fields.Many2one('uom.uom', 'Unit', track_visibility=True, default=_default_uom)

    # total_large_available = fields.Float('Space Available/m2', compute='_get_total_large_available')
    total_large_available = fields.Float('Space Available/m2', min=0)

    total_large_available_text = fields.Char('Total Large Available', compute='_get_total_large_available_text')
    total_large_rent = fields.Float('Rent. Out/m2', compute='_get_total_large_rent')
    total_large_child = fields.Float('Total Large Child', compute='_get_total_large_child')

    total_tenant = fields.Float('Total Space')
    total_tenant_available = fields.Float('Total Space Available')
    total_tenant_rent = fields.Float('Total Space Rented')
    
    def _get_total_tenant_available(self):
        for record in self:
            record.total_tenant_available = record.total_tenant - record.total_tenant_rent
    
    is_child = fields.Float('Is Child', compute='_get_is_child')
    is_parent = fields.Float('Is Parent', compute='_get_is_parent')

    have_parent = fields.Boolean('Have Parent')
        
    @api.depends('parent_id')
    def _set_have_parent(self):
        for product in self:
            if product.parent_id is not False:
                product.have_parent = True
    
    def _get_is_child(self):
        for record in self:
            record.is_child = True if len(record.child_ids) <= 0 else False
    
    def _get_is_parent(self):
        for record in self:
            record.is_parent = True if len(record.child_ids) > 0 else False
    
    total_childs = fields.Boolean(compute='_compute_total_childs')
    
    contract_price = fields.Float('Price')
    contract_price_uom_id = fields.Many2one('uom.uom', 'Unit', track_visibility=True, default=_default_uom)

    category = fields.Selection([
        ('Property','Property'),
        ('Service','Service'),
        ('Jaminan','Jaminan'),
    ], string="Product Type", track_visibility=True)

    parent_id = fields.Many2one('product.template', domain="[('is_property', '=', True)]")
    child_ids = fields.One2many('product.template', inverse_name='parent_id')

    parent_code = fields.Char()
    parent_level = fields.Integer()
    parent_scheme = fields.Char()

    parent_root_id = fields.Many2one('product.template', domain="[('is_property', '=', True),('parent_id', '=', False)]")
    child_root_ids = fields.One2many('product.template', inverse_name='parent_root_id')
    
    property_code = fields.Char(string="Code")
    property_space = fields.Char(string="Space")
    
    total_large_parent = fields.Float('Total Large Parent', compute='_get_total_large_parent')
    total_large_available_parent = fields.Float('Total Large Parent Available', compute='_get_total_large_available_parent')
    total_large_rent_parent = fields.Float('Total Large Parent Rented', compute='_get_total_large_rent_parent')

    childs_products_count = fields.Integer('Sub Products Count', compute='_get_childs_products_count')

    contract_state = fields.Char(compute="_compute_contract_state", string="Contract Status")

    def _compute_contract_state(self):
        for record in self:
            if record.is_contract_item is True:
                if record.available:
                    record.contract_state = 'Available'
                else:
                    record.contract_state = 'Rented'
            else:
                record.contract_state = ''

    @api.onchange('parent_id')
    def _get_total_large_parent(self):
        for record in self:
            record.total_large_parent = record.parent_id.total_large

    @api.onchange('parent_id')
    def _get_total_large_available_parent(self):
        for record in self:
            record.total_large_available_parent = record.parent_id.total_large_available

    @api.onchange('parent_id')
    def _get_total_large_rent_parent(self):
        for record in self:
            record.total_large_rent_parent = record.parent_id.total_large_rent

    def _compute_price_monthly(self):
        for record in self:
            record.price_monthly = 30 * record.price_per_m2

    def _compute_total_childs(self):
        for record in self:
            record.total_childs = len(record.child_ids)

    def _get_childs_products_count(self):
        for record in self:
            record.childs_products_count = self.env['product.template'].search_count([('parent_id', '=', record.id), ('is_property', '=', True)])

    def _get_total_large_available(self):
        for record in self:
            record.total_large_available = record.total_large - record.total_large_child - record.total_large_rent

    def _get_total_large_available_text(self):
        for record in self:
            if record.total_large_uom_id:
                record.total_large_available_text = "%s %s" % (record.total_large_available, record.total_large_uom_id.name)
            else:
                record.total_large_available_text = "%s" % (record.total_large_available)

    def _get_total_large_rent(self):
        for record in self:
            total_large_rent = 0
            record.total_large_rent = total_large_rent

    def _get_total_large_child(self):
        for record in self:
            total_large_child = 0
            
            product_parent = self.env['product.template'].search([('parent_id', '=', record.id)])

            for product in product_parent:
                total_large_child += product.total_large

            record.total_large_child = total_large_child

    def action_childs_products(self):
        self.ensure_one()
        return {
            'name': 'Sub Products',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'domain': [('parent_id', '=', self.id), ('is_property', '=', True)],
            'context': {'default_parent_id': self.id, 'default_have_parent': True, 'default_is_property': True, 'default_location_id': self.location_id.id},
        } 
    
    @api.model
    def create(self, vals): 
        if 'is_property' in vals and vals['is_property'] is True:
            parent_level = 1
            parent_code = ''.join(random.sample(string.ascii_uppercase, 5))

            if 'have_parent' in vals and vals['have_parent'] is False:
                vals['parent_id'] = False

            if 'parent_id' in vals:
                product_parent = self.env['product.template'].search([('id', '=', vals['parent_id'])], limit=1)

                # if product_parent:
                #     if vals['total_large'] > product_parent.total_large_available:
                #         raise UserError("Total large melebihi total large available parent (%s m2)." % (product_parent.total_large_available))

            if product_parent:
                if product_parent.parent_root_id:
                    vals['parent_root_id'] = product_parent.parent_root_id.id
                else:
                    vals['parent_root_id'] = product_parent.id

                parent_level = product_parent.parent_level + 1
                parent_scheme = product_parent.parent_scheme + '.' + parent_code
            else:
                parent_scheme = parent_code

            if 'is_contract_item' in vals and vals['is_contract_item'] is False:
                vals['available'] = False
                vals['recurring_type'] = False
                vals['contract_price'] = False
                vals['contract_price_uom_id'] = False

            vals['parent_code'] = parent_code
            vals['parent_level'] = parent_level
            vals['parent_scheme'] = parent_scheme
            
            vals['version'] = 1

        return super(Product, self).create(vals)

    def write(self, vals):
        if 'is_property' in vals and vals['is_property'] is True:
            if 'version' in vals:
                if vals['version'] is False:
                    vals['version'] = 1
            else:
                vals['version'] = 1

            if 'is_contract_item' in vals and vals['is_contract_item'] is False:
                vals['available'] = False
                vals['recurring_type'] = False
                vals['contract_price'] = False
                vals['contract_price_uom_id'] = False

            if 'have_parent' in vals and vals['have_parent'] is False:
                vals['parent_id'] = False

            if 'parent_id' in vals:
                product_parent = self.env['product.template'].search([('id', '=', vals['parent_id'])], limit=1)
                
                if product_parent:
                    if product_parent.parent_root_id:
                        vals['parent_root_id'] = product_parent.parent_root_id.id
                    else:
                        vals['parent_root_id'] = product_parent.id

                    vals['parent_level'] = product_parent.parent_level + 1
                    vals['parent_scheme'] = product_parent.parent_scheme + '.' + vals['parent_code']
                    if 'total_large' in vals:
                        if vals['total_large'] > product_parent.total_large_available:
                            raise UserError("Total large melebihi total large available parent (%s m2)." % (product_parent.total_large_available))

        return super(Product, self).write(vals)

    def fixing_parent_root(self):
        products = self.env['product.template'].search([('is_property', '=', True)])
        for rec in products:
            if rec.parent_id:
                parent_code = rec.parent_scheme.split('.')[0]
                product_parent = self.env['product.template'].search([('parent_code', '=', parent_code)], limit=1)
                if product_parent:
                    rec.parent_root_id = product_parent.id
            else:
                rec.parent_root_id = False

    @api.onchange('total_large')
    def onchange_total_large(self):
        for values in self:
            total_child = self.env['product.template'].search_count([('parent_id', '=', values.id)])
            
            if total_child <= 0:
                values.total_large_available = values.total_large