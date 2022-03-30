odoo.define('mcs_aspl_pos_promotion.promotions', function (require) {
"use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var utils = require('web.utils');

    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;


    models.PosModel.prototype.models.push(
    {
        model:  'pos.promotion',
        fields: [],
        domain: function(self){
            var current_date = moment(new Date()).locale('en').format("YYYY-MM-DD");
            var weekday = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
            var current_time = moment(new Date().getTime()).locale('en').format("H");
            var d = new Date();
            var current_day = weekday[d.getDay()]
            return [['from_date','<=',current_date],['to_date','>=',current_date],['active','=',true],
                    ['day_of_week_ids.name','in',[current_day]], ['id','in',self.config.promotion_ids]];
        },
        loaded: function(self, pos_promotions){
            self.pos_promotions = pos_promotions;
        },
    },{
        model:  'pos.conditions',
        fields: [],
        loaded: function(self,pos_conditions){
            self.pos_conditions = pos_conditions;
        },
    },{
        model:  'get.discount',
        fields: [],
        loaded: function(self,pos_get_discount){
            self.pos_get_discount = pos_get_discount;
        },
    },{
        model:  'quantity.discount',
        fields: [],
        loaded: function(self,pos_get_qty_discount){
            self.pos_get_qty_discount = pos_get_qty_discount;
        },
    },{
        model:  'quantity.discount.amt',
        fields: [],
        loaded: function(self,pos_qty_discount_amt){
            self.pos_qty_discount_amt = pos_qty_discount_amt;
        },
    },{
        model:  'discount.multi.products',
        fields: [],
        loaded: function(self,pos_discount_multi_prods){
            self.pos_discount_multi_prods = pos_discount_multi_prods;
        },
    },{
        model:  'discount.multi.categories',
        fields: [],
        loaded: function(self,pos_discount_multi_categ){
            self.pos_discount_multi_categ = pos_discount_multi_categ;
        },
    },{
        model:  'discount.above.price',
        fields: [],
        loaded: function(self,pos_discount_above_price){
            self.pos_discount_above_price = pos_discount_above_price;
        },
    });

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        apply_promotion: function(){
            var self = this;
            self.remove_promotion();
            var order = self.pos.get_order();
            var lines = order.get_new_order_lines();
            var promotion_list = self.pos.pos_promotions;
            var condition_list = self.pos.pos_conditions;
            var discount_list = self.pos.pos_get_discount;
            var pos_get_qty_discount_list = self.pos.pos_get_qty_discount;
            var pos_qty_discount_amt = self.pos.pos_qty_discount_amt;
            var pos_discount_multi_prods = self.pos.pos_discount_multi_prods;
            var pos_discount_multi_categ = self.pos.pos_discount_multi_categ;
            var pos_discount_above_price = self.pos.pos_discount_above_price;
            var selected_line = self.pos.get_order().get_selected_orderline();
            var current_time = Number(moment(new Date().getTime()).locale('en').format("H"));
            if(order && lines && lines[0]){
                _.each(lines, function(line){
                    if(promotion_list && promotion_list[0]){
                        _.each(promotion_list, function(promotion){
                            if((Number(promotion.from_time) <= current_time && Number(promotion.to_time) > current_time) || (!promotion.from_time && !promotion.to_time)){
                            if(promotion && promotion.promotion_type == "buy_x_get_y"){
                                if(promotion.pos_condition_ids && promotion.pos_condition_ids[0]){
                                    _.each(promotion.pos_condition_ids, function(pos_condition_line_id){
                                        var line_record = _.find(condition_list, function(obj) { return obj.id == pos_condition_line_id});
                                        if(line_record){
                                            if(line_record.product_x_id && line_record.product_x_id[0] == line.product.id){
                                                if(!line.get_is_rule_applied()){
                                                    if(line_record.operator == 'is_eql_to'){
                                                        if(line_record.quantity == line.quantity){
                                                            if(line_record.product_y_id && line_record.product_y_id[0]){
                                                                var product = self.pos.db.get_product_by_id(line_record.product_y_id[0]);
                                                                var new_line = new models.Orderline({}, {pos: self.pos, order: order, product: product});

                                                                // MCS
                                                                // new_line.fix_amount_discount = new_line.price * line_record.quantity_y;
                                                                // !MCS

                                                                new_line.set_quantity(line_record.quantity_y);
                                                                // new_line.set_unit_price(0);
                                                                new_line.set_discount(100);
                                                                new_line.set_promotion({
                                                                    'prom_prod_id':line_record.product_y_id[0],
                                                                    'parent_product_id':line_record.product_x_id[0],
                                                                    'rule_name':promotion.promotion_code,
                                                                });
                                                                new_line.set_is_rule_applied(true);

                                                                // MCS
                                                                new_line.custom_promotion_id = promotion.id;
                                                                if (promotion.vendor_id && promotion.vendor_id[0]){
                                                                    new_line.vendor_id = promotion.vendor_id[0];
                                                                }
                                                                new_line.vendor_shared = promotion.vendor_shared;
                                                                new_line.sarinah_shared = promotion.sarinah_shared;
                                                                //line.custom_promotion_id = promotion.id;
                                                                // !MCS

                                                                order.add_orderline(new_line);
                                                                line.set_child_line_id(new_line.id);
                                                                line.set_is_rule_applied(true);
                                                            }
                                                        }
                                                    }else if(line_record.operator == 'greater_than_or_eql'){
                                                        if(line.quantity >= line_record.quantity){
                                                            if(line_record.product_y_id && line_record.product_y_id[0]){
                                                                var product = self.pos.db.get_product_by_id(line_record.product_y_id[0]);
                                                                var new_line = new models.Orderline({}, {pos: self.pos, order: order, product: product});

                                                                // MCS
                                                                // new_line.fix_amount_discount = new_line.price * line_record.quantity_y;
                                                                // !MCS

                                                                new_line.set_quantity(line_record.quantity_y);
                                                                // new_line.set_unit_price(0);
                                                                new_line.set_discount(100);
                                                                new_line.set_promotion({
                                                                    'prom_prod_id':line_record.product_y_id[0],
                                                                    'parent_product_id':line_record.product_x_id[0],
                                                                    'rule_name':promotion.promotion_code,
                                                                });

                                                                new_line.set_is_rule_applied(true);
                                                                order.add_orderline(new_line);
                                                                line.set_child_line_id(new_line.id);
                                                                line.set_is_rule_applied(true);

                                                                // MCS
                                                                new_line.custom_promotion_id = promotion.id;
                                                                if (promotion.vendor_id && promotion.vendor_id[0]){
                                                                    new_line.vendor_id = promotion.vendor_id[0];
                                                                }
                                                                new_line.vendor_shared = promotion.vendor_shared;
                                                                new_line.sarinah_shared = promotion.sarinah_shared;
//                                                                line.custom_promotion_id = promotion.id;
                                                                // !MCS

                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    });
                                }
                            }
                            else if(promotion && promotion.promotion_type == "buy_x_get_dis_y"){
                                if(promotion.parent_product_ids && promotion.parent_product_ids[0] && (jQuery.inArray(line.product.id,promotion.parent_product_ids) != -1)){
                                    var disc_line_ids = [];
                                    _.each(promotion.pos_quntity_dis_ids, function(pos_quntity_dis_id){
                                        var disc_line_record = _.find(discount_list, function(obj) { return obj.id == pos_quntity_dis_id});
                                        if(disc_line_record){
                                            if(disc_line_record.product_id_dis && disc_line_record.product_id_dis[0]){
                                                disc_line_ids.push(disc_line_record);
                                            }
                                        }
                                    });
                                    line.set_buy_x_get_dis_y({
                                        'disc_line_ids':disc_line_ids,
                                        'promotion':promotion,
                                    });
                                }
                                if(line.get_buy_x_get_dis_y().disc_line_ids){
                                    _.each(line.get_buy_x_get_dis_y().disc_line_ids, function(disc_line){
                                        _.each(lines, function(orderline){
                                            if(disc_line.product_id_dis && disc_line.product_id_dis[0] == orderline.product.id){
                                                var count = 0;
                                                _.each(order.get_orderlines(), function(_line){
                                                    if(_line.product.id == orderline.product.id){
                                                        count += 1;
                                                    }
                                                });
                                               // if(count <= disc_line.qty){
                                                    var cart_line_qty = orderline.get_quantity();
                                                    if(cart_line_qty >= disc_line.qty){
                                                        var prmot_disc_lines = [];
                                                        var flag = true;
                                                        order.get_orderlines().map(function(o_line){
                                                            if(o_line.product.id == orderline.product.id){
                                                                if(o_line.get_is_rule_applied()){
                                                                    flag = false;
                                                                }
                                                            }
                                                        });
                                                        if(flag){
                                                            var extra_prod_qty = cart_line_qty - disc_line.qty;
                                                            if(extra_prod_qty != 0){
                                                                orderline.set_quantity(disc_line.qty);
                                                            }
                                                            orderline.set_discount(disc_line.discount_dis_x);
                                                            orderline.set_buy_x_get_y_child_item({
                                                                'rule_name':line.get_buy_x_get_dis_y().promotion.promotion_code,
                                                                'promotion_type':line.get_buy_x_get_dis_y().promotion.promotion_type,
                                                            });
                                                            orderline.set_is_rule_applied(true);

                                                            // MCS
                                                            orderline.custom_promotion_id = promotion.id;
                                                            if (promotion.vendor_id && promotion.vendor_id[0]){
                                                                orderline.vendor_id = promotion.vendor_id[0];
                                                            }
                                                            orderline.vendor_shared = promotion.vendor_shared;
                                                            orderline.sarinah_shared = promotion.sarinah_shared;
                                                            // !MCS

                                                            self.pos.chrome.screens.products.order_widget.rerender_orderline(orderline);
                                                            if(extra_prod_qty != 0){
                                                                var new_line = new models.Orderline({}, {pos: self.pos, order: order, product: orderline.product});
                                                                new_line.set_quantity(extra_prod_qty);

                                                                // MCS
//                                                                new_line.custom_promotion_id = promotion.id;
                                                                // !MCS

                                                                order.add_orderline(new_line);
                                                            }
                                                            return false;
                                                        }
                                                    }
                                             //   }
                                            }
                                        });
                                    });
                                }
                            }
                            else if(promotion && promotion.promotion_type == "quantity_discount"){
                                if(promotion.product_id_qty && promotion.product_id_qty[0]){
                                    _.each(promotion.product_id_qty, function(product_id_qty_e){
                                        var line_ids = [];
                                        if (product_id_qty_e == line.product.id){
//                                            line.set_has_aspl_promotion(true);
                                            _.each(promotion.pos_quntity_ids, function(pos_quntity_id){
                                                var line_record = _.find(pos_get_qty_discount_list, function(obj) { return obj.id == pos_quntity_id});
                                                if(line_record){
                                                    if(line.get_quantity() == line_record.quantity_dis){
                                                        if(line_record.discount_dis){
                                                            line.set_discount(line_record.discount_dis);
                                                            line.set_quantity_discount({
                                                                'rule_name':promotion.promotion_code,
                                                            });
                                                            line.set_is_rule_applied(true);

                                                            // MCS
                                                            line.custom_promotion_id = promotion.id;
                                                            if (promotion.vendor_id && promotion.vendor_id[0]){
                                                                line.vendor_id = promotion.vendor_id[0];
                                                            }
                                                            line.vendor_shared = promotion.vendor_shared;
                                                            line.sarinah_shared = promotion.sarinah_shared;
                                                            // !MCS

                                                            self.pos.chrome.screens.products.order_widget.rerender_orderline(line);
                                                            return false;
                                                        }
                                                    }
                                                }
                                            });
                                        }
                                    });
                                }
                            }else if(promotion && promotion.promotion_type == "quantity_price"){
                                if(promotion.product_id_amt && promotion.product_id_amt[0] == line.product.id){
                                    var line_ids = [];
                                    _.each(promotion.pos_quntity_amt_ids, function(pos_quntity_amt_id){
                                        var line_record = _.find(pos_qty_discount_amt, function(obj) { return obj.id == pos_quntity_amt_id});
                                        if(line_record){
                                            if(line.get_quantity() >= line_record.quantity_amt){
                                                if(line_record.discount_price){
                                                    line.set_discount_amt(line_record.discount_price);
                                                    line.set_discount_amt_rule(promotion.promotion_code);
													line.set_unit_price(((line.get_unit_price()*line.get_quantity()) - line_record.discount_price)/line.get_quantity());
//                                                    line.set_unit_price(line_record.discount_price);
                                                    line.set_is_rule_applied(true);

                                                    // MCS
                                                    line.custom_promotion_id = promotion.id;
                                                    if (promotion.vendor_id && promotion.vendor_id[0]){
                                                        line.vendor_id = promotion.vendor_id[0];
                                                    }
                                                    line.vendor_shared = promotion.vendor_shared;
                                                    line.sarinah_shared = promotion.sarinah_shared;
                                                    // !MCS

                                                    self.pos.chrome.screens.products.order_widget.rerender_orderline(line);
                                                    return false;
                                                }
                                            }
                                        }
                                    });
                                }
                            }else if(promotion && promotion.promotion_type == "discount_on_multi_product"){
                                if(promotion.multi_products_discount_ids && promotion.multi_products_discount_ids[0]){
                                    _.each(promotion.multi_products_discount_ids, function(disc_line_id){
                                        var disc_line_record = _.find(pos_discount_multi_prods, function(obj) { return obj.id == disc_line_id});
                                        if(disc_line_record){
                                            self.check_products_for_disc(disc_line_record, promotion);
                                        }
                                    })
                                }
                            }else if(promotion && promotion.promotion_type == "discount_on_multi_categ"){
                                if(promotion.multi_categ_discount_ids && promotion.multi_categ_discount_ids[0]){
                                    _.each(promotion.multi_categ_discount_ids, function(disc_line_id){
                                        var disc_line_record = _.find(pos_discount_multi_categ, function(obj) { return obj.id == disc_line_id});
                                        if(disc_line_record){
                                            self.check_categ_for_disc(disc_line_record, promotion);
                                        }
                                    })
                                }
                            }
//                            else if(promotion && promotion.promotion_type == "discount_on_above_price"){
//                                if(promotion && promotion.discount_price_ids && promotion.discount_price_ids[0]){
//                                    _.each(promotion.discount_price_ids, function(line_id){
//                                        var line_record = _.find(pos_discount_above_price, function(obj) { return obj.id == line_id});
//                                        if(line_record && line_record.product_brand_ids && line_record.product_brand_ids[0]
//                                            && line_record.product_categ_ids && line_record.product_categ_ids[0]){
//                                            if(line.product.product_brand_id && line.product.product_brand_id[0]){
//                                                if($.inArray(line.product.product_brand_id[0], line_record.product_brand_ids) != -1){
//                                                    if(line.product.pos_categ_id){
//                                                        var product_category = self.pos.db.get_category_by_id(line.product.pos_categ_id[0])
//                                                        if(product_category){
//                                                            if($.inArray(product_category.id, line_record.product_categ_ids) != -1){
//                                                                if(line_record.discount_type == "fix_price"){
//                                                                    if(line.product.lst_price >= line_record.price && line.quantity > 0){
//                                                                        if(line_record.price){
//                                                                            line.set_discount_amt(line_record.price);
//                                                                            line.set_discount_amt_rule(line_record.pos_promotion_id[1]);
//                                                                            line.set_unit_price(((line.get_unit_price()*line.get_quantity()) - line_record.price)/line.get_quantity());
//                                                                            line.set_is_rule_applied(true);
//                                                                            self.pos.chrome.screens.products.order_widget.rerender_orderline(line);
//                                                                        }
//                                                                    }
//                                                                } else if(line_record.discount_type == "percentage"){
//                                                                    if(line_record.discount){
//                                                                        if(line.product.lst_price >= line_record.price && line.quantity > 0){
//                                                                            line.set_discount(line_record.discount);
//                                                                            line.set_is_rule_applied(true);
//                                                                        }
//                                                                    }
//                                                                } else if(line_record.discount_type == "free_product"){
//                                                                    if(line_record.free_product && line_record.free_product[0]){
//                                                                        var product = self.pos.db.get_product_by_id(line_record.free_product[0]);
//                                                                        var new_line = new models.Orderline({}, {pos: self.pos, order: order, product: product});
//                                                                        new_line.set_quantity(1);
//                                                                        new_line.set_unit_price(0);
//                                                                        new_line.set_promotion({
//                                                                            'prom_prod_id':line_record.free_product[0],
//                                                                            'parent_product_id':line.id,
//                                                                            'rule_name':line_record.pos_promotion_id[1],
//                                                                        });
//                                                                        new_line.set_is_rule_applied(true);
//                                                                        order.add_orderline(new_line);
//                                                                        line.set_child_line_id(new_line.id);
//                                                                        line.set_is_rule_applied(true);
//                                                                    }
//                                                                }
//                                                            }
//                                                        }
//                                                    }
//                                                }
//                                            }
//                                        }else if(line_record.product_brand_ids.length <= 0 && line_record.product_categ_ids.length > 0){
//                                            if(line.product.pos_categ_id){
//                                                var product_category = self.pos.db.get_category_by_id(line.product.pos_categ_id[0]);
//                                                if(product_category){
//                                                    if($.inArray(product_category.id, line_record.product_categ_ids) != -1){
//                                                        if(line_record.discount_type == "fix_price"){
//                                                            if(line.product.lst_price >= line_record.price && line.quantity > 0){
//                                                                if(line_record.price){
//                                                                    line.set_discount_amt(line_record.price);
//                                                                    line.set_discount_amt_rule(line_record.pos_promotion_id[1]);
//                                                                    line.set_unit_price(((line.get_unit_price()*line.get_quantity()) - line_record.price)/line.get_quantity());
//                                                                    line.set_is_rule_applied(true);
//                                                                    self.pos.chrome.screens.products.order_widget.rerender_orderline(line);
//                                                                }
//                                                            }
//                                                        } else if(line_record.discount_type == "percentage"){
//                                                            if(line_record.discount){
//                                                                if(line.product.lst_price >= line_record.price && line.quantity > 0){
//                                                                    line.set_discount(line_record.discount);
//                                                                    line.set_is_rule_applied(true);
//                                                                }
//                                                            }
//                                                        } else if(line_record.discount_type == "free_product"){
//                                                            if(line_record.free_product && line_record.free_product[0]){
//                                                                var product = self.pos.db.get_product_by_id(line_record.free_product[0]);
//                                                                var new_line = new models.Orderline({}, {pos: self.pos, order: order, product: product});
//                                                                new_line.set_quantity(1);
//                                                                new_line.set_unit_price(0);
//                                                                new_line.set_promotion({
//                                                                    'prom_prod_id':line_record.free_product[0],
//                                                                    'parent_product_id':line.id,
//                                                                    'rule_name':line_record.pos_promotion_id[1],
//                                                                });
//                                                                new_line.set_is_rule_applied(true);
//                                                                order.add_orderline(new_line);
//                                                                line.set_child_line_id(new_line.id);
//                                                                line.set_is_rule_applied(true);
//                                                            }
//                                                        }
//                                                    }
//                                                }
//                                            }
//                                        }else if(line_record.product_categ_ids.length == 0 && line_record.product_brand_ids.length > 0){
//                                            if(line.product.product_brand_id && line.product.product_brand_id[0]){
//                                                if($.inArray(line.product.product_brand_id[0], line_record.product_brand_ids) != -1){
//                                                    if(line_record.discount_type == "fix_price"){
//                                                        if(line.product.lst_price >= line_record.price && line.quantity > 0){
//                                                            if(line_record.price){
//                                                                line.set_discount_amt(line_record.price);
//                                                                line.set_discount_amt_rule(line_record.pos_promotion_id[1]);
//                                                                line.set_unit_price(((line.get_unit_price()*line.get_quantity()) - line_record.price)/line.get_quantity());
//                                                                line.set_is_rule_applied(true);
//                                                                self.pos.chrome.screens.products.order_widget.rerender_orderline(line);
//                                                            }
//                                                        }
//                                                    } else if(line_record.discount_type == "percentage"){
//                                                        if(line_record.discount){
//                                                            if(line.product.lst_price >= line_record.price && line.quantity > 0){
//                                                                line.set_discount(line_record.discount);
//                                                                line.set_is_rule_applied(true);
//                                                            }
//                                                        }
//                                                    } else if(line_record.discount_type == "free_product"){
//                                                        if(line_record.free_product && line_record.free_product[0]){
//                                                            var product = self.pos.db.get_product_by_id(line_record.free_product[0]);
//                                                            var new_line = new models.Orderline({}, {pos: self.pos, order: order, product: product});
//                                                            new_line.set_quantity(1);
//                                                            new_line.set_unit_price(0);
//                                                            new_line.set_promotion({
//                                                                'prom_prod_id':line_record.free_product[0],
//                                                                'parent_product_id':line.id,
//                                                                'rule_name':line_record.pos_promotion_id[1],
//                                                            });
//                                                            new_line.set_is_rule_applied(true);
//                                                            order.add_orderline(new_line);
//                                                            line.set_child_line_id(new_line.id);
//                                                            line.set_is_rule_applied(true);
//                                                        }
//                                                    }
//                                                }
//                                            }
//                                        }
//                                    });
//                                }
//                            }
                            }
                        });
                    }
                });
            }
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options){
            this.custom_promotion_id=null;
            this.vendor_id=null;
            this.vendor_shared=null;
            this.sarinah_shared=null;
            this.fix_amount_discount=0;
            this.has_aspl_promotion = false;
            _super_orderline.initialize.call(this, attr, options);
        },
        export_for_printing: function(){
            var dict = _super_orderline.export_for_printing.call(this);
            var new_attr = {
                    custom_promotion_id : this.custom_promotion_id,
                    vendor_id : this.vendor_id,
                    vendor_shared : this.vendor_shared,
                    sarinah_shared : this.sarinah_shared,
                    fix_amount_discount : this.fix_amount_discount,
            }
            $.extend(dict, new_attr);
            return dict;
        },
        get_has_aspl_promotion: function(){
            var self = this;
            var line = self.product.id;
            var promotion_list = self.pos.pos_promotions;
            var condition_list = self.pos.pos_conditions;
            var current_time = Number(moment(new Date().getTime()).locale('en').format("H"));
            // Todo check promo lainnya
            if(promotion_list && promotion_list[0]){
                _.each(promotion_list, function(promotion){
                    if((Number(promotion.from_time) <= current_time && Number(promotion.to_time) > current_time) || (!promotion.from_time && !promotion.to_time)){
                        if(promotion && promotion.promotion_type == "buy_x_get_y"){
                            if(promotion.pos_condition_ids && promotion.pos_condition_ids[0]){
                                _.each(promotion.pos_condition_ids, function(pos_condition_line_id){
                                    var line_record = _.find(condition_list, function(obj) { return obj.id == pos_condition_line_id});
                                    if(line_record){
                                        if(line_record.product_x_id && line_record.product_x_id[0] == line.product.id){
                                            return true
                                        }
                                    }
                                });
                            }
                        }
                    }
                });
            }

            return self.has_aspl_promotion;
        },
        get_custom_promotion_id: function(){
            var self = this;
            return self.custom_promotion_id;
        },
        get_vendor_id: function(){
            var self = this;
            return self.vendor_id;
        },
        get_vendor_shared: function(){
            var self = this;
            return self.vendor_shared;
        },
        get_sarinah_shared: function(){
            var self = this;
            return self.sarinah_shared;
        },
        get_fix_amount_discount: function(){
            var self = this;
            return self.fix_amount_discount;
        },
        export_as_JSON: function() {
            var self = this;
            var loaded = _super_orderline.export_as_JSON.call(this);
            loaded.custom_promotion_id = self.get_custom_promotion_id();
            loaded.vendor_id = self.get_vendor_id();
            loaded.vendor_shared = self.get_vendor_shared();
            loaded.sarinah_shared = self.get_sarinah_shared();
            loaded.fix_amount_discount = self.get_fix_amount_discount();
            return loaded;
        },
        init_from_JSON: function(json) {
            var self = this;
            var loaded = _super_orderline.init_from_JSON.call(this,json);
            this.custom_promotion_id = json.custom_promotion_id;
            this.vendor_id = json.vendor_id;
            this.vendor_shared = json.vendor_shared;
            this.sarinah_shared = json.sarinah_shared;
            this.fix_amount_discount = json.fix_amount_discount;
        },
    });

});