# -*- coding: utf-8 -*-

from odoo import models, fields, api


# class mcs_inherit_product_zebra(models.TransientModel):
#     _name = 'wizard.print.zebra'
#     _description = 'Wizard for looping direct print ZPL'
#
#     # product_ids = fields.Many2many(comodel_name='product.product', string='Products')
#     count = fields.Integer("Count")
#
#     def act_print(self):
#         for p in self.product_ids:
#             print("MAssssss")
#             p.print_zebra()
            # return p.env.ref('product_label_for_zebra_printer.report_product_zpl_label').report_action(p,{})

class mcs_inherit_product_product(models.Model):
    _inherit = 'product.product'

    print_copy = fields.Integer("Numbers of copies ZPL Print", default=10)
    print_pricelist = fields.Many2one(comodel_name="product.pricelist", string="Pricelist For ZPL Print")

    def get_data_field(self, stype):
        if stype == 'price':
            pricelist = self.env['product.pricelist'].search([('id', '=', self.print_pricelist.id or 1)])
            price = self.list_price
            if pricelist:
                price = pricelist.get_product_price(self, 1, False)
            return '{:,.0f}'.format(price).replace(",", ".")
        elif stype == 'variant':
            return self.product_template_attribute_value_ids._get_combination_name_new()

#     def get_report_template(self):
#         print("Masukkkk")
# #         temp = """
# #         {self.description}
# # """
# #         rep = self.env.ref('product_label_for_zebra_printer.report_product_zpl_label')
# #         zzz = rep.parse_template(temp, "product.product", self.id, rep.report_template_id)
# #         print(zzz)
#
# class InheritReportTemplate(models.Model):
#     _inherit = 'report.template'
#
#     base_template = fields.Text(string="Base Report Template")