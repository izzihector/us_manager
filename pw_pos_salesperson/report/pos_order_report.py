# -*- coding: utf-8 -*-
from odoo import models, fields, tools


class PosOrderReport(models.Model):
    _inherit = "report.pos.order"

    saleperson_id = fields.Many2one('res.users', string='Salesperson', readony=True)

    def _select(self):
        return super(PosOrderReport, self)._select() + ',l.user_id AS saleperson_id'

    def _group_by(self):
        return super(PosOrderReport, self)._group_by() + ',l.user_id'

        
    # hs - add product brand & product owner on pivot
    product_brand = fields.Char("Product Brand")
    product_owner = fields.Char("Product Owner")
    
    def _select(self):
        # hs - add product brand & product owner on pivot, select product brand dan owner
        return """
            SELECT
                MIN(l.id) AS id,
                COUNT(*) AS nbr_lines,
                s.date_order AS date,
                SUM(l.qty) AS product_qty,
                SUM(l.qty * l.price_unit / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) AS price_sub_total,
                SUM(ROUND((l.qty * l.price_unit) * (100 - l.discount) / 100 / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END, cu.decimal_places)) AS price_total,
                SUM((l.qty * l.price_unit) * (l.discount / 100) / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) AS total_discount,
                CASE
                    WHEN SUM(l.qty * u.factor) = 0 THEN NULL
                    ELSE (SUM(l.qty*l.price_unit / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END)/SUM(l.qty * u.factor))::decimal
                END AS average_price,
                SUM(cast(to_char(date_trunc('day',s.date_order) - date_trunc('day',s.create_date),'DD') AS INT)) AS delay_validation,
                s.id as order_id,
                s.partner_id AS partner_id,
                s.state AS state,
                s.user_id AS user_id,
                s.location_id AS location_id,
                s.company_id AS company_id,
                s.sale_journal AS journal_id,
                l.product_id AS product_id,
                pt.categ_id AS product_categ_id,
                p.product_tmpl_id,
                pb.name AS product_brand,
                o.name AS product_owner,
                ps.config_id,
                pt.pos_categ_id,
                s.pricelist_id,
                s.session_id,
                s.account_move IS NOT NULL AS invoiced
        """

    def _from(self):
        # hs - add product brand & product owner on pivot, join product brand dan owner
        return """
            FROM pos_order_line AS l
                INNER JOIN pos_order s ON (s.id=l.order_id)
                LEFT JOIN product_product p ON (l.product_id=p.id)
                LEFT JOIN product_template pt ON (p.product_tmpl_id=pt.id)
                LEFT JOIN product_brand pb ON (pt.brand_id=pb.id)
                LEFT JOIN res_partner o ON (pt.owner_id=o.id)
                LEFT JOIN uom_uom u ON (u.id=pt.uom_id)
                LEFT JOIN pos_session ps ON (s.session_id=ps.id)
                LEFT JOIN res_company co ON (s.company_id=co.id)
                LEFT JOIN res_currency cu ON (co.currency_id=cu.id)
        """

    def _group_by(self):
        # hs - add product brand & product owner on pivot, group by product brand dan owner
        return """
            GROUP BY
                s.id, s.date_order, s.partner_id,s.state, pt.categ_id,
                s.user_id, s.location_id, s.company_id, s.sale_journal,
                s.pricelist_id, s.account_move, s.create_date, s.session_id,
                l.product_id,
                pt.categ_id, pt.pos_categ_id,
                p.product_tmpl_id,
                pb.id,
                o.id,
                ps.config_id
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._group_by())
        )
