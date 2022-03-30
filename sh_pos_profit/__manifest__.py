# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "POS Profit in Sale Detail",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Point Of Sale", 
    "summary": "POS Profit Report,POS Order Daily Products Profit  Report,POS Anlysis Module, Products Cost Subtotal,Discount, Cost Price In Point Of Sale,point of sale Profit Odoo",
    "description": """Currently, profit and cost subtotal not there in the pos summary report. So here we build a module that provides you profit details, cost subtotal, discount amount, subtotal, cost price in the sales details report.
POS Profit Report Odoo, POS Order Daily Products Profit  Report Odoo. 
Calculate Profit/ Earning Report In Point Of Sale, Day/Month/Year Wise Clients POS Detail Report Odoo, Feature Of Customer profit, Subtotal, discount amount,Cost subtotal, cost price,Discount, Total Discount, Total CostPrice , Total Subtotal, Total Profitt ,Total Profit ,Cost Subtotal In POS.""",
    "version": "13.0.2",
    "depends": ['point_of_sale', 'bs_sarinah_department'],
    "application" : True,
    "data": [
        'views/report_pos_sales_details_custom.xml',
    ],

    "images": ["static/description/background.jpg", ],
    "auto_install":False,
    "installable" : True,
    "price": 25,
    "currency": "EUR"
}
