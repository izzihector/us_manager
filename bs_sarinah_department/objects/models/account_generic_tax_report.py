# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.tools.translate import _
from odoo.tools.misc import formatLang

class AccountGenericTaxReport(models.AbstractModel):
    _inherit = 'account.generic.tax.report'

    filter_branch = True
    filter_department = True

    def _compute_from_amls(self, options, dict_to_fill, period_number):
        """ Fills dict_to_fill with the data needed to generate the report.
        """
        if options.get('tax_grids'):
            self._compute_from_amls_grids(options, dict_to_fill, period_number)
        else:
            self._compute_from_amls_taxes(options, dict_to_fill, period_number)

    def _compute_from_amls_grids(self, options, dict_to_fill, period_number):
        """ Fills dict_to_fill with the data needed to generate the report, when
        the report is set to group its line by tax grid.
        """
        tables, where_clause, where_params = self._query_get(options)
        
        branch_list = []
        department_list = []


        if options.get('branch_ids'):
            branch_list = options.get('branch_ids')
        
        if options.get('department_ids'):
            department_list = options.get('department_ids')
        
        account_query = ''
        if branch_list:
            if len(branch_list) == 1:
                branch = branch_list[0]
                account_query = """ AND account_move_line.branch_id = %s """ % (str(branch))
            else:
                branches = tuple(list(set(branch_list)))
                account_query = """ AND account_move_line.branch_id in %s """ % (str(tuple(branches)))

        if department_list:
            if len(department_list) == 1:
                department = department_list[0]
                account_query = """ AND account_move_line.department_id = %s """ % (str(department))
            else:
                departments = tuple(list(set(department_list)))
                account_query = """ AND account_move_line.department_id in %s """ % (str(tuple(departments)))

        sql = """SELECT account_tax_report_line_tags_rel.account_tax_report_line_id,
                        SUM(coalesce(account_move_line.balance, 0) * CASE WHEN acc_tag.tax_negate THEN -1 ELSE 1 END
                                                 * CASE WHEN account_journal.type = 'sale' THEN -1 ELSE 1 END
                                                 * CASE WHEN account_move.type in ('in_refund', 'out_refund') THEN -1 ELSE 1 END)
                        AS balance
                 FROM """ + tables + """
                 JOIN account_move
                 ON account_move_line.move_id = account_move.id
                 JOIN account_account_tag_account_move_line_rel aml_tag
                 ON aml_tag.account_move_line_id = account_move_line.id
                 JOIN account_journal
                 ON account_move.journal_id = account_journal.id
                 JOIN account_account_tag acc_tag
                 ON aml_tag.account_account_tag_id = acc_tag.id
                 JOIN account_tax_report_line_tags_rel
                 ON acc_tag.id = account_tax_report_line_tags_rel.account_account_tag_id
                 WHERE account_move_line.tax_exigible """ + account_query + """ AND """ + where_clause + """
                 GROUP BY account_tax_report_line_tags_rel.account_tax_report_line_id
        """

        self.env.cr.execute(sql, where_params)

        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in dict_to_fill:
                dict_to_fill[result[0]]['periods'][period_number]['balance'] = result[1]
                dict_to_fill[result[0]]['show'] = True


    def _sql_cash_based_branch_taxes(self, branch_list, department_list):
        account_query = ''
        if len(branch_list) == 1:
            branch = branch_list[0]
            account_query += """ AND "account_move_line".branch_id = %s""" % (str(branch))
        elif len(branch_list) > 1:
            branches = tuple(list(set(branch_list)))
            account_query += """ AND "account_move_line".branch_id in %s""" % (str(tuple(branches)))
        if len(department_list) == 1:
            department = department_list[0]
            account_query += """ AND "account_move_line".department_id = %s""" % (str(department))
        elif len(department_list) > 1:
            departments = tuple(list(set(department_list)))
            account_query += """ AND "account_move_line".department_id in %s""" % (str(tuple(departments)))
        sql = """SELECT id, sum(base) AS base, sum(net) AS net FROM (
                    SELECT tax.id,
                    SUM("account_move_line".balance) AS base,
                    0.0 AS net
                    FROM account_move_line_account_tax_rel rel, account_tax tax, %s
                    WHERE (tax.tax_exigibility = 'on_payment')
                    AND (rel.account_move_line_id = "account_move_line".id)
                    AND (tax.id = rel.account_tax_id)
                    AND ("account_move_line".tax_exigible)
                    AND %s
                    GROUP BY tax.id
                    UNION
                    SELECT tax.id,
                    0.0 AS base,
                    SUM("account_move_line".balance) AS net
                    FROM account_tax tax, %s
                    WHERE (tax.tax_exigibility = 'on_payment')
                    AND "account_move_line".tax_line_id = tax.id
                    AND ("account_move_line".tax_exigible)
                    AND %s
                    """ + account_query + """
                    GROUP BY tax.id) cash_based
                    GROUP BY id;"""
        return sql

    def _sql_tax_amt_regular_branch_taxes(self, branch_list, department_list):
        account_query = ''
        if len(branch_list) == 1:
            branch = branch_list[0]
            account_query += """ AND "account_move_line".branch_id = %s""" % (str(branch))
        elif len(branch_list) > 1:
            branches = tuple(list(set(branch_list)))
            account_query += """ AND "account_move_line".branch_id in %s""" % (str(tuple(branches)))
        if len(department_list) == 1:
            department = department_list[0]
            account_query += """ AND "account_move_line".department_id = %s""" % (str(department))
        elif len(department_list) > 1:
            departments = tuple(list(set(department_list)))
            account_query += """ AND "account_move_line".department_id in %s""" % (str(tuple(departments)))
        sql = """SELECT "account_move_line".tax_line_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
                    FROM account_tax tax, %s
                    WHERE %s AND tax.tax_exigibility = 'on_invoice' AND tax.id = "account_move_line".tax_line_id """+ account_query +""" 
                    GROUP BY "account_move_line".tax_line_id"""
        return sql

    def _sql_net_amt_regular_branch_taxes(self, branch_list, department_list):
        account_query = ''
        if len(branch_list) == 1:
            branch = branch_list[0]
            account_query += """ AND "account_move_line".branch_id = %s""" % (str(branch))
        elif len(branch_list) > 1:
            branches = tuple(list(set(branch_list)))
            account_query += """ AND "account_move_line".branch_id in %s""" % (str(tuple(branches)))
        if len(department_list) == 1:
            department = department_list[0]
            account_query += """ AND "account_move_line".department_id = %s""" % (str(department))
        elif len(department_list) > 1:
            departments = tuple(list(set(department_list)))
            account_query += """ AND "account_move_line".department_id in %s""" % (str(tuple(departments)))
        sql = """SELECT r.account_tax_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
                 FROM %s
                 INNER JOIN account_move_line_account_tax_rel r ON ("account_move_line".id = r.account_move_line_id)
                 INNER JOIN account_tax t ON (r.account_tax_id = t.id)
                 WHERE %s AND t.tax_exigibility = 'on_invoice' """+ account_query +""" GROUP BY r.account_tax_id"""
        return sql

    def _compute_from_amls_taxes(self, options, dict_to_fill, period_number):
        """ Fills dict_to_fill with the data needed to generate the report, when
        the report is set to group its line by tax grid.
        """
        if options.get('branch_ids') or options.get('department_ids'):
            branch = options.get('branch_ids')
            department = options.get('department_ids')
            sql = self._sql_cash_based_branch_taxes(branch, department)
        else:
            sql = self._sql_cash_based_taxes()

        tables, where_clause, where_params = self._query_get(options)
        query = sql % (tables, where_clause, tables, where_clause)
        self.env.cr.execute(query, where_params + where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in dict_to_fill:
                dict_to_fill[result[0]]['periods'][period_number]['net'] = result[1]
                dict_to_fill[result[0]]['periods'][period_number]['tax'] = result[2]
                dict_to_fill[result[0]]['show'] = True

        if options.get('branch_ids') or options.get('department_ids'):
            branch = options.get('branch_ids')
            department = options.get('department_ids')
            sql = self._sql_net_amt_regular_branch_taxes(branch, department)
            query = sql % (tables, where_clause)
            self.env.cr.execute(query, where_params)
        else:
            sql = self._sql_net_amt_regular_taxes()
            query = sql % (tables, where_clause, tables, where_clause)
            self.env.cr.execute(query, where_params + where_params)


        for tax_id, balance in self.env.cr.fetchall():
            if tax_id in dict_to_fill:
                dict_to_fill[tax_id]['periods'][period_number]['net'] += balance
                dict_to_fill[tax_id]['show'] = True

        if options.get('branch_ids') or options.get('department_ids'):
            branch = options.get('branch_ids')
            department = options.get('department_ids')
            sql = self._sql_tax_amt_regular_branch_taxes(branch, department)
        else:
            sql = self._sql_tax_amt_regular_taxes()

        query = sql % (tables, where_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()

        for result in results:
            if result[0] in dict_to_fill:
                dict_to_fill[result[0]]['periods'][period_number]['tax'] = result[1]
                dict_to_fill[result[0]]['show'] = True
