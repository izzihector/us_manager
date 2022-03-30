# -*- coding: utf-8 -*-
from odoo.fields import datetime,date
from datetime import timedelta
import pytz
from odoo.addons.ks_dashboard_ninja.lib import ks_date_filter_selections


def ks_get_date_range_from_fiscal(date_state,timezone,type, self):
    ks_date_data = {}
    ks_date = datetime.now()
    ks_year = date.year
    fiscal_year_date = self.env.company.compute_fiscalyear_dates(ks_date)
    fiscal_year_start_date = fiscal_year_date['date_from']
    fiscal_year_end_date = fiscal_year_date['date_to']
    fiscal_year_start_date = datetime(fiscal_year_start_date.year, fiscal_year_start_date.month, fiscal_year_start_date.day)
    fiscal_year_end_date = datetime(fiscal_year_end_date.year, fiscal_year_end_date.month, fiscal_year_end_date.day)
    if date_state == 'previous':
        ks_year = fiscal_year_start_date.year
        ks_year -= 1
        fiscal_year_start_date = datetime(ks_year, fiscal_year_start_date.month, fiscal_year_start_date.day)
        fiscal_year_end_date = datetime(ks_year + 1, fiscal_year_end_date.month, fiscal_year_end_date.day) - timedelta(
            seconds=1)
    elif date_state == 'next':
        ks_year = fiscal_year_start_date.year
        ks_year += 1
        fiscal_year_start_date = datetime(ks_year, fiscal_year_start_date.month, fiscal_year_start_date.day)
        fiscal_year_end_date = datetime(ks_year + 1, fiscal_year_end_date.month, fiscal_year_end_date.day) - timedelta(
            seconds=1)

    if type == 'date':
        ks_date_data["selected_start_date"] = fiscal_year_start_date
        ks_date_data["selected_end_date"] = fiscal_year_end_date
    else:
        ks_date_data["selected_start_date"] = ks_date_filter_selections.ks_convert_into_utc(fiscal_year_start_date, timezone)
        ks_date_data["selected_end_date"] = ks_date_filter_selections.ks_convert_into_utc(fiscal_year_end_date, timezone)
    return ks_date_data


# ks_date_filter_selections.ks_date_series_t= ks_date_series_t
ks_date_filter_selections.ks_get_date_range_from_fiscal = ks_get_date_range_from_fiscal