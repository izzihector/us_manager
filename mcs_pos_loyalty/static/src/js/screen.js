odoo.define('mcs_pos_loyalty.screen', function (require) {
	"use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var popup_widget = require('point_of_sale.popups');

    var field_utils = require('web.field_utils');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;

    models.load_fields('res.partner',['loyalty_id', 'date_of_birth']);

    var _super = models.Order;
    models.Order = models.Order.extend({

        get_new_total_points: function() {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.get_client().loyalty_points, this.pos.loyalty.rounding);
            }
        },

        get_new_points: function() {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.loyalty_points || 0, this.pos.loyalty.rounding);
            }
        },
        get_new_total_points: function() {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.get_client().loyalty_points, this.pos.loyalty.rounding);
            }
        },

        export_for_printing: function(){
            var json = _super.prototype.export_for_printing.apply(this,arguments);
            if (this.pos.loyalty && this.get_client()) {
                json.loyalty = {
                    rounding:     this.pos.loyalty.rounding || 1,
                    name:         this.pos.loyalty.name,
                    client:       this.get_client().name,
                    points_won  : this.get_new_points(),
                    points_spent: this.get_spent_points(),
                    points_total: this.get_new_total_points(),
                };
            }
            return json;
        },

        set_new_points: function(points){
            this.loyalty_points = points;
        },

    });

	screens.ClientListScreenWidget.include({

        save_client_details: function(partner) {
        var self = this;

        var fields = {};
        this.$('.client-details-contents .detail').each(function(idx,el){
            if (self.integer_client_details.includes(el.name)){
                var parsed_value = parseInt(el.value, 10);
                if (isNaN(parsed_value)){
                    fields[el.name] = false;
                }
                else{
                    fields[el.name] = parsed_value
                }
            }
            else{
                fields[el.name] = el.value || false;
            }
        });

        if (!fields.loyalty_id) {
            if (!fields.phone) {
                if (!fields.name) {
                    this.gui.show_popup('error', _t('A Customer Name Is Required'));
                    return;
                }
                if (!fields.email) {
                    this.gui.show_popup('error', _t('An Email Is Required'));
                    return;
                }
                this.gui.show_popup('error', _t('Phone Number Is Required'));
                return;
            }
        }

        if (this.uploaded_picture) {
            fields.image_1920 = this.uploaded_picture;
        }

        fields.id = partner.id || false;

        var contents = this.$(".client-details-contents");
        contents.off("click", ".button.save");


        rpc.query({
                model: 'res.partner',
                method: 'create_from_ui',
                args: [fields],
            })
            .then(function(partner_id){
                self.saved_client_details(partner_id);
            }).catch(function(error){
                error.event.preventDefault();
                var error_body = _t('Your Internet connection is probably down.');
                if (error.message.data) {
                    var except = error.message.data;
                    error_body = except.arguments && except.arguments[0] || except.message || error_body;
                }
                self.gui.show_popup('error',{
                    'title': _t('Error: Could not Save Changes'),
                    'body': error_body,
                });
                contents.on('click','.button.save',function(){ self.save_client_details(partner); });
            });
    },

        check_client_details: function(partner) {
            var self = this;
            rpc.query({
                model: 'res.partner',
                method: 'check_wallet_vernoss',
                args: [partner],
            })
            .then(function(partner_id){
                if (partner_id){
                    self.saved_client_details(partner_id);
                }
                else{
                    self.gui.show_popup('error',{
                        'title': _t('Error Vernoss'),
                        'body': "Loyalty ID not found!",
                    });
                }

            })
            .catch(function(error){
                error.event.preventDefault();
                var error_body = _t('Your Internet connection is probably down.');
                if (error.message.data) {
                    var except = error.message.data;
                    error_body = except.arguments && except.arguments[0] || except.message || error_body;
                }
                self.gui.show_popup('error',{
                    'title': _t('Error: Could not Check'),
                    'body': error_body,
                });
                contents.on('click','.button.check',function(){ self.check_client_details(partner); });
            });
        },
        display_client_details: function(visibility,partner,clickpos){
            this._super(visibility,partner,clickpos);

            var self = this;
            var contents = this.$('.client-details-contents');

            contents.off('click','.button.check');
            contents.on('click','.button.check',function(){ self.check_client_details(partner); });
        },
    });

    screens.PaymentScreenWidget.include({
        check_client_details: function() {
            var self = this;
            var order = this.pos.get_order();
            var serialized = order.export_as_JSON();
            rpc.query({
                model: 'pos.order',
                method: 'sendEarnTransaction',
                args: [serialized],
            })
            .then(function(result){
                if (result.point || result.point >= 0){
                    var client = self.pos.get_order().get_client();
                    if ( client ) {
                        client.loyalty_points = result.point;
                    }
                    self.pos.get_order().set_new_points(result.earn_points);
                    self.finalize_validation();
                }
                else{
                    self.gui.show_popup('error',{
                        'title': _t('Error Vernoss'),
                        'body': result.responseMessage,
                    });
                }

            })
            .catch(function(error){
//                error.event.preventDefault();
                var error_body = _t('Your Internet connection is probably down.');
                if (error.message.data) {
                    var except = error.message.data;
                    error_body = except.arguments && except.arguments[0] || except.message || error_body;
                }
                self.gui.show_popup('error',{
                    'title': _t('Error Vernoss: Could not Check'),
                    'body': error_body,
                });
            });
        },
        validate_order: function(force_validation) {
            if (this.order_is_valid(force_validation)) {

                var order = this.pos.get_order();

                if (order.get_won_points() > 0){
                    this.check_client_details();
                }
                else{
                    this.finalize_validation();
                }
            }

        }
    });

    var CustomLoyaltyPopup = popup_widget.extend({
        template: 'CustomLoyaltyPopup',
        show: function(){
            var self=this;
            this._super();

            var order = this.pos.get_order();
            var client = this.pos.get_client();
            var available_point = client ? client.loyalty_points : 0;
            var total_order = order.get_total_with_tax();

            var client_points = this.$el[0].querySelector('.client_points');
            client_points.innerHTML = available_point.toLocaleString();

            var redeemable_points = available_point > total_order ? total_order : available_point;

            var client_redeemable_points = this.$el[0].querySelector('.client_redeemable_points');
            client_redeemable_points.innerHTML = redeemable_points.toLocaleString();

            $('#client_points_redeem').attr({"max" : redeemable_points});
            $('#client_points_redeem').on('change',function(e){
                if($(this).val() > redeemable_points){
                        self.gui.show_popup('alert',{
                        'title': _t('Warning'),
                        'body':  _t('Points redeem cannot be greater than redeemable points'),
                    });
                }
            })

            $('.custom_cancel').on('click',function(){
                self.gui.close_popup();
            });

            var rewards = order.get_available_rewards();
            var reward = rewards[0];
            var product   = this.pos.db.get_product_by_id(reward.discount_product_id[0]);

            $('.confirm_redeem').on('click',function(){
                var discount = parseFloat($('#client_points_redeem').val());

                if (!product) {
                    self.gui.close_popup();
                    self.gui.current_screen.order_widget.numpad_state.reset();
                }

                order.add_product(product, {
                    price: -discount,
                    quantity: 1,
                    merge: false,
                    extras: { reward_id: reward.id },
                });
                 self.gui.close_popup();
                 self.gui.current_screen.order_widget.numpad_state.reset();
            });

        }
    });

    gui.define_popup({ name: 'custom_loyalty', widget: CustomLoyaltyPopup });

    gui.Gui.include({
        numpad_input: function(buffer, input, options) {
            var newbuf  = buffer.slice(0);
            options = options || {};
            var newbuf_float  = newbuf === '-' ? newbuf : field_utils.parse.float(newbuf);
            var decimal_point = _t.database.parameters.decimal_point;
            if (input === decimal_point) {
                if (options.firstinput) {
                    newbuf = "0.";
                }else if (!newbuf.length || newbuf === '-') {
                    newbuf += "0.";
                } else if (newbuf.indexOf(decimal_point) < 0){
                    newbuf = newbuf + decimal_point;
                }
            } else if (input === 'CLEAR') {
                newbuf = "";
            } else if (input === 'BACKSPACE') {
                newbuf = newbuf.substring(0,newbuf.length - 1);
            } else if (input === '+') {
                if ( newbuf[0] === '-' ) {
                    newbuf = newbuf.substring(1,newbuf.length);
                }
            } else if (input === '-') {
                if (options.firstinput) {
                    newbuf = '-0';
                } else if ( newbuf[0] === '-' ) {
                    newbuf = newbuf.substring(1,newbuf.length);
                } else {
                    newbuf = '-' + newbuf;
                }
            } else if (input[0] === '+' && !isNaN(parseFloat(input))) {
                newbuf = this.chrome.format_currency_no_symbol(newbuf_float + parseFloat(input));
            }else if (input[0] === '*' && !isNaN(parseFloat(input.substring(1,input.length)))) {
                newbuf = this.chrome.format_currency_no_symbol(newbuf_float * parseFloat(input.substring(1,input.length)));
            } else if (!isNaN(parseInt(input))) {
                if (options.firstinput) {
                    newbuf = '' + input;
                } else {
                    newbuf += input;
                }
            }
            if (newbuf === "-") {
                newbuf = "";
            }

            // End of input buffer at 12 characters.
            if (newbuf.length > buffer.length && newbuf.length > 12) {
                this.play_sound('bell');
                return buffer.slice(0);
            }

            return newbuf;
        },
    });

//    var LoyaltyButton = screens.ActionButtonWidget.extend({
//        template: 'LoyaltyButton',
//        button_click: function(){
//            var order  = this.pos.get_order();
//            var client = order.get_client();
//            if (!client) {
//                this.gui.show_screen('clientlist');
//                return;
//            }
//
//            var rewards = order.get_available_rewards();
//            if (rewards.length === 0) {
//                this.gui.show_popup('alert',{
//                    'title': _t('No Rewards Available'),
//                    'body':  _t('There are no rewards available for this customer as part of the loyalty program'),
//                });
//                return;
//            }
//            else {
//                var list = [];
//                for (var i = 0; i < rewards.length; i++) {
//                    list.push({
//                        label: rewards[i].name,
//                        item:  rewards[i],
//                    });
//                }
//                this.gui.show_popup('custom_loyalty', {
//                    'title': _t("Customize Loyalty"),
//                });
//            }
//        },
//    });

//    screens.define_action_button({
//        'name': 'loyalty',
//        'widget': LoyaltyButton,
//        'condition': function(){
//            return this.pos.loyalty && this.pos.loyalty.rewards.length;
//        },
//    });


});