# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class InheritPosPromotions(models.Model):
    _inherit = 'pos.promotions'

    offer_type2 = fields.Selection(string="Offer Type",
                                   required=True,
                                   selection=[('buy_x_get_y', 'Buy X Product & Get Y Product Free'),
                                             ('buy_x_get_y_qty', 'Buy X Product & Get Y Qty Product Free'),
                                             ('buy_x_get_discount_on_y', 'Buy X and Get Discount on Y Product')])

    criteria_type = fields.Selection([('every_new_customer','For Every New Customers '),
        ('every_x_order','For Every X Order Per POS Session '),
        ('first_x_customer','For First X Customers Per POS Session'),
        ('every_order','For Every Order '),('based_specific_date','Based On Specific Date'),], default='based_specific_date')

    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    vendor_id = fields.Many2one(comodel_name='res.partner', string="Vendor Name")
    day_of_week_ids = fields.Many2many('day.weeks', string="Day Of The Week", required=True)

    @api.onchange('offer_type2')
    def onchange_offer_type2(self):
        for x in self:
            x.offer_type = x.offer_type2

    # @api.onchange('offer_type')
    # def onchange_offer_type(self):
    #     for x in self:
    #         x.offer_type2 = x.offer_type

    @api.onchange('vendor_id')
    def onchange_vendor_id(self):
        for x in self:
            x.discounted_ids = None
            x.buy_x_get_y_ids = None
            x.buy_x_get_y_qty_ids = None
            x.buy_x_get_discount_on_y_ids = None
            x.discount_sale_total_ids = None


    @api.constrains('wk_day', 'wk_month', 'discount_sale_total_ids')
    def validate_day_mont(self):
        # if (self.criteria_type == 'based_specific_date'):
        #     if not self.wk_month and not self.wk_day:
        #         raise ValidationError("Please enter the Day and Month")
        #     if not self.wk_month:
        #         raise ValidationError("Please enter the Month")
        #     elif not self.wk_day:
        #         raise ValidationError("Please enter the Day")
        #
        #     if self.wk_month.isdigit() and self.wk_day.isdigit():
        #         wk_day = int(self.wk_day)
        #         wk_month = int(self.wk_month)
        #         if wk_month > 12 or wk_month < 1:
        #             raise ValidationError("Month can't be less than 0 or greater than 12")
        #         elif wk_month in [1, 3, 5, 7, 8, 10, 12]:
        #             if (wk_day < 1 or wk_day > 31):
        #                 raise ValidationError("Please check the day in corresponding month")
        #         elif wk_month in [4, 6, 9, 11]:
        #             if (wk_day < 1 or wk_day > 30):
        #                 raise ValidationError("Please check the day in corresponding month")
        #         elif wk_month == 2:
        #             if (wk_day < 1 or wk_day > 28):
        #                 raise ValidationError("Please check the day in corresponding month")
        #
        #     else:
        #         raise ValidationError("Day and month will be interger type")

        if (len(self.discount_sale_total_ids) > 1):
            for line1 in self.discount_sale_total_ids:
                for line2 in self.discount_sale_total_ids:
                    if (line1.id != line2.id):
                        flag = 0
                        if (
                                line2.min_amount < line1.min_amount and line2.min_amount < line1.max_amount and line2.max_amount < line1.max_amount and line2.max_amount < line1.min_amount):
                            flag += 1
                        elif (
                                line2.min_amount > line1.min_amount and line2.min_amount > line1.max_amount and line2.max_amount > line1.max_amount and line2.max_amount > line1.min_amount):
                            flag += 1

                        if (not flag):
                            raise ValidationError(
                                'There is some overlapping in the Rule. Please Check and re-assign the Rules.')

class DayWeeks(models.Model):
    _name = 'day.weeks'

    name = fields.Char(string="Name")
