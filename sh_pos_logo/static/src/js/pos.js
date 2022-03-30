odoo.define("sh_pos_logo.screens", function (require) {
    "use strict";

    var gui = require("point_of_sale.gui");
    var models = require("point_of_sale.models");
    var screens = require("point_of_sale.screens");
    var core = require("web.core");
    var PopupWidget = require("point_of_sale.popups");
    var rpc = require("web.rpc");
    var ActionManager = require("web.ActionManager");
    var Session = require("web.session");
    var PosBaseWidget = require("point_of_sale.BaseWidget");
    var gui = require("point_of_sale.gui");
    var models = require("point_of_sale.models");
    var chrome = require("point_of_sale.chrome");

    var QWeb = core.qweb;
    var _t = core._t;

    models.load_fields("res.company", ["sh_pos_global_header_logo", "global_header_logo", "sh_pos_global_logo", "global_receipt_logo"]);

    chrome.Chrome.include({
        get_header_logo_url: function (config) {
            return window.location.origin + "/web/image?model=pos.config&field=header_logo&id=" + config;
        },
        get_global_header_logo_url: function (company) {
            return window.location.origin + "/web/image?model=res.company&field=global_header_logo&id=" + company;
        },
    });

    screens.ReceiptScreenWidget.include({
        get_receipt_logo_url: function (config) {
            return window.location.origin + "/web/image?model=pos.config&field=receipt_logo&id=" + config;
        },
        get_receipt_global_logo_url: function (company) {
            return window.location.origin + "/web/image?model=res.company&field=global_receipt_logo&id=" + company;
        },
        get_receipt_render_env: function () {
            var order = this.pos.get_order();
            var render_env = this._super();
            render_env.receipt_logo_url = this.get_receipt_logo_url(this.pos.config.id);
            render_env.receipt_global_logo_url = this.get_receipt_global_logo_url(this.pos.company.id);
            return render_env;
//            return {
//                widget: this,
//                pos: this.pos,
//                order: order,
//                receipt: order.export_for_printing(),
//                orderlines: order.get_orderlines(),
//                paymentlines: order.get_paymentlines(),
//                receipt_logo_url: this.get_receipt_logo_url(this.pos.config.id),
//                receipt_global_logo_url: this.get_receipt_global_logo_url(this.pos.company.id),
//            };
        },
    });
});
