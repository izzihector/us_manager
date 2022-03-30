odoo.define('mcs_aspl_pos_discount_auto.models', function (require) {
	"use strict";

	var models = require('point_of_sale.models');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var DB = require('point_of_sale.DB');
    var pos_model = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var popup_widget = require('point_of_sale.popups');
    var SuperOrder = models.Order;
    var SuperOrderline = pos_model.Orderline;
    var QWeb = core.qweb;
    var _t = core._t;

    models.load_models({
        model:'pos.custom.discount',
        field: [],
        domain:function(self){
            var current_date =  new Date();
            return [['id','in',self.config.discount_ids], ['start_date', '<=', current_date], ['end_date', '>=', current_date]];
        },
        order: [{name: 'start_date', asc: true}],
        loaded: function(self,result) {
            self.all_discounts = result;
        },
    });

    var DiscountPopup = popup_widget.extend({
         template: 'DiscountPopup',
        ask_password: function(password) {
            var self = this;
            var ret = new $.Deferred();
            if (password) {
                this.gui.show_popup('password',{
                    'title': _t('Password ?'),
                    confirm: function(pw) {
                        if (Sha1.hash(pw) !== password) {
                            self.gui.show_popup('error_popup',{
                                'title':_t('Password Incorrect !!!'),
                                'body':_('Entered Password Is Incorrect ')
                            });
                        } else {
                            ret.resolve();
                        }
                    },
                    cancel: function() {
                        self.gui.current_screen.order_widget.numpad_state.reset();
                    }
                });
            } else {
                ret.resolve();
            }
            return ret;
        },
        check_discount_eligibility: function(discount,product_id){
            var self = this;
            var discount_type = discount.discount_type;
            var discount_apply_on =  discount.apply_on;
            var discount_start_date = discount.start_date;
            var discount_end_date = discount.end_date;
            var product_ids = discount.product_ids;
            var categ_ids = discount.categ_ids;
            var exception_dates_ids = discount.exception_date_ids;
            var day_week_ids = discount.day_of_week_ids;
            var discount_value = self.format_currency_no_symbol(discount.value);

            var flag_exception = true;
            var flag_day_week = false;
            var flag_categ_id = false;
            var now = new Date();
            var dict_excp_date ={};
            _.each(day_week_ids, function(day){
                if(day == (now.getDay()+1)){
                    flag_day_week = true;
                }
            });
            if(exception_dates_ids && exception_dates_ids[0]){
                _.each(exception_dates_ids,function(date_id){
                    dict_excp_date[date_id] = [self.pos.db.get_exception_dates_by_id(date_id).start_date,self.pos.db.get_exception_dates_by_id(date_id).end_date];
                });
                _.each(dict_excp_date,function(x,y){
                    var todaydate = moment().utc().format();
                    if (todaydate > moment(x[0]).format() &&
                            todaydate < moment(x[1]).format()) {
                        flag_exception = true;
                    }
                    else
                    {
                        flag_exception = false;
                    }
                })
            }
            if(flag_exception){
                if(discount_apply_on == 'product'){
                    var flag_for_product = false;
                    for(var i=0; i <= product_ids.length; i++){
                        if(product_ids[i] == product_id){
                            flag_for_product = true;
                            if(flag_day_week){
                                if(!discount.start_time && !discount.end_time){
                                    if (moment().utc().format() > moment(discount_start_date).format() &&
                                            moment().utc().format() < moment(discount_end_date).format()) {
                                            return true;
                                        } else{
                                            return false;
                                        }
                                } else{
                                    if(discount.start_time <= now.getHours() && discount.end_time > now.getHours()){
                                        if (moment().utc().format() > moment(discount_start_date).format() &&
                                                moment().utc().format() < moment(discount_end_date).format()) {
                                            return true;
                                        } else{
                                            return false;
                                        }
                                    } else{
                                        return false;
                                    }
                                }
                            } else{
                                return false;
                            }
                        }
                    }if(!flag_for_product){
                        return false;
                    }
                } else if (discount_apply_on == 'category'){
                    var flag_for_categ = false;
                    var product = self.pos.db.get_product_by_id(product_id);
                    for (var i=0;i<=categ_ids.length;i++){
                        if(product.pos_categ_id && product.pos_categ_id[0]){
                            flag_categ_id = true
                            var categ_product = self.pos.db.get_product_by_category(categ_ids[i])
                            if($.inArray(product,categ_product) !== -1){
                                flag_for_categ = true;
                                break;
                            }
                        }
                    }
                    if(flag_for_categ){
                        if(flag_day_week){
                            if(!discount.start_time && !discount.end_time){
                                if (moment().utc().format() > moment(discount_start_date).format() &&
                                        moment().utc().format() < moment(discount_end_date).format()) {
                                        return true;
                                    } else{
                                        return false;
                                    }
                            } else{
                                if(discount.start_time <= now.getHours() && discount.end_time > now.getHours()){
                                    if (moment().utc().format() > moment(discount_start_date).format() &&
                                            moment().utc().format() < moment(discount_end_date).format()) {
                                        return true;
                                    } else{
                                        return false;
                                    }
                                } else{
                                    return false;
                                }
                            }
                        }else{
                            return false;
                        }
                    } else{
                        if(!flag_for_categ){
                            return false;
                        }
                    }
                }
            }
        },
        show: function() {
            var self = this;
            this._super();
            var discount_id = null;
            var discount_list = self.pos.all_discounts;
            var discount_value=0;
            var order = this.pos.get_order();
            var discount_price = 0;
            var discount_type = '';
            var discount_apply_on = '';
            var discount = null;
            var currentOrder = self.pos.get('selectedOrder');
            $(".button.apply").removeClass('oe_hidden');
            $(".button.apply_complete_order").removeClass('oe_hidden');
            $("#discount_error").hide();
            self.render_list(self.pos.all_discounts);
            $('.discount-list tr').eq(1).addClass('selected');
            discount_id = parseInt($('.product_discount.selected').attr('id'));
            order.set_custom_discount(discount_id);
            if(!discount_list.length){
                $(".button.apply_complete_order").addClass('oe_hidden');
                $(".button.apply").addClass('oe_hidden');
            }
            $(".product_discount").on("click",function(e){
                $("#discount_error").hide();
                $(".product_discount").removeClass('selected');
                $(this).addClass('selected');

                discount_id = parseInt($('.product_discount.selected').attr('id'));
                order.set_custom_discount(discount_id);
            });

            $(".button.apply").on('click',function(){
                var orderline = order.get_selected_orderline();
                discount = order.get_custom_discount();
                discount_type = discount.discount_type;
                discount_value = self.format_currency_no_symbol(discount.value);
                var res = self.check_discount_eligibility(discount,orderline.product.id);
                if(discount_value != 0){
                    if(res){
                        if(discount_type == "percentage"){
                            orderline.set_discount(discount_value);
                        } else {
                            orderline.set_fix_discount(discount_value);
                            orderline.set_unit_price(orderline.get_unit_price()-orderline.get_fix_discount());
                        }
                        $('ul.orderlines li.selected div#custom_discount_reason').text('');
                        self.gui.close_popup();
                        self.gui.current_screen.order_widget.numpad_state.reset();
                    } else{
                        alert("Discount not applicable.");
                    }
                    orderline.custom_discount_reason='';
                } else{
                    $(".product_discount").css("background-color","burlywood");
                    setTimeout(function(){
                        $(".product_discount").css("background-color","");
                    },100);
                    setTimeout(function(){
                        $(".product_discount").css("background-color","burlywood");
                    },200);
                    setTimeout(function(){
                        $(".product_discount").css("background-color","");
                    },300);
                    setTimeout(function(){
                        $(".product_discount").css("background-color","burlywood");
                    },400);
                    setTimeout(function(){
                        $(".product_discount").css("background-color","");
                    },500);
                    return;
                }
            });
            $(".button.apply_complete_order").on('click',function(){
                _.each(self.pos.all_discounts, function(disc){
                    discount = disc;
                    discount_type = discount.discount_type;
//                    discount_value = self.format_currency_no_symbol(discount.value);
                    discount_value = discount.value;
                    if(discount_value != 0){
                        var orderline_ids = order.get_orderlines();
                        for(var i=0; i< orderline_ids.length; i++){
                                var has_disc = false;
                                if (orderline_ids[i].get_fix_discount() > 0 || orderline_ids[i].get_discount() > 0){
                                    has_disc = true;
                                }
                                if(!has_disc){
                                    var res = self.check_discount_eligibility(discount,orderline_ids[i].product.id);
                                    if(res){
                                        if(discount_type == "percentage"){
                                            orderline_ids[i].set_discount(discount_value);
                                        }else{
                                            orderline_ids[i].set_fix_discount(discount_value);
                                            orderline_ids[i].set_unit_price(orderline_ids[i].get_unit_price()-orderline_ids[i].get_fix_discount())
                                        }
                                        orderline_ids.custom_discount_reason='';
                                        orderline_ids[i].custom_discount_id=disc.id;
                                    }
                                }
                            }
                        $('ul.orderlines li div#custom_discount_reason').text('');
                        self.gui.close_popup();
                        self.gui.current_screen.order_widget.numpad_state.reset();
                    }
                    else{
                        $(".product_discount").css("background-color","burlywood");
                        setTimeout(function(){
                            $(".product_discount").css("background-color","");
                        },100);
                        setTimeout(function(){
                            $(".product_discount").css("background-color","burlywood");
                        },200);
                        setTimeout(function(){
                            $(".product_discount").css("background-color","");
                        },300);
                        setTimeout(function(){
                            $(".product_discount").css("background-color","burlywood");
                        },400);
                        setTimeout(function(){
                            $(".product_discount").css("background-color","");
                        },500);
                        return;
                    }
                });
            });
            /*remove_disc*/
             $(".button.remove_disc").on('click',function(){
                if(order && order.get_selected_orderline()){
                    var orderline_ids = order.get_orderlines();
                    var selected_line = '';
                    for(var i=0; i< orderline_ids.length; i++){
                        selected_line = orderline_ids[i];
    //                    var selected_line = order.get_selected_orderline();
                        if(selected_line){
                            if(selected_line.get_fix_discount() > 0){
                                selected_line.set_unit_price(selected_line.get_unit_price() + selected_line.get_fix_discount())
                                selected_line.set_fix_discount(0)
                            }
                            selected_line.set_discount(0);
                            self.gui.close_popup();
                            self.gui.current_screen.order_widget.numpad_state.reset();
                        }
                    }
                }
            });
            $(".button.cancel").on('click',function(){
                self.gui.close_popup();
                self.gui.current_screen.order_widget.numpad_state.reset();
            });
            $(".button.customize").on("click",function(){
                var user = self.pos.get_cashier();
                if(self.pos.config.allow_security_pin && user.pin){
                    var user = self.pos.get_cashier();
                    self.ask_password(user.pin).then(function(){
                        self.gui.show_popup('custom_discount', {
                            'title': _t("Customize Discount"),
                        });
                    });
                }
                else{
                    self.gui.show_popup('custom_discount', {
                    'title': _t("Customize Discount")
                    });
                }
            });
        },
        render_list: function(discounts){
            var contents = this.$el[0].querySelector('.discount-list-contents');
            contents.innerHTML = "";
            for(var i=0;i<discounts.length;i++){
                var discount = discounts[i];
                var discountline_html = QWeb.render('DiscountLine',{widget: this, discount:discounts[i]});
                var discountline = document.createElement('tbody');
                discountline.innerHTML = discountline_html;
                discountline = discountline.childNodes[1];
                contents.appendChild(discountline);
            }
        },
        renderElement: function(){
            var self = this;
            self._super();
            var discount_id = parseInt($('.product_discount.selected').attr('id'));
        },
    });

    gui.define_popup({ name: 'customer_discount', widget: DiscountPopup });

    pos_model.Orderline = pos_model.Orderline.extend({
        initialize: function(attr,options){
            this.custom_discount_id=null;
            SuperOrderline.prototype.initialize.call(this,attr,options);
        },
        export_for_printing: function(){
            var dict = SuperOrderline.prototype.export_for_printing.call(this);
            var new_attr = {
                    custom_discount_id : this.custom_discount_id,
            }
            $.extend(dict, new_attr);
            return dict;
        },
        get_custom_discount_id: function(){
            var self = this;
            return self.custom_discount_id;
        },
        export_as_JSON: function() {
            var self = this;
            var loaded = SuperOrderline.prototype.export_as_JSON.call(this);
            loaded.custom_discount_id = self.get_custom_discount_id();
            return loaded;
        },
        init_from_JSON: function(json) {
            var self = this;
            var loaded = SuperOrderline.prototype.init_from_JSON.call(this,json);
            this.custom_discount_id = json.custom_discount_id
        },
    });

//    models.Order = models.Order.extend({
//        add_product: function(product, options){
//            var self = this;
//            SuperOrder.add_product.call(this,product, options);
//            var discount_value=0;
//            var discount = null;
//            var discount_type = '';
//            var order = this.pos.get_order();
//            console.log(this);
//            _.each(self.pos.all_discounts, function(disc){
//				discount = disc;
//                discount_type = discount.discount_type;
//                discount_value = discount.value;
//                if(discount_value != 0){
//                    var orderline_ids = order.get_orderlines();
//                    for(var i=0; i< orderline_ids.length; i++){
//                            var res = self.pos.chrome.check_discount_eligibility(discount,orderline_ids[i].product.id);
//                            if(res){
//                                if(discount_type == "percentage"){
//                                    orderline_ids[i].set_discount(discount_value);
//                                }else{
//                                    orderline_ids[i].set_fix_discount(discount_value);
//                                    orderline_ids[i].set_unit_price(orderline_ids[i].get_unit_price()-orderline_ids[i].get_fix_discount())
//                                }
//                                orderline_ids.custom_discount_reason='';
//                            }
//                        }
//                    $('ul.orderlines li div#custom_discount_reason').text('');
////                    self.gui.close_popup();
//                    self.gui.current_screen.order_widget.numpad_state.reset();
//                }
//                else{
//                    return;
//                }
//			})
//        }
//	});
});