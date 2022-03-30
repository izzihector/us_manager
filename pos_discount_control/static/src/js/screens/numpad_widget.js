odoo.define('pos_discount_control.numpad_widget', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var NumpadWidget = screens.NumpadWidget;

    NumpadWidget.include({
        applyAccessRights: function() {
            // Call super to render the price control
            this._super();
            var cashier = this.pos.get('cashier') || this.pos.get_cashier();
            var has_discount_control_rights = !this.pos.config.restrict_discount_control || cashier.role == 'manager';
            this.$el.find('.mode-button[data-mode="discount"]')
                .toggleClass('disabled-mode', !has_discount_control_rights)
                .prop('disabled', !has_discount_control_rights);
            if (!has_discount_control_rights && this.state.get('mode')=='discount'){
                this.state.changeMode('quantity');
            }
        },
    });
});
