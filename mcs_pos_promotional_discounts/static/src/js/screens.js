odoo.define('mcs_pos_promotional_discounts.screens', function (require) {
	"use strict";
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var _t = core._t;
    var QWeb = core.qweb;


	
	screens.OrderWidget.include({
		get_offers: function(product){
			var self = this;
			var product_id = product.id;
			var offers = []
			_.each(self.pos.db.promotions_by_sequence_id, function(promotions){
				if(promotions.offer_type == 'discount_on_products'){
					if(self.pos.db.discount_items){
						var flag = false
						var discount_val = 0
						var val = 0
						_.each(self.pos.db.discount_items, function(item){
							flag = false
							if(promotions.discounted_ids.includes(item.id)){
								if(!flag && item.apply_on == "1_products"){
									if(item.product_id[0] == product.id){
										discount_val = item.percent_discount
										flag = true
									}
								}
								if(!flag && item.apply_on == "2_categories"){
									if(item.categ_id[0] == product.categ_id[0]){
										discount_val = item.percent_discount
										flag = true
									}
								}
								if(!flag && item.apply_on == "3_all"){
									discount_val = item.percent_discount
									flag = true
								}
								if(flag){
									if(val == 0){
										val+=1
										item['offer_name'] = "Get " + item.discount + " Discount"
										offers.push(item)
									}
								}
							}
						});
					}
				}
				else if (promotions.offer_type == 'buy_x_get_y'){
					if(self.pos.db.buy_x_get_y){
						for (var i = 1; i <= self.pos.db.buy_x_get_y.length; i++){
							var item = self.pos.db.buy_x_get_y[self.pos.db.buy_x_get_y.length-i]
							if(promotions.buy_x_get_y_ids.includes(item.id)){
								if(item.product_x_id[0] == product_id){
									item['offer_name'] = "Buy " + item.qty_x + " " + product.display_name + " & Get " +item.product_y_id[1]
									offers.push(item)
								}
							}
						}
					}
				}
				else if (promotions.offer_type == 'buy_x_get_y_qty'){
					if(self.pos.db.buy_x_get_y_qty){
						for (var i = 1; i <= self.pos.db.buy_x_get_y_qty.length; i++){
							var item = self.pos.db.buy_x_get_y_qty[self.pos.db.buy_x_get_y_qty.length-i]
							if(promotions.buy_x_get_y_qty_ids.includes(item.id)){
								if(item.product_x_id[0] == product_id){
									item['offer_name'] = "Buy " + item.qty_x + " " + product.display_name + " & Get " + item.qty_y + " "  +item.product_y_id[1]
									offers.push(item)
								}
							}
						}
					}
				}
				else if (promotions.offer_type == 'buy_x_get_discount_on_y'){
					if(self.pos.db.buy_x_get_discount_on_y){
						for (var i = 1; i <= self.pos.db.buy_x_get_discount_on_y.length; i++){
							var item = self.pos.db.buy_x_get_discount_on_y[self.pos.db.buy_x_get_discount_on_y.length-i]
							if(promotions.buy_x_get_discount_on_y_ids.includes(item.id)){
								if(item.product_x_id[0] == product_id){
									item['offer_name'] = "Buy " + item.qty_x + " " + product.display_name + " & Get " + item.discount + "% Discount on" +item.product_y_id[1]
									offers.push(item)
								}				
							}
						}
					}
				}
			})
			return offers
		}
    });
});