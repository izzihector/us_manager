from datetime import timedelta
from types import SimpleNamespace

from odoo import api, fields, models


class ReportSaleReport(models.AbstractModel):
    _name = 'report.bs_sarinah_portal.xlsx_sale_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, xlsx_data, sale_report_objs):
        domain = [
            ("product_id.owner_id", "child_of", self.env.user.partner_id.commercial_partner_id.id),
        ]
        report_ids = sale_report_objs.sudo().search(domain, order='date desc, branch_id asc, brand_id asc, product_id asc, id desc')
        self._apply_workbook_format(workbook)
        ws = workbook.add_worksheet('Sales Report')
        ws.set_column('A:A', 20)
        ws.set_column('B:D', 30)
        ws.set_column('E:E', 70)
        ws.set_column('F:F', 10)
        ws.set_column('G:L', 30)
        ws.set_row(0, 20)

        row = 0
        ws.merge_range(row, 0, row, self.table_end_column_num-1, 'Sales Report', self.format_title)
        row += 1
        row = self._render_header(ws, row, [
            'Date',
            'No SO',
            'Location',
            'Brand',
            'Variant',
            'Qty',
            'Gross Sale',
            'Discount',
            'Net Sales',
            'Hak Mitra',
            'Discount Beban Mitra',
            'Hak Mitra Setelah Discount',
        ])
        for report in report_ids:
            row = self._render_line(ws, row, 0, [
                (report.date + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                report.name,
                report.branch_id.display_name,
                report.brand_id.display_name,
                ', '.join([
                    '%s (%s)' % (report.product_id.name, attr.name)
                    for attr in report.product_id.product_template_attribute_value_ids
                ]),
                report.product_uom_qty,
                report.price_total + report.discount_amount,
                report.discount_amount,
                report.price_total,
                report.supplier_revenue,
                report.supplier_discount,
                report.supplier_gross_revenue,
            ])

        if not len(report_ids):
            ws.merge_range(row, 0, row, self.table_end_column_num,
                           'There are currently no sales report found by your criteria.')

    def _render_header(self, ws, row, section_cols):
        for idx in range(0, self.table_end_column_num):
            if len(section_cols) > idx:
                ws.write(row, idx, section_cols[idx], self.format_header)
            else:
                ws.write(row, idx, None, self.format_header)
        return row + 1

    def _render_line(self, ws, row, col, line_cols, ignore_empty=False):
        line_cols = ([''] * (col or 0)) + line_cols
        for idx in range(0, self.table_end_column_num):
            if len(line_cols) > idx:
                if ignore_empty and line_cols[idx] == '':
                    continue
                ws.write(row, idx, line_cols[idx], self.format_content)
            else:
                ws.write(row, idx, None, self.format_content)
        return row + 1

    def _apply_workbook_format(self, workbook):
        self.table_end_column = 'L'
        self.table_end_column_num = 12
        self.format_title = workbook.add_format({
            'font_size': 15,
            'font_color': '#333333',
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        self.format_header = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter',
            'top': 1,
            'bottom': 1,
        })
        self.format_content = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter',
            'bottom': 1,
        })
