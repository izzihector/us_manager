from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from collections import OrderedDict

def write_roman(num):

    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])

romawi = {
    0: '',
    1: 'I',
    2: 'II',
    3: 'III',
    4: 'IV',
    5: 'V',
    6: 'VI',
    7: 'VII',
    8: 'VIII',
    9: 'IX',
    10: 'X',
    11: 'XI',
    12: 'XII',
}

bulan_name_arr = {
    0: '',
    1: 'Januari',
    2: 'Februari',
    3: 'Maret',
    4: 'April',
    5: 'Mei',
    6: 'Juni',
    7: 'Juli',
    8: 'Agustus',
    9: 'September',
    10: 'Oktober',
    11: 'November',
    12: 'Desember',
}

class Sequence(models.Model):
    _name = 'mcs_property.sequence'

    name = fields.Char()
    number = fields.Integer()

class LostReason(models.Model):
    _name = 'mcs_property.lost_reason'

    name = fields.Char()

class Orders(models.Model):
    _inherit = ['sale.order']
    
    def action_confirm_property(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'date_order': fields.Datetime.now()
        })

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True


    hide = fields.Boolean()

    is_property = fields.Boolean(track_visibility=True)
    contract_id = fields.Many2one('mcs_property.contract',track_visibility=True)
    contract_state = fields.Selection([
        ('', ''),
        ('0', 'Draft'),
        ('10', 'Confirm'),
        ('20', 'Approve'),
        ('30', 'Running'),
        ('40', 'Expired'),
        ('50', 'Closed'),
    ], string='Contract Status', readonly=True, index=True, tracking=3, default='')
    contract_category = fields.Char()

    recurring_type = fields.Selection([('Harian', 'Harian'), ('Bulanan', 'Bulanan'), ('Tahunan', 'Tahunan')],
                                               track_visibility=True)
    recurring_value = fields.Integer()

    recurring_month = fields.Char()
    recurring_year = fields.Char()
    
    recurring_active = fields.Boolean()

    recurring_month_display = fields.Char('Recurring Month')
    # recurring_month_display = fields.Char('Recurring Month', compute="_recurring_month_display")

    def _recurring_month_display(self):
        for rec in self:
            if rec.recurring_month:
                rec.recurring_month_display = bulan_name_arr[int(rec.recurring_month)]

    @api.model
    def create(self, vals):
        record = super(Orders, self).create(vals)

        if record.is_property is True:
            if record.recurring_active is True:
                record.contract_id.acive_sale_order_id = record.id

        return record

