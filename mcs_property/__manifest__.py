# -*- coding: utf-8 -*-
{
    'name': "MCS | PROPERTY MANAGEMENT",
    'summary': """
        MCS | PROPERTY MANAGEMENT
    """,
    'description': """
        MCS Property
        For Odoo V. 13. If you want to know more about us, please visit our official website. Click here
        If you find an error or bug from this module, please contact our developer to help with your problem. ( bratabayu@matrica.co.id or info@matrica.co.id)
        PT. Matrica Consulting Service
        Matrica Technical Manager
        Brata Bayu. S, S.Kom

        Developer : Hari Sabintang

        Office :
        Patrajasa Office Tower 15th floor 1503B Jl. Jend. Gatot Subroto Kav. 32 - 34 Jakarta Selatan 12950 Indonesia
        021-52900185
        info@matrica.co.id

        V 13.0.2
        - Nama produk unit property tidak menggunakan fungsi name_get lagi
        - Nama produk unit property set otomatis ketika Create atau Update
        - Format nama produk property: nama lokasi / nama space / kode unit
        - Contract line penambahan field 
          + payment_timeframe_type: pilihan untuk menentukan pembayaran bulanan/ tahunan
          + payment_timeframe_value: nilai untuk menentukan pembayaran per berapa bulan/ tahun
        - Ketika timeframe pembayaran unit property lebih besar daripada lama kontrak, maka end_date dari lama kontrak mengikut berdasarkan time_frame pembayaran unit property
        - Field recurring type dan recurring value di contract line disembunyikan, fungsi yang berkaitan dengan field tersebut sekarang langsung berhubungan ke field recurring type dan recurring value di contract 
        - Ketika recurring type atau recurring value contract diubah, maka total harga di line juga akan ikut berubah
    """,
    'author': "MCS",
    'website': "http://www.matrica.co.id",
    'category': 'Property',
    'version': '13.0.2',
    'depends': ['base', 'sale', 'product', 'auth_signup', 'purchase', 'hr_expense', 'bs_sarinah_department', 'bs_consignment_bills', 'vendor_product_management', 'bi_product_brand'],
    'data': [
        'security/res_group.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/assets.xml',

        'views/products.xml',
        'views/customers.xml',
        'views/contract.xml',
        # 'views/product_category.xml',
        'views/document_properties.xml',
        'views/format_nomor.xml',

        'views/orders.xml',

        # 'views/signup.xml',

        'views/actions.xml',
        'views/menu.xml',

        'wizards/contract.xml',
    ],
    "images": ['static/description/icon.png'],
    'demo': [
        'demo/demo.xml',
    ],
}
