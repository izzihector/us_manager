odoo.define('pos_manager_validation.pos_manager_validation', function (require) {
"use strict";

var chrome = require('point_of_sale.chrome');
var core = require('web.core');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');

var _t = core._t;
var _lt = core._lt;


chrome.OrderSelectorWidget.include({
    validateByManager: function(action, event, $el) {
        var self = this;
        var managerUserIDs = this.pos.config.manager_user_ids;
        var users = this.pos.users;

        this.gui.show_popup('password', {
            'title': _t('Manager Validation'),
            confirm: function(password) {
                this.pos.manager = false;
                for (var i = 0; i < users.length; i++) {
                    if (managerUserIDs.indexOf(users[i].id) > -1
                            && password === (users[i].pos_security_pin || '')) {
                        this.pos.manager = users[i];
                    }
                }
                if (this.pos.manager) {
                    self.deleteorder_click_handler(event, $el)
                } else {
                    self.gui.show_popup('error', _t('Incorrect Password'));
                }
            },
        });
    },

    deleteorder_click_handler: function(event, $el) {
        var managerUserIDs = this.pos.config.manager_user_ids;
        var user = this.pos.manager || this.pos.get_cashier();

        if (this.pos.config.iface_validate_delete_order
                && managerUserIDs.indexOf(user.id) === -1) {
            this.validateByManager('deleteOrder', event, $el);
        } else {
            this._super(event, $el);
            this.pos.manager = false;
        }
    },
});

chrome.Chrome.include({
    build_widgets: function() {
        for (var i = 0; i < this.widgets.length; i++) {
            var widget = this.widgets[i];
            if (widget.name === 'close_button') {
                widget.args = {
                    label: _lt('Close'),
                    action: function() {
                        var self = this;
                        if (!this.confirmed) {
                            this.$el.addClass('confirm');
                            this.$el.text(_t('Confirm'));
                            this.confirmed = setTimeout(function() {
                                self.$el.removeClass('confirm');
                                self.$el.text(_t('Close'));
                                self.confirmed = false;
                            }, 2000);
                        } else {
                            this.gui.close(this);
                        }
                    },
                }
            }

        }
        this._super();
    },
});

models.NumpadState = models.NumpadState.extend({
    appendNewChar: function(newChar) {
        var oldBuffer = this.get('buffer');
        if (oldBuffer === '0') {
            var buffer = newChar;
        } else if (oldBuffer === '-0') {
            var buffer = '-' + newChar;
        } else {
            var buffer = (this.get('buffer')) + newChar;
        }
        this.trigger('set_value', buffer);
    },
});

screens.OrderWidget.include({
    validateByManager: function(action, val) {
        var self = this;
        var managerUserIDs = this.pos.config.manager_user_ids;
        var users = this.pos.users;

        this.gui.show_popup('password', {
            'title': _t('Manager Validation'),
            confirm: function(password) {
                this.pos.manager = false;
                for (var i = 0; i < users.length; i++) {
                    if (managerUserIDs.indexOf(users[i].id) > -1
                            && password === (users[i].pos_security_pin || '')) {
                        this.pos.manager = users[i];
                    }
                }
                if (this.pos.manager) {
                    self.set_value(val);
                } else {
                    self.gui.show_popup('error', _t('Incorrect Password'));
                }
            },
        });
    },

    set_value: function(val) {
        var managerUserIDs = this.pos.config.manager_user_ids;
        var mode = this.numpad_state.get('mode');
        var order = this.pos.get_order();
        var orderline = order.get_selected_orderline();
        var user = this.pos.manager || this.pos.get_cashier();

        if (this.pos.config.iface_validate_decrease_quantity && orderline
                && parseFloat(orderline.quantity) > parseFloat(val)
                && mode === 'quantity' && managerUserIDs.indexOf(user.id) === -1) {
            this.validateByManager('decreaseQuantity', val);
        } else {
            this.numpad_state.set({'buffer': val})
            this._super(val);
            this.pos.manager = false;
        }
    },
});

screens.NumpadWidget.include({
    validateByManager: function(action, event) {
        var self = this;
        var managerUserIDs = this.pos.config.manager_user_ids;
        var users = this.pos.users;

        this.gui.show_popup('password', {
            'title': _t('Manager Validation'),
            confirm: function(password) {
                this.pos.manager = false;
                for (var i = 0; i < users.length; i++) {
                    if (managerUserIDs.indexOf(users[i].id) > -1
                            && password === (users[i].pos_security_pin || '')) {
                        this.pos.manager = users[i];
                    }
                }
                if (this.pos.manager) {
                    if (action === 'deleteOrderLine' || action === 'decreaseQuantity') {
                        self.clickDeleteLastChar();
                    } else {
                        self.clickChangeMode(event);
                    }
                } else {
                    self.gui.show_popup('error', _t('Incorrect Password'));
                }
            },
        });
    },

    clickDeleteLastChar: function() {
        var buffer = this.state.get('buffer');
        var managerUserIDs = this.pos.config.manager_user_ids;
        var mode = this.state.get('mode');
        var user = this.pos.manager || this.pos.get_cashier();

        if (this.pos.config.iface_validate_delete_orderline && buffer === ''
                && mode === 'quantity' && managerUserIDs.indexOf(user.id) === -1) {
            this.validateByManager('deleteOrderLine');
        } else if (this.pos.config.iface_validate_decrease_quantity && buffer !== ''
                   && mode === 'quantity' && managerUserIDs.indexOf(user.id) === -1) {
            this.validateByManager('decreaseQuantity');
        } else {
            this._super();
            this.pos.manager = false;
        }
    },

    clickChangeMode: function(event) {
        var managerUserIDs = this.pos.config.manager_user_ids;
        var newMode = event.currentTarget.attributes['data-mode'].value;
        var user = this.pos.manager || this.pos.get_cashier();

        if (this.pos.config.iface_validate_discount && newMode === 'discount'
                && managerUserIDs.indexOf(user.id) === -1) {
            this.validateByManager('changeMode', event);
        } else if (this.pos.config.iface_validate_price && newMode === 'price'
                   && managerUserIDs.indexOf(user.id) === -1) {
            this.validateByManager('changeMode', event);
        } else {
            this._super(event);
            this.pos.manager = false;
        }
    },
});

gui.Gui.include({
    validateByManager: function(action, close_button, screen_name, params, refresh, skip_close_popup) {
        var self = this;
        var managerUserIDs = this.pos.config.manager_user_ids;
        var users = this.pos.users;

        this.show_popup('password', {
            'title': _t('Manager Validation'),
            confirm: function(password) {
                this.pos.manager = false;
                for (var i = 0; i < users.length; i++) {
                    if (managerUserIDs.indexOf(users[i].id) > -1
                            && password === (users[i].pos_security_pin || '')) {
                        this.pos.manager = users[i];
                    }
                }
                if (this.pos.manager) {
                    if (action === 'showScreen') {
                        self.show_screen(screen_name, params, refresh, skip_close_popup);
                    } else {
                        self.close(close_button);
                    }
                } else {
                    self.show_popup('error', _t('Incorrect Password'));
                }
            },
        });
    },

    close: function(close_button) {
        var managerUserIDs = this.pos.config.manager_user_ids;
        var user = this.pos.manager || this.pos.get_cashier();

        if (this.pos.config.iface_validate_close && managerUserIDs.indexOf(user.id) === -1) {
            this.validateByManager('close', close_button);
        } else {
            clearTimeout(close_button.confirmed);
            this._super(close_button);
            this.pos.manager = false;
        }
    },

    show_screen: function(screen_name, params, refresh, skip_close_popup) {
        var managerUserIDs = this.pos.config.manager_user_ids;
        var user = this.pos.manager || this.pos.get_cashier();

        if (this.pos.config.iface_validate_payment && screen_name === 'payment'
                && managerUserIDs.indexOf(user.id) === -1) {
            this.validateByManager('showScreen', false, screen_name, params, refresh, skip_close_popup);
        } else {
            this._super(screen_name, params, refresh, skip_close_popup);
            this.pos.manager = false;
        }
    },
});


});
