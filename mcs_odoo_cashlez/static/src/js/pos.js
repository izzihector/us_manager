odoo.define("mcs_odoo_cashlez.pos", function (require) {
    "use strict";

    var gui = require('point_of_sale.gui');
    var screens = require('point_of_sale.screens');

    var order_screen = gui.Gui.prototype.screen_classes.filter(function(el) { return el.name == 'order_screen'})[0].widget
    order_screen.include({
//    screens.OrderScreenWidget.include({

        events: _.extend({}, order_screen.prototype.events, {
            "click .button.cashlez": "click_cashlez",
        }),
        click_cashlez: function () {
            if(typeof Android !== "undefined" && Android !== null) {
                Android.openHistory();
            } else {
                alert("Not viewing in webview");
            }
        },
    });

});