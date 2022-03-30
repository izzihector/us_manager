from types import SimpleNamespace

from odoo import api, fields, models


class ReportPPBKReport(models.AbstractModel):
    _name = 'report.bs_sarinah_portal.xlsx_ppbk_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, xlsx_data, ppbk_objs):
        self._apply_workbook_format(workbook)
        ws = workbook.add_worksheet("Report")
        ws.set_portrait()
        ws.set_page_view()
        ws.center_horizontally()
        ws.set_margins(left=0, right=0, top=0, bottom=0)
        ws.hide_gridlines()
        ws.print_across()
        ws.fit_to_pages(1, 0)

        ws.set_column('A:A', 5)
        ws.set_column('B:M', 22)
        report_data = ppbk_objs.get_report_data()
        data = SimpleNamespace(**report_data)

        row = self._render_report_header(ws, 0, data)

        row = self._render_section_title(ws, row, ['A', 'MASTER VENDOR'])
        row = self._render_section_header(ws, row, [
            'Kode Vendor',
            'Nama Vendor',
            'PKP',
            'No. NPWP',
            'Bank',
            'No Rekening',
            'Nama Rekening',
        ])
        self._render_line(ws, row, 0, [
            data.partner.ref,
            data.partner.name,
            'YA' if data.partner.l10n_id_pkp else 'TIDAK',
            data.partner.vat,
        ])
        for idx, bank in enumerate(data.partner.bank_ids):
            row = self._render_line(ws, row, 4, [
                bank.bank_id.display_name,
                bank.acc_number,
                bank.acc_holder_name,
            ], ignore_empty=idx == 0)
        row += 2

        row = self._render_section_title(ws, row, ['B', 'MASTER VENDOR CONCESSION'])
        row = self._render_section_header(ws, row, [
            'Kode Vendor',
            'Lokasi',
            'Kode Konsesi/Brand',
            'Produk Kategori',
            '-Sarinah Margin (%)',
        ])
        for brand in data.brands:
            row = self._render_line(ws, row, 0, [
                data.partner.ref,
                data.branch.name or '-',
                brand.code,
            ])
            row -= 1
            for idx, margin in enumerate(brand.margin_ids):
                row = self._render_line(ws, row, 3, [
                    margin.category_id.display_name,
                    (margin.consignment_margin, 'percentage'),
                ], ignore_empty=idx == 0)
            if len(brand.margin_ids) == 0:
                row = self._render_line(ws, row, 3, [
                    '-',
                    (brand.consignment_margin, 'percentage'),
                ], ignore_empty=True)
        row += 2

        row = self._render_section_title(ws, row, ['C', 'PROMOTION'])
        row = self._render_section_header(ws, row, [
            'Kode Promotion',
            'Lokasi',
            'Kode Vendor',
            'Kode Produk',
            '-Diskon (%)',
            '-Sharing Diskon Vendor (%)',
        ])
        for discount in data.discounts:
            row = self._render_line(ws, row, 0, [
                discount.name,
                data.branch.name,
                discount.vendor_id.ref,
                ','.join(discount.product_ids.mapped('default_code')) if discount.product_ids else '-',
                (discount.value, 'percentage'),
                (discount.vendor_shared, 'percentage'),
            ])
        if len(data.discounts) == 0:
            error_msg = 'There is no transaction data found for this date period.'
            ws.merge_range(row, 0, row, 12, error_msg, self.format_error_line)
            row += 1
        row += 2

        row = self._render_section_title(ws, row, ['D', 'TRANSAKSI POS'])
        row = self._render_section_header(ws, row, [
            'Branch',
            'Kode Produk',
            '-Qty Sales',
            '-Subtotal',
            '-Diskon',
            '-Total',
            '-PPN Keluaran',
            '-Omset Setelah PPN'
        ])
        for order in data.orders:
            order = SimpleNamespace(**order)
            row = self._render_line(ws, row, 0, [
                data.branch.name,
                order.product_id.default_code,
                order.qty,
                order.subtotal,
                order.discount,
                order.total,
                order.taxes_amount,
                order.omset_amount,
            ])
        if len(data.orders) == 0:
            error_msg = 'There is no transaction data found for this date period.'
            ws.merge_range(row, 0, row, 12, error_msg, self.format_error_line)
            row += 1
        ws.merge_range(row, 0, row, 2, 'TOTAL', self.format_section_content)
        row = self._render_line(ws, row, 2, [
            data.orders_summary[0],
            data.orders_summary[1],
            data.orders_summary[2],
            data.orders_summary[3],
            data.orders_summary[4],
            data.orders_summary[5],
        ], ignore_empty=True)
        row += 2

        row = self._render_section_title(ws, row, ['E', 'PERHITUNGAN BAGI HASIL'])
        row = self._render_section_header(ws, row, [
            'Kode Produk',
            'Nama Produk',
            '-Sarinah Margin(%)',
            '-Sarinah Margin',
            '-Vendor Margin(%)',
            '-Vendor Margin',
            '-Shared Disc Sarinah (%)',
            '-Diskon Beban Sarinah',
            '-Shared Disc Vendor (%)',
            '-Diskon Beban Vendor',
            '-Income Sarinah',
            '-Income Vendor'
        ])
        for profit in data.profit_sharings:
            profit = SimpleNamespace(**profit)
            row = self._render_line(ws, row, 0, [
                profit.product_id.default_code,
                profit.product_id.name,
                (profit.sarinah_margin, 'percentage'),
                profit.sarinah_margin_amount,
                (profit.vendor_margin, 'percentage'),
                profit.vendor_margin_amount,
                (profit.sarinah_shared, 'percentage'),
                profit.sarinah_shared_amount,
                (profit.vendor_shared, 'percentage'),
                profit.vendor_shared_amount,
                profit.sarinah_income,
                profit.vendor_income,
            ])
        if len(data.profit_sharings) == 0:
            error_msg = 'There is no transaction data found for this date period.'
            ws.merge_range(row, 0, row, 12, error_msg, self.format_error_line)
            row += 1
        ws.merge_range(row, 0, row, 3, 'TOTAL', self.format_section_content)
        row = self._render_line(ws, row, 3, [
            data.profit_summary[0], ' ',
            data.profit_summary[1], ' ',
            data.profit_summary[2], ' ',
            data.profit_summary[3],
            data.profit_summary[4],
            data.profit_summary[5],
        ], ignore_empty=True)
        row += 2

        row = self._render_section_title(ws, row, ['F', 'BILL CONSIGNMENT PAYMENT'])
        row = self._render_section_header(ws, row, [
            'Bill Nomor',
            'Periode',
            'Lokasi',
            'Kode Vendor'
        ])
        for bill in data.bills:
            row = self._render_line(ws, row, 0, [
                bill.name,
                '%s - %s' % (str(bill.consignment_date_start), str(bill.consignment_date_end)),
                bill.branch_id.name,
                bill.partner_id.name,
            ])
        if len(data.bills) == 0:
            error_msg = 'There is no transaction data found for this date period.'
            ws.merge_range(row, 0, row, 12, error_msg, self.format_error_line)
            row += 1
        # Add 2 row spacer
        # row += 2

        # Must be called last
        ws.print_area(0, 0, row, self.table_end_column_num - 1)

    def _render_report_header(self, ws, row, data):
        ws.merge_range('A1:%s1' % self.table_end_column, 'PPBK Report', self.format_title)
        ws.write('A2', 'Company:', self.format_header_title)
        ws.write('A3', data.company.name, self.format_header_content)
        ws.write('A4', 'Branch:', self.format_header_title)
        ws.write('A5', data.branch.name, self.format_header_content)
        ws.write(1, self.table_end_column_num - 2, 'Period Date:', self.format_header_title)
        ws.write(2, self.table_end_column_num - 2, '%s - %s' % (data.start_date, data.end_date), self.format_header_content)
        ws.repeat_rows(0, 6)
        return 6

    def _render_section_title(self, ws, row, section_cols):
        for idx in range(0, self.table_end_column_num):
            if len(section_cols) > idx:
                ws.write(row, idx, section_cols[idx], self.format_section_title)
            else:
                ws.write(row, idx, None, self.format_section_title)
        return row + 1

    def _render_section_header(self, ws, row, header_cols):
        header_cols = [''] + header_cols
        for idx in range(0, self.table_end_column_num):
            cell_format = self.format_section_header
            if len(header_cols) > idx:
                value = header_cols[idx]
                if len(value) > 0 and value[0] == '-':
                    cell_format = self.format_section_header_right
                    value = value[1:]
                ws.write(row, idx, value, cell_format)
            else:
                ws.write(row, idx, None, cell_format)
        return row + 1

    def _render_line(self, ws, row, col, line_cols, ignore_empty=False):
        line_cols = ([''] * ((col or 0) + 1)) + line_cols
        for idx in range(0, self.table_end_column_num):
            if len(line_cols) > idx:
                if ignore_empty and line_cols[idx] == '':
                    continue
                cell_format = self.format_section_content_number
                value = line_cols[idx]
                if type(value) == str:
                    cell_format = self.format_section_content
                if type(value) in (tuple, list) and len(value):
                    if type(value[0]) in (int, float) and value[1] == 'number':
                        cell_format = self.format_section_content_number
                    if type(value[0]) in (int, float) and value[1] == 'percentage':
                        cell_format = self.format_section_content_percentage
                    value = value[0]
                ws.write(row, idx, value, cell_format)
            else:
                ws.write(row, idx, None, self.format_section_content)
        return row + 1

    def _apply_workbook_format(self, workbook):
        self.table_end_column = 'M'
        self.table_end_column_num = 13
        self.format_title = workbook.add_format({
            'font_size': 15,
            'font_color': '#333333',
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        self.format_header_title = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        self.format_header_content = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter'
        })
        self.format_section_title = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter',
            'top': 2,
            'bottom': 2,
        })
        self.format_section_header = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter',
            'top': 1,
            'bottom': 1,
        })
        self.format_section_header_right = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 1,
            'align': 'right',
            'valign': 'vcenter',
            'top': 1,
            'bottom': 1,
        })
        self.format_section_content = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter',
            'top': 1,
            'bottom': 1,
        })
        self.format_section_content_number = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 0,
            'align': 'right',
            'valign': 'vcenter',
            'top': 1,
            'bottom': 1,
            'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)'
        })
        self.format_section_content_percentage = workbook.add_format({
            'font_size': 11,
            'font_color': '#333333',
            'bold': 0,
            'align': 'right',
            'valign': 'vcenter',
            'top': 1,
            'bottom': 1,
            'num_format': '_(* 0.00_)"%";_(* (0.00)"%";_(* "-"??_);_(@_)'
        })
        self.format_error_line = workbook.add_format({
            'font_size': 11,
            'font_color': '#FF0000',
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'top': 1,
            'bottom': 1,
        })
