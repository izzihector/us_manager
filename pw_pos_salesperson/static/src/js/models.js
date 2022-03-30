odoo.define('pos_salesperson.pos_salesperson', function(require){
    
	var models = require('point_of_sale.models');
	var core = require('web.core');
	var gui = require('point_of_sale.gui');
	var screens = require('point_of_sale.screens');
	var _t = core._t;
	var ajax = require('web.ajax');

    var SelectSalespersonButton = screens.ActionButtonWidget.extend({
        template: 'SelectSalespersonButton',
        button_click: function(){
            var user_list = [];
            var order = this.pos.get_order();

            // !Custom by MCS
            var salesperson_list = [];
            var thiss = this;

            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                'model': 'pos.config',
                'method': 'get_salesperson',
                'args': [this.pos.config_id, this.pos.config_id],
                'kwargs': {
                    'context': {},
                }
            }).then(function (data) {
                salesperson_list = data;
                if (salesperson_list.length > 0){
                    for (var i = 0; i < salesperson_list.length; i++) {
                        var user = salesperson_list[i];
                        user_list.push({
                            'label': user.name,
                            'item':  user,
                        });
                    }
                }
                else{
                    for (var i = 0; i < thiss.pos.users.length; i++) {
                        var user = thiss.pos.users[i];
                        user_list.push({
                            'label': user.name,
                            'item':  user,
                        });
                    }
                }
                if (user_list.length > 0) {
                    return thiss.pos.gui.show_popup('selection', {
                    title: _t('Select Salesperson'),
                    list: user_list,
                    confirm: function (user) {
                        var orderlines = order.get_orderlines();
                        for(var i = 0; i < orderlines.length; i++){
                            if(orderlines[i] != undefined){
                                orderlines[i].set_line_user(user);
                            }
                        }
                    },
                });
            }

            });
            // !Custom by MCS

        },
    });
    //
	screens.define_action_button({
        'name': 'SelectSalespersonButton',
        'widget': SelectSalespersonButton,
        'condition': function(){ 
            return this.pos.config.allow_salesperson;
        },
    });
    //
    var _super_Orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        init_from_JSON: function (json) {
            var self = this;
            if (json.user_id) {
                var user = this.get_user_by_id(json.user_id);
                if (user) {
                    this.set_line_user(user);
                }
            }
            return _super_Orderline.init_from_JSON.apply(this, arguments);
        },
        //
        export_as_JSON: function () {
            var json = _super_Orderline.export_as_JSON.apply(this, arguments);
            if (this.user_id) {
                json.user_id = this.user_id.id;
            }
            return json;
        },
        //
        get_user_image_url: function () {
            if (this.user_id && this.user_id.id !== undefined) {
                return window.location.origin + '/web/image?model=res.users&field=image_128&id=' + this.user_id.id;
            }
            return null;
        },
        //
        get_user_by_id: function (user_id) {
            var self = this;
            var user = null;
            for (var i = 0; i < self.pos.users.length; i++) {
                if (self.pos.users[i].id == user_id) {
                    user = self.pos.users[i];
                }
            }
            return user;
        },
        //
        get_line_user: function () {
            if (this.user_id && this.user_id.id !== undefined) {
                return this.user_id;
            }
            return null;
        },
        //
        set_line_user: function (user) {
            this.user_id = user;
            this.trigger('change', this);
        },
        //
        remove_sale_person: function () {
            this.user_id = null;
            this.trigger('change', this);
        },
    });
    //
    screens.OrderWidget.include({
        render_orderline: function (orderline) {
            var self = this;
            var selectedLine = this._super(orderline);
            var remove_user = selectedLine.querySelector('.remove_person');
            if (remove_user) {
                remove_user.addEventListener('click', (function () {
                    orderline.remove_sale_person()
                }.bind(this)));
            }
            var line_user = selectedLine.querySelector('.sale_person');
            if (line_user) {
                line_user.addEventListener('click', (function () {
                    var user_list = [];
                    for (var i = 0; i < self.pos.users.length; i++) {
                        var user = self.pos.users[i];
                        user_list.push({
                            'label': user.name,
                            'item':  user,
                        });
                    }
                    if (user_list.length > 0) {
                        return self.pos.gui.show_popup('selection', {
                            title: _t('Select Salesperson'),
                            list: user_list,
                            confirm: function (user) {
                                orderline.set_line_user(user);
                            },
                        });
                    } 

                }.bind(this)));
            }
            return selectedLine;
        },
    });
});
