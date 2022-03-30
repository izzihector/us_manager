# -*- coding: utf-8 -*-
{
    'name': "mcs_vernoss_product",
    'summary': """
        Integrasi Kategori dan Droduk dari Odoo ke LMS Vernoss 
        """,
    'description': """
        Integrasi Kategori dan Droduk dari Odoo ke LMS Vernoss 
    """,
    'author': "PT Matrica",
    'website': "http://www.matrica.co.id",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'sale'],
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
