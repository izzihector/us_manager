odoo.define('bs_sarinah_portal.ppbk_report', function (require) {
  'use strict';

  const AbstractAction = require('web.AbstractAction');
  const core = require('web.core');
  const session = require('web.session');
  const Qweb = core.qweb;

  const PPBKReport = AbstractAction.extend({
    events: {
      'click .o_ppbk_report_action': '_onClickAction',
      'click .print-pdf': 'print_pdf',
      'click .print-xlsx': 'print_xlsx'
    },
    init: function (parent, action) {
      this.given_context = session.user_context;
      this.hasControlPanel = true;
      if (action.context) {
        this.given_context = action.context;
      }
      return this._super.apply(this, arguments);
    },
    willStart: function () {
      var proms = [this._super.apply(this, arguments), this.get_html()];
      return Promise.all(proms);
    },
    start: function () {
      let self = this;
      return this._super.apply(this, arguments).then(function () {
        self.set_html();
      })
    },
    renderSearch: function () {
      this.$buttonPrint = $(Qweb.render('bs_sarinah_portal.ppbk_button'));
    },
    update_cp: function () {
      var status = {
        title: 'PPBK Report',
        cp_content: {
          $buttons: this.$buttonPrint,
        },
      };
      return this.updateControlPanel(status);
    },
    get_html: function () {
      let self = this;
      return this._rpc({
        model: 'ppbk.report',
        method: 'get_html',
        args: [self.given_context],
      }).then(function (result) {
        self.html = result.html;
      })
    },
    set_html: function () {
      let self = this;
      self.$('.o_content').html(self.html);
      self.renderSearch();
      self.update_cp();
    },
    _reload: function () {
      let self = this;
      return this.get_html().then(function () {
        self.$el.html(self.html);
      });
    },
    print_pdf: function (e) {
      e.preventDefault();
      var self = this;
      self._rpc({
        model: 'ppbk.report',
        method: 'get_report_data',
        args: [[]],
        context: self.given_context,
      }).then(function (data) {
        var action = {
          'type': 'ir.actions.report',
          'report_type': 'qweb-pdf',
          'report_name': 'bs_sarinah_portal.ppbk_reporting',
          'report_file': 'bs_sarinah_portal.ppbk_reporting',
          'data': {'js_data': data},
          'context': {
            'active_model': 'ppbk.report',
            'landscape': 0,
            'from_js': true
          },
          'display_name': 'PPBK Report',
        };
        return self.do_action(action);
      });
    },
    print_xlsx: function (e) {
      e.preventDefault();
      var self = this;
      var action = {
        'type': 'ir.actions.report',
        'report_type': 'xlsx',
        'report_name': 'bs_sarinah_portal.xlsx_ppbk_report',
        'report_file': 'bs_sarinah_portal.xlsx_ppbk_report',
        'context': self.given_context,
        'display_name': 'PPBK Report',
      };
      return self.do_action(action);
    },
    _onClickAction: function (ev) {
      ev.preventDefault();
      return this.do_action({
        type: 'ir.actions.act_window',
        res_model: $(ev.currentTarget).data('model'),
        res_id: $(ev.currentTarget).data('res-id'),
        views: [[false, 'form']],
        target: 'current'
      });
    },
  });

  core.action_registry.add('bs_sarinah_portal.action_ppbk_report', PPBKReport);
  return PPBKReport;
});
