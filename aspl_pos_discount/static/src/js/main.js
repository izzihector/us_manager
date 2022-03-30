odoo.define('aspl_pos_discount.main', function (require) {
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

    models.load_models([{
        model:'pos.custom.discount',
        field: [],
        domain:function(self){
            var current_date = moment(new Date()).format("YYYY-MM-DD hh:mm:ss");
            return [['id','in',self.config.discount_ids]];
        },
        loaded: function(self,result) {
            self.all_discounts = result;
        }
    },{
        model:'day.week',
        field: [],
        domain: null,
        loaded: function(self,result) {
            self.db.add_get_day_week(result);
        }
    },{
        model:'exception.dates',
        field: [],
        domain: null,
        loaded: function(self,result) {
            self.db.add_exception_dates(result);
        }
    }],{
            'before': 'pos.category'
        }
    );

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        set_custom_discount: function(discount_id){
            var self = this;
            var discount_list = self.pos.all_discounts;
            var discount = false;
            for(var i=0; i<discount_list.length; i++ ){
                if( discount_list[i].id == discount_id){
                    discount = discount_list[i];
                    this.set('discount', discount)
                }
            }
        },
        get_custom_discount: function(){
            return this.get('discount')
        },
    });
    screens.ScreenWidget.include({
        init: function(parent, options){
            var self = this;
            this._super(parent, options);
            this.keydown_discount = function(event){
                event.stopImmediatePropagation();
                self.keyboard_discount(event);
            };
        },
        start: function(){
            var self = this;
            this._super();
            $(document).keydown(_.bind(this.keydown_discount, self));
        },
        keyboard_discount: function(event){
            var self = this;
             if($(':focus').prop("tagName") == "INPUT" || $(':focus').prop("tagName") == 'TEXTAREA'){
                 return
             }
            if(self.gui.get_current_screen() === "products" ){
                var keytostring = event.key;
                var el = '';
                if(self.gui.current_popup){
                    if(self.gui.current_popup.el && self.gui.current_popup.el.id){
                        el = self.gui.current_popup.el.id
                    }
                }
                if(keytostring === self.pos.config.open_discount_popup){
                    var order = self.pos.get_order();
                    if(order.get_orderlines() && order.get_orderlines().length > 0){
                        self.gui.show_popup('customer_discount',{});
                    } else{
                        self.gui.show_popup('error_popup',{
                            'title':_t('No Selected Orderline'),
                            'body':_t('No order line is Selected. Please add or select an Orderline')
                        });
                    }
                }
                if(el === "inbuilt_discount"){
                    if(event.key === 'a' || event.key === 'A'){
                        $('.apply_complete_order').trigger('click');
                    } else if(event.key === 's' || event.key === 'S'){
                        $('.button.apply').trigger('click');
                    } else if(event.key === 'm' || event.key === 'M'){
                        $('.fa-stack-discount').trigger('click');
                    }else if(event.key === 'n' || event.key === 'N'){
                        $('.button.cancel').trigger('click');
                    }else if(event.key === 'r' || event.key === 'R'){
                        $('.button.remove_disc').trigger('click');
                    }
                } else if(el === "custom_discount_popup"){
                    if(event.key === 'a' || event.key === 'A'){
                        $('.whole_order').trigger('click');
                    } else if(event.key === 's' || event.key === 'S'){
                        $('.current_product').trigger('click');
                    }  else if(event.key === 'b' || event.key === 'B'){
                        $('.custom_cancel').trigger('click');
                    }
                }
            }
            if(self.gui.current_popup){
                if(event.keyCode === $.ui.keyCode.ESCAPE){
                    self.gui.current_popup.click_cancel();
                    self.gui.current_screen.order_widget.numpad_state.reset();
                }
                if(event.keyCode === $.ui.keyCode.UP){
                    var prev_el = $('.product_discount.selected').prev();
                    if(prev_el.length > 0){
                        $('.product_discount.selected').removeClass('selected');
                        $(prev_el).addClass('selected');
                        var disc_id = $('.product_discount.selected').attr('id');
                        self.pos.get_order().set_custom_discount(disc_id);
                    }
                }
                if(event.keyCode === $.ui.keyCode.DOWN){
                    var next_el = $('.product_discount.selected').next();
                    if(next_el.length > 0){
                        $('.product_discount.selected').removeClass('selected');
                        $(next_el).addClass('selected');
                        var disc_id = $('.product_discount.selected').attr('id');
                        self.pos.get_order().set_custom_discount(disc_id);
                    }
                }
            }
        },
    });
    pos_model.Orderline = pos_model.Orderline.extend({
        initialize: function(attr,options){
            this.custom_discount_reason='';
            this.fix_discount = 0;
            SuperOrderline.prototype.initialize.call(this,attr,options);
        },
        export_for_printing: function(){
            var dict = SuperOrderline.prototype.export_for_printing.call(this);
            var new_attr = {
                    custom_discount_reason : this.custom_discount_reason,
                    fix_discount : this.get_fix_discount()
            }
            $.extend(dict, new_attr);
            return dict;
        },
        get_custom_discount_reason: function(){
            var self = this;
            return self.custom_discount_reason;
        },
        export_as_JSON: function() {
            var self = this;
            var loaded = SuperOrderline.prototype.export_as_JSON.call(this);
            loaded.custom_discount_reason = self.get_custom_discount_reason();
            loaded.fix_discount = this.get_fix_discount();
            return loaded;
        },
        init_from_JSON: function(json) {
            var self = this;
            var loaded = SuperOrderline.prototype.init_from_JSON.call(this,json);
            this.custom_discount_reason = json.custom_discount_reason
            this.fix_discount = json.fix_discount
        },
        set_fix_discount: function(discount){
            var disc = parseFloat(discount);
            this.fix_discount = disc;
            this.trigger('change',this);
        },
        get_fix_discount: function(){
            return this.fix_discount;
        }
    });

    var CustomDiscountPopup = popup_widget.extend({
        template: 'CustomDiscountPopup',
        show: function(){
            var self=this;
            this._super();
            var order = this.pos.get_order();
            $('#custom_discount_type').focus();
            var focusableEls = $('.tbl_custom_discont').find('.tbl_custom_discont');
            var firstFocusableEl = focusableEls.first()[0];
            var lastFocusableEl = focusableEls.last()[0];
            var KEYCODE_TAB = 9;
            $('.tbl_custom_discont').on('keydown', function(e) {
                if (e.key === 'Tab' || e.keyCode === KEYCODE_TAB) {
                    if (e.shiftKey){
                        if (document.activeElement === firstFocusableEl) {
                            lastFocusableEl.focus();
                            e.preventDefault();
                        }
                    } else{
                        if (document.activeElement === lastFocusableEl) {
                            firstFocusableEl.focus();
                            e.preventDefault();
                        }
                    }
                }
            });
            $('#custom_discount_type').on('change',function(e){
                if($(this).val() == 'percent'){
                    $('#discount_fix').addClass("hidden-field");
                    $('#discount_fix').val('')
                    $('#discount').removeClass("hidden-field");
                    $('#discount').focus();
                }
                if($(this).val() == 'fixed'){
                    $('#discount').addClass("hidden-field");
                    $('#discount').val('')
                    $('#discount_fix').removeClass("hidden-field");
                    $('#discount_fix').focus();
                }
            })
            $('.custom_cancel').on('click',function(){
                self.gui.show_popup('customer_discount',{});
            });
            $('#discount').on('click',function(){
                $('#error_div').hide();
            })
            $('.current_product').on('click',function(){
                var per = parseFloat($('#discount').val());
                var fix = parseFloat($('#discount_fix').val());
                if(!per && !fix || per > 100  || (per <= 0 || fix <= 0)){
                    $('#error_div').show();
                    $('#customize_error').html('<i class="fa fa-exclamation-triangle" aria-hidden="true"></i > Discount percent must be between 0 and 100.')
                } else{
                    var customize_discount = parseFloat($('#discount').val())
                    var reason =($("#reason").val());
                    if($('#custom_discount_type').val() == 'percent'){
                        order.get_selected_orderline().set_discount(customize_discount);
                    } else {
                        order.get_selected_orderline().set_fix_discount(fix);
                        order.get_selected_orderline().set_unit_price(order.get_selected_orderline().get_unit_price()-order.get_selected_orderline().get_fix_discount());
                    }
                    self.pos.get_order().get_selected_orderline().custom_discount_reason=reason;
                    $('ul.orderlines li.selected div#custom_discount_reason').text(reason);
                    self.gui.close_popup();
                    self.gui.current_screen.order_widget.numpad_state.reset();
                }
            });
            $('.whole_order').on('click',function(){
                var orderline_ids = order.get_orderlines();
                var per = parseFloat($('#discount').val());
                var fix = parseFloat($('#discount_fix').val());
                if(!per && !fix || per > 100 || (per <= 0 || fix <= 0)){
                    $('#error_div').show();
                    $('#customize_error').html('<i class="fa fa-exclamation-triangle" aria-hidden="true"></i > Discount percent must be between 0 and 100.')
                } else{
                    var reason =($("#reason").val());
                    var discount_type = $('#custom_discount_type').val();
                    for(var i=0; i< orderline_ids.length; i++){
                        if(discount_type == "percent"){
                            orderline_ids[i].set_discount(per);
                        }else{
                            orderline_ids[i].set_fix_discount(fix);
                            orderline_ids[i].set_unit_price(orderline_ids[i].get_unit_price() - orderline_ids[i].get_fix_discount())
                        }
                        orderline_ids[i].custom_discount_reason=reason;
                    }
                    $('ul.orderlines li div#custom_discount_reason').text(reason);
                    self.gui.close_popup();
                    self.gui.current_screen.order_widget.numpad_state.reset();
                }
            });
        }
    });
    gui.define_popup({ name: 'custom_discount', widget: CustomDiscountPopup });

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

            var flag_exception = true; // fix by MCS - LLHa (before: exception date must be filled)
            var flag_day_week = false;
            var flag_categ_id = false;
            var now = new Date();
            var dict_excp_date ={};
            _.each(day_week_ids, function(day){
//            Fix by MCS - LLHa (now.getDay() start from 0 (Sunday), day is ID, start from 1 (Sunday))
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
                    // fix by MCS - LLHa (before: exception date must be filled)
                    else
                    {
                        flag_exception = false;
                    }
                    // !fix by MCS - LLHa (before: exception date must be filled)
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
                discount = order.get_custom_discount();
                discount_type = discount.discount_type;
                discount_value = self.format_currency_no_symbol(discount.value);
                if(discount_value != 0){
                    var orderline_ids = order.get_orderlines();
                    for(var i=0; i< orderline_ids.length; i++){
                            var res = self.check_discount_eligibility(discount,orderline_ids[i].product.id);
                            if(res){
                                if(discount_type == "percentage"){
                                    orderline_ids[i].set_discount(discount_value);
                                }else{
                                    orderline_ids[i].set_fix_discount(discount_value);
                                    orderline_ids[i].set_unit_price(orderline_ids[i].get_unit_price()-orderline_ids[i].get_fix_discount())
                                }
                                orderline_ids.custom_discount_reason='';
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
            /*remove_disc*/
            $(".button.remove_disc").on('click',function(){
                if(order && order.get_selected_orderline()){
                    var selected_line = order.get_selected_orderline();
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

    var ErrorPopup = popup_widget.extend({
        template:'ErrorPopup',
        events: {
                'click #password_ok_button':  'click_password_ok_button',
            },
            click_password_ok_button: function(){
                var self = this;
                this.gui.close_popup();
                self.gui.current_screen.order_widget.numpad_state.reset();
            },
    });
    gui.define_popup({name:'error_popup', widget: ErrorPopup});

    screens.NumpadWidget.include({
        changedMode: function() {
            var self = this;
            var mode = this.state.get('mode');
            if(mode == 'discount'){
                if(self.pos.get_order().get_selected_orderline()){
                    if(self.pos.config.discount_ids.length ||self.pos.config.allow_custom_discount){
                        self.gui.show_popup('customer_discount', {
                        'title': _t("Discount List"),
                        });
                    }
                    else{
                        self.gui.show_popup('error_popup',{
                            'title':_t('No Discount Is Available'),
                            'body':_t('No discount is available for current POS. Please add discount from configuration')
                        });
                    }
                }
                else {
                    self.gui.show_popup('error_popup',{
                        'title':_t('No Selected Orderline'),
                        'body':_t('No order line is Selected. Please add or select an Orderline')
                    });
                }
            }
            self._super();
        },
    });

    DB.include({
        init: function(options){
            this._super.apply(this, arguments);
            this.day_week_by_id = {};
            this.exception_dates_by_id = {};
        },
        add_get_day_week: function(day_week){
            var self = this;
            day_week.map(function(res){
                self.day_week_by_id[res.id] = res;
            });
        },
        get_day_week_by_id: function(id){
            return this.day_week_by_id[id];
        },
        add_exception_dates: function(exception_dates){
            var self = this;
            exception_dates.map(function(res){
                self.exception_dates_by_id[res.id] = res;
            });
        },
        get_exception_dates_by_id: function(id){
            return this.exception_dates_by_id[id];
        },
    });
});
