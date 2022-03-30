odoo.define('pos_open_cash_drawer', function (require) {
"use strict";
var screens = require('point_of_sale.screens');
    
    screens.ActionpadWidget.include({
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.js_cashdrawer').click(function(){
                self.pos.proxy.printer.open_cashbox();
            });
        }
    });
});

