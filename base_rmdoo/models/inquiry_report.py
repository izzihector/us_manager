# -*- coding: utf-8 -*-

from odoo import models, fields, api, http
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import calendar, datetime, odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class InquiryAbstract(models.AbstractModel):
    _name = 'inquiry.abstract'
    _description = 'Inquiry Abstract'

    def _get_daterange(self, date=datetime.datetime.now(), daterange='monthly'):
        year = fields.Date.from_string(date).strftime('%Y')
        month = fields.Date.from_string(date).strftime('%m')
        day = fields.Date.from_string(date).strftime('%d')
        if daterange == 'daily':
            date_from = date_to = '{}-{}-{}'.format(year, month, day)
        elif daterange == 'monthly':
            date_from = '{}-{}-01'.format(year, month)
            date_to = '{}-{}-{}'.format(year, month, str(calendar.monthrange(int(year), int(month))[1]).zfill(2))
        elif daterange == 'yearly':
            date_from = '{}-01-01'.format(year)
            date_to = '{}-12-31'.format(year)
        else:
            raise UserError('daterange not defined')
        return date_from, date_to
    
    def _get_default(self, field, model=False):
        try:
            lines_obj = self.env[model or self.lines._name]
            lines = lines_obj.read_group([('id', '!=', False)], [field], [field])
            return [line and line[field] and line[field][0] for line in lines]
        except:
            return []
    
    def _get_domain(self, field, model=False):
        return "[('id','in',%s)]" % (self._get_default(field, model))
    
    @api.depends()
    def _defocus(self):
        self.defocus = """
        <script type="text/javascript">
        $(function () {
            $('input[type=text]').blur();
        });
        </script>
        """
        
    defocus = fields.Html('HTML', sanitize=False, compute='_defocus')
    result = fields.Html('HTML', sanitize=False, readonly=True, default='''
        <div style="display:block;text-align:center;" class="alert alert-info" role="alert">
            Please click <i class="fa fa-fw o_button_icon fa-magic"/> above to generate result.
        </div>
    ''')
    is_result = fields.Boolean('Resulted')
    
    
    def do_print(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'print_view',
        }
        
    
    def add_to_dash(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'add_to_dash',
        }
        
    
    def do_reload(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class InquiryReport(models.TransientModel):
    _name = 'inquiry.report'
    _inherit = ['inquiry.abstract']
    _description = 'Inquiry Report'
    
    def _get_first_doy(self):
        now = datetime.datetime.now()
        return '%s-01-01' % (now.year)
    
    def _get_last_doy(self):
        now = datetime.datetime.now()
        return '%s-12-31' % (now.year)
    
    @api.depends('date_from', 'date_to', 'create_uids', 'write_uids')
    def _get_lines(self):
        for line in self:
            lines_obj = self.env[line.lines._name]
            line.lines = lines_obj.search([
                ('create_date', '>=', line.date_from),
                ('create_date', '<=', line.date_to),
                ('create_uid', 'in', [user.id for user in line.create_uids]) if line.create_uids else ('id', '!=', False),
                ('write_uid', 'in', [user.id for user in line.write_uids]) if line.write_uids else ('id', '!=', False),
            ])
            
    @api.depends('lines')
    def _get_html(self):
        for line in self:
            line.html = """
            <script>
                var data = [{
                    x: ['DUMMY', 'PLOTLY', 'GRAPH'],
                    y: [20, 10, 30],
                    name: 'DATA 1',
                    type: 'bar'
                }, {
                    x: ['DUMMY', 'PLOTLY', 'GRAPH'],
                    y: [80, 90, 70],
                    name: 'DATA 2',
                    type: 'bar'
                }];

                Plotly.newPlot('plotly-container', data, {barmode:'stack'}, {responsive:true});
            </script>
            <div id="plotly-container" class="plotly-container"/>
            """
            
    def _generate_pivot(self, record, renderer='Table', rows=[], cols=[], aggregator='Count', vals=[], hidden_attributes=['ID'], visible_attributes=[], container='plotly-pivot-container', show_button=False):
        fields_obj = self.env['ir.model.fields']
        model = record._name
        
        if (visible_attributes == 'used_only') or not show_button:
            visible_attributes = []
            visible_attributes.append(rows)
            visible_attributes.append(cols)
            visible_attributes.append(vals)
            visible_attributes = [subitem for sublist in visible_attributes for subitem in sublist]
        
        pivot = """
        <script>
            $(function(){
                $.post('/pivot/json', {
                    'csrf_token':"%s",
                    'model':"%s",
                    'record':"%s",
                    'fields':"%s"
                }, function (data) {
                    var lines = JSON.parse(data);
                    $("#%s").pivotUI(
                        lines,
                        {
                            renderers: $.extend(
                                $.pivotUtilities.renderers,
                                $.pivotUtilities.subtotal_renderers,
                                $.pivotUtilities.d3_renderers,
                                $.pivotUtilities.plotly_renderers
                            ),
                            rendererName: "%s",
                            dataClass: $.pivotUtilities.SubtotalPivotData,
                            aggregator: $.pivotUtilities.aggregator,
                            aggregatorName: "%s",
                            hiddenAttributes: %s,
                            autoSortUnusedAttrs: true,
                            unusedAttrsVertical: false,
                            rendererOptions: {
                                collapseRowsAt: 0,
                                collapseColsAt: 0
                            },
                            vals: %s,
                            rows: %s,
                            cols: %s
                        }
                    );
                    $('#%s .pvtUiCell').toggle();
                });
             });
        </script>
        %s
        <div id="%s" class="plotly-container"><img src="/base_rmdoo/static/src/img/ajax-loader.gif"/></div>
        """ % (
            http.request.csrf_token(),
            model,
            record.ids,
            visible_attributes,
            container,
            renderer,
            aggregator,
            [(fields_obj._get(model, hidden_attribute) and fields_obj._get(model, hidden_attribute).field_description or hidden_attribute) for hidden_attribute in hidden_attributes],
            [(fields_obj._get(model, val) and fields_obj._get(model, val).field_description or val) for val in vals],
            [(fields_obj._get(model, row) and fields_obj._get(model, row).field_description or row) for row in rows],
            [(fields_obj._get(model, col) and fields_obj._get(model, col).field_description or col) for col in cols],
            container,
            ('''<div class="plotly-container-btn"><a onclick="$('#%s .pvtUiCell').toggle(100);"><i class="fa fa-line-chart"/></a></div>''' % (container)) if show_button else '',
            container
        )
        return pivot
            
    @api.depends('lines')
    def _get_pivot(self, renderer='Table', rows=[], cols=[], aggregator='Count', vals=[], hidden_attributes=['ID'], visible_attributes=[], container='plotly-pivot-container', show_button=False):
        for line in self:
            line.pivot_on = (self.env['ir.config_parameter'].sudo().get_param('rmdoo.pivot.on') == 'on')
            if line.pivot_on:
                if self.env['ir.config_parameter'].sudo().get_param('rmdoo.pivot.button') == 'on':
                    show_button = True
                elif self.env['ir.config_parameter'].sudo().get_param('rmdoo.pivot.button') == 'off':
                    show_button = False
                line.pivot = self._generate_pivot(line.lines, renderer, rows, cols, aggregator, vals, hidden_attributes, visible_attributes, container=container, show_button=show_button)
            else:
                line.pivot = ''
    
    name = fields.Char('Name', default=_description, readonly=True)
    date_from = fields.Date('Date From', default=lambda self:self._get_daterange(daterange='monthly')[0], required=True)
    date_to = fields.Date('Date To', default=lambda self:self._get_daterange(daterange='monthly')[1], required=True)
    create_uids = fields.Many2many('res.users', '%s_create_uids_rel' % (_name.replace('.', '_')), string='Created By', domain=lambda self:self._get_domain('create_uid'))  # , default=_get_create_uids_default)
    write_uids = fields.Many2many('res.users', '%s_write_uids_rel' % (_name.replace('.', '_')), string='Last Updated By', domain=lambda self:self._get_domain('write_uid'))  # , default=_get_write_uids_default)
    lines = fields.Many2many('product.product', string='Product', compute='_get_lines')
    html = fields.Html('HTML', sanitize=False, compute='_get_html')
    pivot = fields.Html('Pivot', sanitize=False, compute='_get_pivot')
    pivot_on = fields.Boolean('Pivot On?', compute='_get_pivot')
        
    
    def list_view(self):
        if self.ensure_one():
            return {
                'name': 'Inquiries Report',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'view_mode': 'tree,form,pivot',
                'src_model': self._name,
                'res_model': self.lines._name,
                'domain': "[('id','in',%s)]" % ([line.id for line in self.lines]),
                'context': {
                    'create': False,
                    'edit': False,
                    'delete': False,
                },
            }
        else:
            return False