class Contract(models.Model):
    _name = 'mcs_property.contract'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Contract"

    adendum_version = fields.Integer()

    invoice_count = fields.Integer('Trial/ Meeting Count', compute='_get_invoice_count')
    sale_order_count = fields.Integer('Trial/ Meeting Count', compute='_get_sale_order_count')

    riwayat_penagihan_ids = fields.One2many('mcs_property.contract.riwayat_penagihan', 'contract_id')

    product_location_id = fields.Many2one('mcs_property.location', string='Location')
    product_parent_id = fields.Many2one('product.template', string='Location', domain="[('is_property', '=', True), ('parent_id', '=', False)]", change_default=True, ondelete='cascade', check_company=True)

    def cronjob_notif_tagihan(self):
        time_now = date.today()

        contracts = self.env['mcs_property.contract'].sudo().search([
                ('state', '=', '30'),
                ('warning_date', '<=', time_now),
                ('end_date', '>=', time_now)
            ])
        
        for contract in contracts:
            notification_ids = list()
            notification_ids.append((0, 0, {'res_partner_id':contract.partner_id.id, 'notification_type':'inbox'}))

            message = _(""" Kontrak <b>""" + contract.name + """</b> dalam masa penagihan!! Kontrak akan berakhir sebelum %s.""") % (contract.end_date)

            contract.sudo().message_post(body=message, message_type='notification', subtype='mail.mt_comment', notification_ids=notification_ids) 

            self.env['mcs_property.contract.riwayat_penagihan'].create({
                                    'contract_id': contract.id,
                                    'name': message,
                                })
        
        for contract in contracts:
            notification_ids = list()
            notification_ids.append((0, 0, {'res_partner_id':contract.create_uid.partner_id.id, 'notification_type':'inbox'}))

            message = _(""" Tagihan kontrak <b>""" + contract.name + """</b> sudah dikirimkan!! Kontrak akan berakhir sebelum %s.""") % (contract.end_date)

            contract.sudo().message_post(body=message, message_type='notification', subtype='mail.mt_comment', notification_ids=notification_ids) 
        
    def _get_invoice_count(self):
        for record in self:
            record.invoice_count = self.env['sale.order'].search_count([('contract_id', '=', record.id)])

    def open_invoices(self):
        return False

    def _get_sale_order_count(self):
        for record in self:
            record.sale_order_count = self.env['sale.order'].search_count([('contract_id', '=', record.id), ('hide', '=', False)])

    def open_sale_orders(self):
        self.ensure_one()
        return {
            'name': 'Sale orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('contract_id', '=', self.id), ('hide', '=', False)],
            'context': {'default_contract_id': self.id},
        }

    @api.model
    def create(self, vals):
        vals['state'] = '0'
        return  super(Contract, self).create(vals)

    def write(self, vals):
        state = ''
        is_cancel = ''
        for rec in self:
            state = rec.state
            is_cancel = rec.is_cancel
        
        if state == '' and is_cancel is True:
            raise ValidationError("You're not allowed to edit this record")
        
        return super(Contract, self).write(vals)

    def _default_validity_date(self):
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days'):
            days = self.env.company.quotation_validity_days
            if days > 0:
                return fields.Date.to_string(datetime.now() + timedelta(days))
        return False

    @api.model
    def _default_note(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'account.use_invoice_terms') and self.env.company.invoice_terms or ''

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.uid
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param(
                'account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        self.update(values)

    name = fields.Char(string='Contract Number', required=True, readonly=True, index=True,
                       default=lambda self: _('Draft'))
    real_name = fields.Char(string='Contract Number', readonly=True)

    state = fields.Selection([
        ('', ''),
        ('0', 'Draft'),
        ('10', 'Confirm'),
        ('20', 'Approve'),
        ('30', 'Running'),
        ('40', 'Expired'),
        ('50', 'Closed'),
    ], string='Contract Status', readonly=True, index=True, tracking=3, default='')

    state_name = fields.Char(string='Contract Status', compute="_compute_state_name")

    def _compute_state_name(self):
        for rec in self:
            state_name = ''

            if rec.state == '0':
                state_name = 'Draft'
            elif rec.state == '10':
                state_name = 'Confirm'
            elif rec.state == '20':
                state_name = 'Approve'
            elif rec.state == '30':
                state_name = 'Running'
            elif rec.state == '40':
                state_name = 'Expired'
            elif rec.state == '50':
                state_name = 'Closed'

            if rec.is_cancel_requested is True:
                state_name = 'Request Cancel'
            elif rec.is_cancel is True:
                state_name = 'Cancel'

            if rec.is_wanprestasi is True:
                state_name = 'Wanprestasi'

            rec.state_name = state_name

    # domain_by_user = fields.Boolean(compute="_compute_domain_by_user")
    
    # def _compute_domain_by_user(self):
    #     for rec in self:
    #         if rec.name == 'Add-VII-22/DIREKSI/Perj./X/2021':
    #             rec.domain_by_user = True
    #         else:
    #             rec.domain_by_user = False

    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user,
        domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)])

    approved_by = fields.Many2one('res.users')
    approved_at = fields.Datetime()
        
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, index=True, tracking=True, domain=[('is_property', '=', True)])
    partner_npwp = fields.Char(related="partner_id.npwp")
    partner_phone = fields.Char(related="partner_id.phone")
    partner_mobile = fields.Char(related="partner_id.mobile")
    partner_email = fields.Char(related="partner_id.email")

    lost_reason = fields.Many2one('mcs_property.lost_reason', string="Cancellation Reason")
    lost_reason_detail = fields.Text()

    is_cancel = fields.Boolean()
    is_cancel_requested = fields.Boolean() # request pembatalan
    
    @api.onchange('contract_line_ids', 'contract_line_ids.include_in_total', 'contract_line_ids.price_total')
    def _compute_amount(self):
        for rec in self:
            price_total= 0
            contract_recurring_value = rec.contract_recurring_value
            for line in rec.contract_line_ids:
                if line.include_in_total:
                    price_total += line.price_total

                    if line.product_id.category == "Property":
                        contract_recurring_value = line.recurring_value

            rec.price_total = price_total
            rec.contract_recurring_value = contract_recurring_value

    price_total = fields.Monetary(compute='_compute_amount', string='Contract Price')
    
    def submit_cancel(self):
        self.is_cancel_requested = True

    def do_confirm_cancel(self):
        self.state = ''
        self.is_cancel = True

    def do_deny_cancel(self):
        self.state = '0'
        self.is_cancel_requested = False
        
        return {
            'name': 'Contract',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mcs_property.contract',
        }

    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Address',
        readonly=False, required=True,
        states={'0': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]}, )
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', readonly=False, required=True,
        states={'0': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]}, )

    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'0': [('readonly', False)], 'sent': [('readonly', False)]},
                                 default=fields.Datetime.now,
                                 help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    validity_date = fields.Date(string='Expiration', readonly=True,
                                states={'0': [('readonly', False)], 'sent': [('readonly', False)]},
                                default=_default_validity_date)
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', check_company=True, )

    contract_time = fields.Integer(track_visibility=True, string="Contract Day")
    start_date = fields.Date(track_visibility=True, required=True)
    end_date = fields.Date(track_visibility=True)
    warning_date = fields.Date(track_visibility=True, required=True)
    reminder = fields.Integer(track_visibility=True)
    
    contract_recurring_type = fields.Selection([('Harian', 'Harian'), ('Bulanan', 'Bulanan'), ('Tahunan', 'Tahunan')],
                                               track_visibility=True, string="Recurring Type", required=True)
    contract_recurring_value = fields.Integer(string="Recurring Value", required=True, default=0) 

    document_properties = fields.One2many(comodel_name='mcs_property.document_properties', string="Document Properties",
                                          inverse_name='contract_id')

    contract_line_ids = fields.One2many('mcs_property.contract.line', 'contract_id', string='Contract Lines',
                                        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},
                                        copy=True,
                                        auto_join=True)

    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True, readonly=True,
        states={'0': [('readonly', False)], 'sent': [('readonly', False)]},
        help="If you change the pricelist, only newly added lines will be affected.")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    note = fields.Text('Terms and conditions', default=_default_note)

    contract_active = fields.Boolean(string="Contract Active", readonly=True)

    can_extend = fields.Boolean(compute="_compute_can_extend")
    can_adendum = fields.Boolean(compute="_compute_can_adendum")

    so_security_deposit_id = fields.Many2one('sale.order', ondelete='cascade', index=True)

    is_security_deposit_required = fields.Boolean(compute="_compute_security_deposit_required")

    can_approve_wanprestasi = fields.Boolean(compute="_compute_can_approve_wanprestasi")

    def _compute_can_approve_wanprestasi(self):
        for rec in self:
            can_approve_wanprestasi = False

            if rec.is_wanprestasi_requested is True and rec.is_wanprestasi is False:
                can_approve_wanprestasi = True

            rec.can_approve_wanprestasi = can_approve_wanprestasi

    can_selesai = fields.Boolean(compute="_compute_can_selesai")

    def _compute_can_selesai(self):
        for rec in self:
            can_selesai = False

            if rec.state == '30' and rec.is_wanprestasi is False:
                can_selesai = True

            rec.can_selesai = can_selesai

    def _compute_security_deposit_required(self):
        for rec in self:
            is_security_deposit_required = False

            if rec.state == '20':
                is_security_deposit_paid = True

                if len(rec.so_security_deposit_id.invoice_ids)>0:
                    for a in rec.so_security_deposit_id.invoice_ids:
                        if is_security_deposit_paid is True:
                            if a.invoice_payment_state != 'paid':
                                is_security_deposit_paid = False
                else:
                    is_security_deposit_paid = False

                if is_security_deposit_paid is False:
                    is_security_deposit_required = True

            rec.is_security_deposit_required = is_security_deposit_required

    is_cancel_requested_required = fields.Boolean(compute="_compute_is_cancel_requested_required")

    def _compute_is_cancel_requested_required(self):
        for rec in self:
            is_cancel_requested_required = False

            if rec.is_cancel_requested == True and rec.is_cancel == False:
                is_cancel_requested_required = True

            rec.is_cancel_requested_required = is_cancel_requested_required

    is_extended = fields.Boolean()
    is_adendum_ok = fields.Boolean()

    contract_type = fields.Selection([('New', 'New'), ('Extend', 'Extend'), ('Adendum', 'Adendum'), ('Historical', 'Historical')],
                                               track_visibility=True, string="Contract Type", required=True, default="New")

    new_start_date = fields.Date(store=False)
    new_end_date = fields.Date(store=False)

    onchange_contract_id = fields.Many2one('mcs_property.contract', string='Kontrak Lama', ondelete='cascade', index=True)

    extended_contract_id = fields.Many2one('mcs_property.contract', string='Kontrak Lama', ondelete='cascade', index=True)
    extend_contract_id = fields.Many2one('mcs_property.contract', string='Kontrak Perpanjangan', ondelete='cascade', index=True)

    historical_contract_id = fields.Many2one('mcs_property.contract', string='Kontrak Lama', ondelete='cascade', index=True)
    adendum_contract_id = fields.Many2one('mcs_property.contract', string='Kontrak Adendum', ondelete='cascade', index=True)
    
    acive_sale_order_id = fields.Many2one('sale.order', string='SO Aktif', ondelete='cascade', index=True)

    def submit_extend(self):
        new_contract = self.copy()

        self.is_extended = True
        self.extend_contract_id = new_contract.id

        new_contract.name = 'Draft'
        new_contract.state = '0'
        new_contract.start_date = self.new_start_date
        new_contract.end_date = self.new_end_date
        new_contract.contract_type = "Extend"
        new_contract.extended_contract_id = self.id
        new_contract.acive_sale_order_id = False
        new_contract.so_security_deposit_id = False

    def _compute_can_extend(self):
        for rec in self:
            today = date.today()
            min_date = rec.warning_date

            can_extend = False

            if min_date is not False:
                if today > min_date and rec.is_extended is False and rec.state in ['30', '40'] and rec.is_wanprestasi is False:
                    can_extend = True
            
            rec.can_extend = can_extend

    def _compute_can_adendum(self):
        for rec in self:
            today = date.today()
            min_date = rec.warning_date

            can_adendum = False

            if min_date is not False:
                if rec.is_adendum_ok is False and rec.is_extended is False and rec.state in ['30', '40'] and rec.is_wanprestasi is False:
                    can_adendum = True
            
            rec.can_adendum = can_adendum

    def _compute_warning_date(self):
        for rec in self:
            contract_recurring_type = rec.contract_recurring_type
            contract_recurring_value = rec.contract_recurring_value

            month_day_total = 30
            year_day_total = 365

            is_tahun_kabisat = False
            year = rec.start_date.year
            if year % 4 == 0:
                is_tahun_kabisat = True

            if is_tahun_kabisat is True:
                year_day_total = 366
            
            day = contract_recurring_value
            if contract_recurring_type == 'Bulanan':
                day = contract_recurring_value * month_day_total
            elif contract_recurring_type == 'Tahunan':
                day = contract_recurring_value * year_day_total

            end_date = rec.end_date
            today = date.today()

            warning_date = False

            if end_date:
                warning_date = end_date -  timedelta(days=day)

            rec.warning_date = warning_date

    def unlink(self):
        for contract_line_id in self.contract_line_ids:
            if contract_line_id.product_id.category == 'Property':
                contract_line_id.product_id.available = True
                contract_line_id.product_id.total_large_available = contract_line_id.product_id.space_rent_out
                contract_line_id.product_id.space_rent_out = 0

        return super(Contract, self).unlink()

    def do_clear_sequence(self):
        self.env['mcs_property.sequence'].search([(1, '=', 1)]).unlink()
    
    def do_adendum(self):
        self.ensure_one()
        return {
            'name': 'Adendum Kontrak',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.addendum',
        }

    def submit_addendum(self):
        sale_orders = self.env['sale.order'].search([('contract_id', '=', self.id)])

        so_prop_ids = list()
        so_prop_paid_ids = list()
        
        for sale_order in sale_orders:
            if sale_order.contract_category == 'Property':
                so_prop_ids.append(sale_order.id)
                
                is_paid = True

                if len(sale_order.invoice_ids)>0:
                    for a in sale_order.invoice_ids:
                        if is_paid is True:
                            if a.invoice_payment_state != 'paid':
                                is_paid = False
                else:
                    is_paid = False

                if is_paid is True:
                    so_prop_paid_ids.append(sale_order.id)
        
        so_prop_paid_count = len(so_prop_paid_ids)

        for sale_order in sale_orders:
            sale_order.contract_id = False

        new_contract = self.copy({'create_uid': self.create_uid})

        if self.adendum_version > 0:
            new_contract.adendum_version += 1
        else:
            self.real_name = self.name
            new_contract.real_name = self.name
            new_contract.adendum_version = 1

        new_contract.name = 'Add-' + write_roman(new_contract.adendum_version) + '-' + new_contract.real_name

        new_contract.contract_type = 'Adendum'
        new_contract.historical_contract_id = self.id
        new_contract.state = '0'
        new_contract.acive_sale_order_id = False
        new_contract.so_security_deposit_id = False

        if new_contract.contract_recurring_type == 'Harian':
            raise UserError("Adendum tidak tersedia di kontrak harian")
            new_contract.contract_recurring_value = new_contract.contract_recurring_value + relativedelta(months=so_prop_paid_count)

        elif new_contract.contract_recurring_type == 'Bulanan':
            new_contract.contract_recurring_value = new_contract.contract_recurring_value - so_prop_paid_count

        elif new_contract.contract_recurring_type == 'Tahunan':
            new_contract.contract_recurring_type = 'Bulanan'
            new_contract.contract_recurring_value = (12 * new_contract.contract_recurring_value) - so_prop_paid_count

        new_contract.start_date = new_contract.start_date + relativedelta(months=so_prop_paid_count)

        for contract_line_id in new_contract.contract_line_ids:
            old_product_template = contract_line_id.product_template_id

            if old_product_template.category == 'Property' and old_product_template.is_contract_item is True:
                old_product_template.existing_product = 'Historical'
                old_product_template.active = False

                new_name = old_product_template.name

                new_product_template = old_product_template.copy()
                new_product_template.name = new_name
                
                new_product_template.existing_product = ''
                new_product_template.active = True

                new_product_template.historical_product_id = old_product_template.id
                new_product_template.version = old_product_template.version + 1
            
                new_product = self.env['product.product'].search([('product_tmpl_id', '=', new_product_template.id)], limit=1)
                new_product.name = new_name
                contract_line_id.product_id = new_product.id

                if contract_line_id.recurring_type == 'Harian':
                    raise UserError("Adendum tidak tersedia di kontrak harian")
                    
                elif contract_line_id.recurring_type == 'Bulanan':
                    contract_line_id.recurring_value = contract_line_id.recurring_value - so_prop_paid_count

                elif contract_line_id.recurring_type == 'Tahunan':
                    # raise UserError("Bug addendum recurring type tahunan")
                    contract_line_id.recurring_type = 'Bulanan'
                    contract_line_id.recurring_value = (12 * contract_line_id.recurring_value) - so_prop_paid_count

        self.contract_type = 'Historical'
        self.adendum_contract_id = new_contract.id
        self.is_adendum_ok = True
        
        for sale_order in sale_orders:
            sale_order.contract_id = self.id

    def do_confirm(self):
        self.ensure_one()
        haveProp = False
        haveSecureDepo = False
        for a in self.contract_line_ids:
            if a.product_id.category == 'Property':
                haveProp = True
            if a.product_id.category == 'Jaminan':
                haveSecureDepo = True
        if haveProp is False:
            raise UserError("Harus ada product property")
        if haveSecureDepo is False:
            raise UserError("Harus ada security deposit")

        return {
            'name': 'Konfirmasi Kontrak',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.confirm',
        }
    
    def submit_confirm(self):
        self.state = '10'
            
        if self.name == 'Draft': 
            sequence_number = 1
            sequence = self.env['mcs_property.sequence'].search([('name', '=', 'mcs_property.contract')], limit=1)
            if sequence:
                sequence_number = sequence.number + 1
                sequence.number = sequence_number
            else:
                sequence = self.env['mcs_property.sequence'].create({'name': 'mcs_property.contract', 'number': 1})

            
            # bulan_romawi = romawi[datetime.now().month]
            bulan_romawi = write_roman(datetime.now().month)
            
            tahun = datetime.now().year

            contract_number = "%s/DIREKSI/Perj./%s/%s" % (sequence_number, bulan_romawi, tahun)

            self.name = contract_number

    def do_cancel(self):
        self.ensure_one()
        return {
            'name': 'Contract Cancellation Reason',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.lost.reason',
        }

    def do_extend(self):
        self.ensure_one()
        
        contract_recurring_type = self.contract_recurring_type
        contract_recurring_value = self.contract_recurring_value

        month_day_total = 30
        year_day_total = 365

        is_tahun_kabisat = False
        year = self.start_date.year
        if year % 4 == 0:
            is_tahun_kabisat = True

        if is_tahun_kabisat is True:
            year_day_total = 366
                
        day = contract_recurring_value
        if contract_recurring_type == 'Bulanan':
            day = contract_recurring_value * month_day_total
        elif contract_recurring_type == 'Tahunan':
            day = contract_recurring_value * year_day_total

        start_date = self.end_date + timedelta(days=1)
        end_date = start_date + timedelta(days=day - 1) 

        return {
            'name': 'Perpanjangan Kontrak',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.extend',
            'context': {'default_start_date': start_date, 'default_end_date': end_date},
        }

    def do_approve(self):
        self.ensure_one()
        return {
            'name': 'Approve Kontrak',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.approve',
        }

    def do_approve_denied(self):
        self.ensure_one()
        return {
            'name': 'Approve Denied Kontrak',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.approve.denied',
        }

    def ask_surat_peringatan(self):
        self.ensure_one()
        return {
            'name': 'Surat Peringatan Kontrak',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.surat_peringatan',
        }

    def ask_surat_peringatan_alasan(self):
        self.ensure_one()
        return {
            'name': 'Alasan Pembatalan',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.surat_peringatan_alasan',
        }
    
    def submit_surat_peringatan(self):
        self.is_wanprestasi_requested = True

    def konfirmasi_surat_peringatan(self):
        self.is_wanprestasi_approved = True

    def submit_surat_peringatan_alasan(self):
        self.is_wanprestasi_alasan_requested = True

    def konfirmasi_surat_peringatan_alasan(self):
        self.is_wanprestasi_approved = True
        self.state = '50'
        self.is_wanprestasi = True

    is_wanprestasi_requested = fields.Boolean()
    is_wanprestasi_approved = fields.Boolean()
    
    is_wanprestasi_alasan_requested = fields.Boolean()
    is_wanprestasi = fields.Boolean()

    wanprestasi_reason = fields.Html(string="Alasan Wanprestasi")
    wanprestasi_file = fields.Binary(string="Lampiran", attachment=True, track_visibility=True)
    wanprestasi_filename = fields.Char(string="Lampiran")
    
    def deny_approve(self):
        self.state = '10'
    
    def submit_approve(self):
        self.state = '20'

        cats = list()
        sale_order_ids = list()

        for contract_line_id in self.contract_line_ids:
            if contract_line_id.product_id.category not in cats:
                if contract_line_id.product_id.category is False or contract_line_id.product_id.category is 'False':
                    print("False")
                else:
                    cats.append(contract_line_id.product_id.category)

                    recurring_value = contract_line_id.recurring_value
                    if contract_line_id.recurring_type == "Tahunan":
                        recurring_value = recurring_value * 12

                    if contract_line_id.product_id.category == "Property":
                        qty = recurring_value / contract_line_id.payment_timeframe_value
                    else:
                        qty = recurring_value
                    index_number = 1

                    start_month = self.start_date.month
                    start_year = self.start_date.year

                    recurring_active = False

                    if contract_line_id.product_id.category == 'Property':
                        recurring_active = True

                    while index_number <= qty:
                        pname = ''
                        if contract_line_id.product_id.category == 'Service':
                            pname = '/Service'
                        elif contract_line_id.product_id.category == 'Jaminan':
                            pname = '/Deposit'
                        sale_order = self.env['sale.order'].create({
                            'partner_id': self.partner_id.id,
                            'name': self.name + '/' + str(index_number) +  pname,
                            'is_property': True,
                            'payment_term_id': self.payment_term_id.id,
                            'contract_id': self.id,
                            'warehouse_id': 1,
                            'department_id': self.env.user.department_id.id,
                            'contract_category': contract_line_id.product_id.category,
                            'recurring_type': contract_line_id.recurring_type if contract_line_id.recurring_type is not False else self.contract_recurring_type,
                            'recurring_value': recurring_value,
                            # 'recurring_month': start_month,
                            # 'recurring_year': start_year,
                            'recurring_active': recurring_active,
                            # 'hide': False if index_number == 1 else True, # untuk kondisi jika hanya bulan awal 
                            'hide': False
                        })

                        month_arr = []
                        year_arr = []

                        for contract_line_idd in self.contract_line_ids:
                            if contract_line_idd.product_id.category == contract_line_id.product_id.category:
                                if contract_line_id.product_id.category == "Property":
                                    index_number_2 = 1
                                    while index_number_2 <= contract_line_id.payment_timeframe_value:
                                        self.env['sale.order.line'].create({
                                            'product_id': contract_line_idd.product_id.id,
                                            'price_unit': contract_line_idd.price_unit,
                                            'product_uom': contract_line_idd.product_uom.id,
                                            # 'product_uom_qty': contract_line_idd.recurring_value,
                                            'product_uom_qty': 1,
                                            'order_id': sale_order.id,
                                            'name': contract_line_id.product_id.category,
                                            'name': "SO %s %s %s" % (contract_line_id.product_id.category, str(bulan_name_arr[int(start_month)]), start_year),

                                            'rent_price': contract_line_id.product_id.rent_price,
                                            'rent_price_month': contract_line_id.product_id.rent_price_month,
                                            'service_charge_price': contract_line_id.product_id.service_charge_price,
                                            'service_charge_price_month': contract_line_id.product_id.service_charge_price_month,
                                        })

                                        if str(start_month) not in month_arr:
                                            month_arr.append(str(bulan_name_arr[int(start_month)]))

                                        if str(start_year) not in year_arr:
                                            year_arr.append(str(start_year))

                                        index_number_2 += 1
                                        recurring_active = False
                        
                                        next_month = start_month + 1
                                        next_year = start_year
                                        if next_month > 12:
                                            next_month = 1
                                            next_year = next_year + 1

                                        start_month = next_month
                                        start_year = next_year
                                else:
                                    self.env['sale.order.line'].create({
                                        'product_id': contract_line_idd.product_id.id,
                                        'price_unit': contract_line_idd.price_unit,
                                        'product_uom': contract_line_idd.product_uom.id,
                                        # 'product_uom_qty': contract_line_idd.recurring_value,
                                        'product_uom_qty': 1,
                                        'order_id': sale_order.id,
                                        'name': "SO %s %s %s" % (contract_line_id.product_id.category, str(bulan_name_arr[int(start_month)]), start_year),

                                        'rent_price': contract_line_id.product_id.rent_price,
                                        'rent_price_month': contract_line_id.product_id.rent_price_month,
                                        'service_charge_price': contract_line_id.product_id.service_charge_price,
                                        'service_charge_price_month': contract_line_id.product_id.service_charge_price_month,
                                    })

                                    if str(start_month) not in month_arr:
                                        month_arr.append(str(bulan_name_arr[int(start_month)]))

                                    if str(start_year) not in year_arr:
                                        year_arr.append(str(start_year))
                        
                                    next_month = start_month + 1
                                    next_year = start_year
                                    if next_month > 12:
                                        next_month = 1
                                        next_year = next_year + 1

                                    start_month = next_month
                                    start_year = next_year

                        sale_order.recurring_month = ", ".join(month_arr)
                        sale_order.recurring_year = ", ".join(year_arr)
                        index_number += 1
                        
                    if contract_line_id.product_id.category == 'Jaminan':
                        contract_line_id.contract_id.so_security_deposit_id = sale_order.id

        for contract_line_id in self.contract_line_ids:
            if contract_line_id.product_id.category == 'Property':
                contract_line_id.product_id.available = False 

    def do_running(self):
        self.ensure_one()
        return {
            'name': 'Running Kontrak',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.running',
        }

    def submit_running(self):
        self.state = '30'

        for contract_line_id in self.contract_line_ids:
            if contract_line_id.product_id.category == 'Property':
                contract_line_id.product_id.space_rent_out = contract_line_id.product_id.total_large_available
                contract_line_id.product_id.total_large_available = 0

        if self.contract_type == "Extend":
            extended_contract_id = self.extended_contract_id
            if extended_contract_id.state == '30':
                extended_contract_id.state = '50'

        if self.contract_type == "Adendum":
            historical_contract_id = self.historical_contract_id
            if historical_contract_id.state == '30':
                historical_contract_id.state = '50'

    def do_done(self):
        self.ensure_one()
        return {
            'name': 'Done Kontrak',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.done',
        }

    def submit_done(self):
        self.state = '50'

        for contract_line_id in self.contract_line_ids:
            if contract_line_id.product_id.category == 'Property':
                contract_line_id.product_id.available = True

    def do_expired(self):
        self.ensure_one()
        return {
            'name': 'Expired Kontrak',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mcs_property.contract.expired',
        }

    def submit_expired(self):
        self.state = '40'

        for contract_line_id in self.contract_line_ids:
            if contract_line_id.product_id.category == 'Property':
                contract_line_id.product_id.available = True

    @api.onchange('onchange_contract_id', 'contract_type')
    def _onchange_onchange_contract_id(self):
        for values in self:
            if values.contract_type == 'Extend' and values.onchange_contract_id is not False:
                values.extended_contract_id = values.onchange_contract_id
                values.contract_line_ids = values.extended_contract_id.contract_line_ids
                values.partner_id = values.extended_contract_id.partner_id
                values.product_location_id = values.extended_contract_id.product_location_id
                values.contract_recurring_type = values.extended_contract_id.contract_recurring_type
                values.contract_recurring_value = values.extended_contract_id.contract_recurring_value
                values.start_date = values.extended_contract_id.start_date
                values.warning_date = values.extended_contract_id.warning_date
                values.payment_term_id = values.extended_contract_id.payment_term_id

    @api.onchange('start_date', 'contract_recurring_type', 'contract_recurring_value')
    def _change_end_date(self):
        for values in self:
            if values.contract_recurring_type and values.contract_recurring_value and values.start_date:
                contract_recurring_type = values.contract_recurring_type
                contract_recurring_value = values.contract_recurring_value

                if contract_recurring_value <= 0:
                    raise UserError("Minimum recurring value is 1")

                if contract_recurring_type == 'Harian':
                    values.end_date = values.start_date + timedelta(days=contract_recurring_value - 1)
                elif contract_recurring_type == 'Bulanan':
                    values.end_date = values.start_date + relativedelta(months=contract_recurring_value) - timedelta(days=1)
                elif contract_recurring_type == 'Tahunan':
                    values.end_date = values.start_date + relativedelta(years=contract_recurring_value) - timedelta(days=1)

                if len(values.contract_line_ids) > 0:
                    for contract_line in values.contract_line_ids:
                        if contract_line.product_id.category == "Property" or contract_line.product_id.category == "Service":
                            contract_line.recurring_type = values.contract_recurring_type
                            contract_line.recurring_value = values.contract_recurring_value

    @api.onchange('end_date')
    def _change_contract_time_date(self):
        for values in self:
            if values.start_date and values.end_date:
                values.contract_time = int((values.end_date - values.start_date).days)

