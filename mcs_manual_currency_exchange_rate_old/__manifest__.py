# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Edited by. Matrica Consulting - TPW (Feb 2022)
#
##############################################################################

{
    'name': "Manual Currency Exchange rate for SO,Invoice,PO,Vendor Bills/Payments",
    'version': "13.0.0.0",
    'summary': "Manual exchange currency rate on SO, Invoice/Bill, PO and Payments",
    'category': 'Accounting',
    'description': """
    manual currency exchange rate
        manual currency exchange rate on invoice 
        manual currency exchange rate on sales order
        manual currency exchange rate on Purchase order
        manual currency exchange rate on request for quotations
        manual currency exchange rate on quotations
        manual currency exchange rate on payments
        manual currency exchange rate on customer payments
        manual currency exchange rate on vendor payments
        manual currency exchange rate on supplier payments
        custom currency exchange rate
        override currency exchange rate
        foreign exchange
        profit and loss by exchange rate
        activate manual currency exchange rate
        invoice manual currency exchange rate
        sales order manual currency exchange rate
        vendor bills manual currency exchange rate
        customer invoice manual currency exchange rate
        payments manual currency exchange rate
        inherit sales order form
        inherit invoice order
        inherit customer invoice
        inherit vendor bills
        inherit customer payments
        inherit vendor bills payments
    """,
    'author': "Matrica",
    'website':"http://www.matrica.co.id",
    'depends': ['base', 'sale_management', 'purchase', 'stock', 'account'],
    'data': [
        'views/inherited_invoice_payment.xml',
        'views/inherited_invoice.xml',
        'views/inherited_purchase_order.xml',
        'views/inherited_sale_order.xml',
        'views/inherited_res_currency.xml',
    ],
    'demo': [],
    "external_dependencies": {},
    'installable': True,
    'auto_install': False,
    'live_test_url': 'https://youtu.be/sDmW8wEQm4g',
    'images': ['static/description/banner.png'],
    
}
