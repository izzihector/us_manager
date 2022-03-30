# -*- coding: utf-8 -*-


{
    'name': 'POS PVG',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Extensions for the Point of Sale ',
    'description': "",
    'depends': ['point_of_sale', 'stock', 'mrp', 'mrp_bom_cost', 'pos_restaurant'],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/pos_sales_cost_report.xml',
        'views/pos_sales_cost_report_line.xml',
        'views/pos_customer_orders_report.xml',
        'views/pos_customer_orders_report_line.xml',
        'views/pos_customers_orders_report.xml',
        'views/pos_template.xml',
        'views/product_view.xml',
        'views/product_template.xml',
        'views/pos_order.xml',
        # 'views/pos_order_type.xml',
        'views/mrp_bom_line.xml',
        # 'views/cost_structure_report.xml',
        'report/pos_sales_cost_report.xml',
        'report/pos_customer_orders_report.xml',
        'report/pos_customers_orders_report.xml',
        'report/mrp_report_bom_structure.xml',
    ],
    'qweb': [
        'static/src/xml/pos_pvg_mrp.xml',
        # 'static/src/xml/pos_pvg_screens.xml',
    ],
    'installable': True,
    'auto_install': False,
}