class HistoryPenagihan(models.Model):
    _name = 'mcs_property.contract.riwayat_penagihan'
    _description = "History Penagihan"

    contract_id = fields.Many2one('mcs_property.contract', string='Contract Reference', required=True,
                                  ondelete='cascade', index=True)
    name = fields.Html(string='Keterangan')
    create_date = fields.Datetime(string='Waktu Penagihan')
    
class ContractLine(models.Model):
    _name = 'mcs_property.contract.line'
    _description = "Contract Lines"

    @api.depends('recurring_type', 'recurring_value', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            recurring_value = line.recurring_value
            if line.recurring_type == "Tahunan":
                recurring_value = line.recurring_value * 12

            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.contract_id.currency_id, recurring_value,
                                            product=line.product_id, partner=line.contract_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    contract_id = fields.Many2one('mcs_property.contract', string='Contract Reference', required=True,
                                  ondelete='cascade', index=True)
    name = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10) 
    
    def _default_currency_id(self):
        data = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)
        return data.id

    currency_id = fields.Many2one('res.currency', string='Currency', default=_default_currency_id)
    price_unit = fields.Monetary(string='Price', currency_field='currency_id', required=True)

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)

    product_id = fields.Many2one('product.product', string='Product', domain="[('is_property', '=', True), ('available', '=', True)]",
        change_default=True, ondelete='cascade', check_company=True, required=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]", required=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)

    category = fields.Selection(related='product_id.category', readonly=False, required=True)
    product_template_id = fields.Many2one(
        'product.template', string='Product Template', related="product_id.product_tmpl_id",
        domain=[('is_property', '=', True), ('available', '=', True)])

    invoice_lines = fields.Many2many('account.move.line', 'mcs_contract_line_invoice_rel', 'contract_line_id',
                                     'invoice_line_id', string='Invoice Lines', ondelete='cascade')
    product_no_variant_attribute_value_ids = fields.Many2many('product.template.attribute.value',
                                                              'mcs_contract_line_product_template',
                                                              string="Extra Values", ondelete='restrict')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', 'mcs_contract_line_analytic', string='Analytic Tags')

    product_location_id = fields.Many2one('mcs_property.location', string='Location', required=True)
    product_parent_id = fields.Many2one('product.template', domain="[('is_property', '=', True), ('parent_id', '=', False)]", change_default=True, ondelete='cascade', check_company=True, string="Location")
    product_parent_code = fields.Char(store=False)

    include_in_total = fields.Boolean(default=True, string="+")

    jenis_sharing = fields.Selection([
            ('revenue_sharing_or_minimum_rental', 'Revenue Sharing / Minimum Rental'), 
            ('revenue_sharing_plus_minimum_rental', 'Revenue Sharing + Minimum Rental'), 
            ('revenue_sharing', 'Revenue Sharing')
        ], track_visibility=True)
    nilai_sharing = fields.Float()
    
    # @api.onchange('nilai_sharing')
    # def _onchange_nilai_sharing(self):
    #     for rec in self:
    #         if rec.category == "Property":
    #             if rec.jenis_sharing == 'revenue_sharing_or_minimum_rental':
    #                 rec.product_id.revenue_sharing_or_minimum_rental = rec.nilai_sharing
    #             if rec.jenis_sharing == 'revenue_sharing_plus_minimum_rental':
    #                 rec.product_id.revenue_sharing_plus_minimum_rental = rec.nilai_sharing
    #             if rec.jenis_sharing == 'revenue_sharing':
    #                 rec.product_id.revenue_sharing = rec.nilai_sharing

    @api.onchange('jenis_sharing')
    def _onchange_jenis_sharing(self):
        for rec in self:
            if rec.category == "Property":
                # if rec.jenis_sharing == 'revenue_sharing_or_minimum_rental':
                #     rec.nilai_sharing = rec.product_id.revenue_sharing_or_minimum_rental
                # if rec.jenis_sharing == 'revenue_sharing_plus_minimum_rental':
                #     rec.nilai_sharing = rec.product_id.revenue_sharing_plus_minimum_rental
                # if rec.jenis_sharing == 'revenue_sharing':
                #     rec.nilai_sharing = rec.product_id.revenue_sharing
                if rec.jenis_sharing == 'revenue_sharing_or_minimum_rental':
                    rec.nilai_sharing = rec.product_id.revenue_sharing if rec.product_id.revenue_sharing > rec.product_id.minimum_rental else rec.product_id.minimum_rental
                if rec.jenis_sharing == 'revenue_sharing_plus_minimum_rental':
                    rec.nilai_sharing = rec.product_id.revenue_sharing + rec.product_id.minimum_rental
                if rec.jenis_sharing == 'revenue_sharing':
                    rec.nilai_sharing = rec.product_id.revenue_sharing

    # ===== hs 
    # 22 01 24
    payment_timeframe_type = fields.Selection([('Bulanan', 'Bulanan'), ('Tahunan', 'Tahunan')],
                                               track_visibility=True, string="Timeframe Type", required=True)
    payment_timeframe_value = fields.Integer(string="Timeframe Value", required=True, default=0)
    
    @api.onchange('payment_timeframe_type', 'payment_timeframe_value')
    def _compute_payment_timeframe(self):
        for rec in self:
            if rec.payment_timeframe_value and rec.contract_id.contract_recurring_type and rec.contract_id.contract_recurring_value and rec.contract_id.start_date and rec.product_id.category == "Property":
                recurring_value = rec.contract_id.contract_recurring_value
                if rec.contract_id.contract_recurring_type == "Harian":
                    recurring_value = 1
                elif rec.contract_id.contract_recurring_type == "Tahunan":
                    recurring_value = rec.contract_id.contract_recurring_value * 12

                qty = int(recurring_value / rec.payment_timeframe_value)
                sisa = recurring_value % rec.payment_timeframe_value
                if sisa > 0:
                    lama_sewa_baru = (qty + 1) * rec.payment_timeframe_value
                    for contract_line_id in rec.contract_id.contract_line_ids:
                        if contract_line_id.product_id.category == "Property" or contract_line_id.product_id.category == "Service":
                            contract_line_id.recurring_value = lama_sewa_baru
                else:
                    for contract_line_id in rec.contract_id.contract_line_ids:
                        if contract_line_id.product_id.category == "Property" or contract_line_id.product_id.category == "Service":
                            contract_line_id.recurring_value = recurring_value
    # =====
        
    @api.onchange('product_location_id')
    def _change_product_location_id(self):
        productId = []
        for rec in self:
            if rec.product_location_id:
                products = self.env['product.product'].search([('is_property', '=', True), ('is_contract_item', '=', True), ('available', '=', True), ('location_id', '=', rec.product_location_id.id)])

                for product in products:
                    productId.append(product.id)
            else:
                products = self.env['product.product'].search([('is_property', '=', True), ('is_contract_item', '=', True), ('available', '=', True)])

                for product in products:
                    productId.append(product.id)

        products_non_property = self.env['product.product'].search([('is_property', '=', True), ('category', '!=', 'Property')])
        
        for product_non_property in products_non_property:
            productId.append(product_non_property.id)

        domain = [('id', 'in', productId)]
                    
        return {'domain': {'product_id': domain}}
        
    @api.onchange('product_parent_id')
    def _change_product_parent_id(self):
        productId = []
        for rec in self:
            if rec.product_parent_id:
                rec.product_parent_code = str(rec.product_parent_id.parent_code) + '.'

                products = self.env['product.product'].search([('is_property', '=', True), ('available', '=', True), ('parent_scheme', 'like', rec.product_parent_code)])

                for product in products:
                    productId.append(product.id)

        products_non_property = self.env['product.product'].search([('is_property', '=', True), ('category', '!=', 'Property')])
        
        for product_non_property in products_non_property:
            productId.append(product_non_property.id)

        domain = [('id', 'in', productId)]
                    
        return {'domain': {'product_id': domain}}

    @api.onchange('product_id')
    def _change_product_id(self):
        for contract_line_id in self:
            contract_line_id.price_unit = contract_line_id.product_id.list_price
            contract_line_id.product_uom = contract_line_id.product_id.uom_id
            contract_line_id.category = contract_line_id.product_id.category
            
            contract_line_id.price_unit = contract_line_id.product_id.contract_price

            if contract_line_id.product_id.category == 'Jaminan':
                contract_line_id.recurring_type = 'Bulanan'
                contract_line_id.recurring_value = 1
            else:
                contract_line_id.recurring_type = contract_line_id.contract_id.contract_recurring_type
                contract_line_id.recurring_value = contract_line_id.contract_id.contract_recurring_value
            
            contract_line_id.payment_timeframe_type = 'Bulanan'
            contract_line_id.payment_timeframe_value = 1
    
    recurring_type = fields.Selection([('Harian', 'Harian'), ('Bulanan', 'Bulanan'), ('Tahunan', 'Tahunan')], default='Bulanan',track_visibility=True, required=True)
    recurring_value = fields.Integer(default=1, required=True)

    @api.model
    def create(self, vals):
        if 'start_date' in vals:
            if vals['start_date'] < vals['date_order'] :
                raise ValidationError('Start Date tidak boleh lebih kecil daripada Order Date')

        # vals['recurring_type'] = 'Bulanan'
        result = super(ContractLine, self).create(vals)

        product = result.product_template_id

        is_changed = False

        if product.category == 'Property':
            if product.contract_price != result.price_unit:
                is_changed = True
                product.contract_price = result.price_unit

            if product.recurring_type != result.recurring_type:
                is_changed = True
                product.recurring_type = result.recurring_type 
                
            if is_changed is True:
                product.existing_product = ''

                new_product = product.copy()
                new_product.name = product.name
                new_product.existing_product = 'Historical'
                new_product.historical_product_id = product.id
                new_product.active = False

                product.version = product.version + 1

        return result

    def write(self, vals):
        # vals['recurring_type'] = 'Bulanan'
        result = super(ContractLine, self).write(vals)

        if result:
            data = self.env['mcs_property.contract.line'].search([('id', '=', self.id)], limit=1)
            product = data.product_template_id

            is_changed = False

            if product.category == 'Property':
                if product.contract_price != data.price_unit:
                    is_changed = True
                    product.contract_price = data.price_unit

                if product.recurring_type != data.recurring_type:
                    is_changed = True
                    product.recurring_type = data.recurring_type 

                if is_changed is True:
                    product.existing_product = '' 

                    new_product = product.copy()
                    new_product.name = product.name
                    new_product.existing_product = 'Historical'
                    new_product.historical_product_id = product.id
                    new_product.active = False
    
                    product.version = product.version + 1

        return result