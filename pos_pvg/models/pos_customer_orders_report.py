from odoo import api, fields, models


class posCustomerOrdersReport(models.Model):
    _name = "pos.customer.orders.report"
    _description = "PoS customer orders report"

    name = fields.Char(
        string=u'Name',
        compute='compute_name',
    )
    start_date = fields.Datetime(
        string=u'Start Date',
    )
    end_date = fields.Datetime(
        string=u'End Date',
    )

    customer = fields.Many2one(
        string=u'Customer',
        comodel_name='res.partner',
        ondelete='set null',
    )

    products = fields.Many2many(
        string=u'Products',
        comodel_name='product.template',
        relation='pos_customer_orders_report_product_template_rel',
        column1='product_template_id',
        column2='pos_customer_orders_report_id',
    )
    pos_orders = fields.Many2many(
        string=u'POS Orders',
        comodel_name='pos.order',
        relation='pos_customer_orders_report_pos_order_rel',
        column1='pos_order_id',
        column2='pos_customer_orders_report_id',
        compute='compute_pos_orders',
    )

    report_lines_ids = fields.One2many(
        string=u'Report Lines',
        comodel_name='pos.customer.orders.report.line',
        inverse_name='pos_customer_orders_report',
        # compute='compute_report_lines',
    )
    
    total_quantity = fields.Float(
        string=u'Total Quantity',
        # compute='compute_total_quantity',
    )
    total_sales = fields.Float(
        string=u'Total Sales',
        # compute='compute_total_sales',
    )
    total_discount = fields.Float(
        string=u'Total Discount',
        # compute='compute_total_discount',
    )
    

    @api.onchange('start_date', 'end_date', 'customer')
    def compute_name(self):
        for record in self:
            if record.start_date and record.end_date and record.customer:
                record.name = record.customer.name + ' - From: ' + record.start_date.strftime(
                    "%Y-%m-%d %H:%M:%S") + ' To: ' + record.end_date.strftime("%Y-%m-%d %H:%M:%S")

    @api.onchange('start_date', 'end_date', 'customer')
    def compute_pos_orders(self):
        for record in self:
            if record.customer:
                pos_orders = self.env['pos.order'].search(['&', ('date_order', '>=', record.start_date), (
                    'date_order', '<=', record.end_date), ('partner_id', '=', record.customer.id)])
                orders_ids = []
                for pos_order in pos_orders:
                    orders_ids.append(pos_order.id)
                record.pos_orders = [(6, 0, orders_ids)]

    # @api.onchange('pos_orders','products','customer')
    # def compute_report_lines(self):
    #     for record in self:
    #         if record.customer and record.pos_orders:
    #             report_lines = []
    #             if record.products:
    #                 for product in record.products:
    #                     quantity = 0.0
    #                     sales = 0.0
    #                     discount = 0.0
    #                     for order in record.pos_orders:
    #                         if order.partner_id.id == record.customer.id:
    #                             for order_line in order.lines:
    #                                 if product.id == order_line.product_id.product_tmpl_id.id:
    #                                     quantity += order_line.qty
    #                                     sales += order_line.price_unit * order_line.qty
    #                                     discount = (product.list_price * quantity) - sales
    #                     if quantity != 0.0:
    #                         report_lines.append((0,0,{'product_template': product.id, 'customer': record.customer.id, 'quantity': quantity, 'sales': sales, 'discount': discount}))
    #                         # report_lines.append({'product_template': product.id, 'customer': record.customer.id, 'quantity': quantity, 'sales': sales, 'discount': discount})
    #                 if len(report_lines) != 0.0:
    #                     record.report_lines_ids = record.report_lines_ids.create(report_lines)

    @api.multi
    def calculate_report_linse(self):
        for record in self:
            if record.report_lines_ids:
                for report_line in record.report_lines_ids:
                    report_line.unlink()
            if record.customer and record.pos_orders:
                report_lines = []
                t_quantity = 0.0
                t_sales = 0.0
                t_discount = 0.0
                if record.products:
                    for product in record.products:
                        quantity = 0.0
                        sales = 0.0
                        discount = 0.0
                        for order in record.pos_orders:
                            if order.partner_id.id == record.customer.id:
                                for order_line in order.lines:
                                    if product.id == order_line.product_id.product_tmpl_id.id:
                                        quantity += order_line.qty
                                        sales += order_line.price_unit * order_line.qty
                                        discount = (product.list_price * quantity) - sales
                        if quantity != 0.0:
                            t_quantity += quantity
                            t_sales += sales
                            t_discount += discount

                            report_lines.append((0,0,{'product_template': product.id, 'customer': record.customer.id, 'quantity': quantity, 'sales': sales, 'discount': discount}))
                            # report_lines.append({'product_template': product.id, 'customer': record.customer.id, 'quantity': quantity, 'sales': sales, 'discount': discount})
                    if len(report_lines) != 0.0:
                        record.report_lines_ids = report_lines
                        record.total_quantity = t_quantity
                        record.total_sales = t_sales
                        record.total_discount = t_discount



    # @api.onchange('report_lines_ids')
    # def compute_total_quantity(self):
    #     for record in self:
    #         if record.report_lines_ids:
    #             t_quantity = 0.0
    #             for line in record.report_lines_ids:
    #                 t_quantity += line.quantity
    #             record.total_quantity = t_quantity

    # @api.onchange('report_lines_ids')
    # def compute_total_sales(self):
    #     for record in self:
    #         if record.report_lines_ids:
    #             t_sales = 0.0
    #             for line in record.report_lines_ids:
    #                 t_sales += line.sales
    #             record.total_sales = t_sales

    # @api.onchange('report_lines_ids')
    # def compute_total_discount(self):
    #     for record in self:
    #         if record.report_lines_ids:
    #             t_discount = 0.0
    #             for line in record.report_lines_ids:
    #                 t_discount += line.discount
    #             record.total_discount = t_discount

class posCustomerOrdersReportLine(models.TransientModel):
    _name = "pos.customer.orders.report.line"
    _description = "PoS customer orders report Line"

    pos_customer_orders_report = fields.Many2one(
        string=u'POS Customer Orders Report',
        comodel_name='pos.customer.orders.report',
        ondelete='CASCADE',
    )
    customer = fields.Many2one(
        string=u'Customer',
        comodel_name='res.partner',
        ondelete='set NULL',
    )
    product_template = fields.Many2one(
        string=u'Product',
        comodel_name='product.template',
        ondelete='set NULL',
    )
    quantity = fields.Float(
        string=u'Quantity',
    )
    sales = fields.Float(
        string=u'Sales',
    )
    discount = fields.Float(
        string=u'Discount',
    )