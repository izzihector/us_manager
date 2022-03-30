# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from openerp import api, fields, models
from openerp.exceptions import Warning, ValidationError
from datetime import datetime


# from chameleon.nodes import Default


class POsCustomDiscount(models.Model):
    _name = "pos.custom.discount"

    name = fields.Char(string="Name", required=1)
    description = fields.Text(string="Description")
    available_in_pos = fields.Many2many('pos.config', string="POS Config")
    discount_type = fields.Selection([('fix_price', 'Fix Price'), ('percentage', 'Percentage')],
                                     string="Discount Type", default="percentage", required=True)
    value = fields.Float(string="Value", required=True)
    day_of_week_ids = fields.Many2many('day.week', string="Day Of The Week", required=True)
    start_date = fields.Datetime(string="Start Date", required=True)
    end_date = fields.Datetime(string="End Date", required=True)
    apply_on = fields.Selection([('product', 'Product'), ('category', 'Category')], string="Applied On", required=True)
    start_time = fields.Integer(string="Start Time(hr)")
    end_time = fields.Integer(string="End Time(hr)", default="23")
    exception_date_ids = fields.One2many('exception.dates', 'discount_id', string="Exception Dates")
    product_ids = fields.Many2many('product.product', string="Product")
    categ_ids = fields.Many2many('pos.category', string="Category")

    @api.constrains('exception_date_ids', 'start_date', 'end_date')
    def check_validation_exception_date_ids(self):
        for id in self.exception_date_ids:
            if self.start_date > id.start_date or self.end_date < id.end_date:
                raise ValidationError("Exception date must be in between discount start date and end date")

    @api.model
    def default_get(self, fields):
        res = super(POsCustomDiscount, self).default_get(fields)
        ids = self.env['day.week'].search([])
        res.update({'day_of_week_ids': [(6, 0, [x.id for x in ids])]})
        return res

    @api.constrains('discount_type', 'value')
    def check_validation_discount(self):
        if self.discount_type == 'percentage':
            if self.value <= 0 or self.value > 100:
                raise ValidationError("Discount percent must be between 1 and 100.")
        if self.discount_type == 'fix_price':
            if self.value <= 0:
                raise ValidationError("Discount fix price  must be grater than 0.")

    @api.constrains('start_date', 'end_date')
    def check_validation_date(self):
        if self.end_date < self.start_date:
            raise ValidationError('End Date not be past from Start Date')

    @api.constrains('start_time', 'end_time')
    def check_validation_time(self):
        if self.end_time < self.start_time:
            raise ValidationError('End Time not be past from Start Time')


class PosConfig(models.Model):
    _inherit = 'pos.config'

    discount_ids = fields.Many2many('pos.custom.discount', string="Discounts")
    allow_custom_discount = fields.Boolean('Allow Customize Discount', default=True)
    allow_security_pin = fields.Boolean('Allow Security Pin')
    open_discount_popup = fields.Char('Shortcut Key')


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    custom_discount_reason = fields.Text('Discount Reason')
    fix_discount = fields.Float('Discount (Fixed)')


class DayWeek(models.Model):
    _name = 'day.week'

    name = fields.Char(string="Name")


class ExceptionDates(models.Model):
    _name = 'exception.dates'

    start_date = fields.Datetime(string="From Date")
    end_date = fields.Datetime(string="To Date")
    discount_id = fields.Many2one('pos.custom.discount')

    @api.constrains('start_date', 'end_date')
    def check_validation_date(self):
        if self.end_date < self.start_date:
            raise ValidationError('End Date not be past from Start Date in exception dates')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
