odoo.define("sh_pos_receipt_extend.pos", function (require) {
    "use strict";

    var screens = require("point_of_sale.screens");
    var rpc = require("web.rpc");
    var core = require("web.core");
    var qweb = core.qweb;

    screens.ReceiptScreenWidget.include({
        show: function () {
            var self = this;
            self.pos.get_order()["is_barcode_exit"] = true;
            self.pos.get_order()["is_qr_exit"] = true;
            
            var order = this.pos.get_order();
            if (this.pos.config.sh_pos_order_number) {                
                setTimeout(function(){
                    rpc.query({
                        model: "pos.order",
                        method: "search_read",
                        domain: [["pos_reference", "=", order["name"]]],
                        fields: ["name"],
                    }).then(function (callback) {
                    	if(callback && callback[0] && callback[0]['name']){
                    		self.pos.get_order()["pos_order_number"] = callback[0]['name']
                            self.$(".pos-receipt-container").html(qweb.render("OrderReceipt", self.get_receipt_render_env()));
                            
                            self.handle_auto_print();
                    	}
                        
                        
                    });
                },2000);
            } 
            self._super();
            
        },
        handle_auto_print: function(){
        	var self = this;
        	if(self.pos.config.sh_pos_order_number){
        		if(self.pos.get_order()['pos_order_number']){
        			self._super();
        		}
        	}else{
        		self._super();
        	}
        },
        get_receipt_render_env: function () {
            var order = this.pos.get_order();
            
            var order_barcode = order.name.split(" ")
            if(order_barcode && order_barcode[1]){
            	order_barcode = order_barcode[1].split("-");
            	order.barcode = "";
                _.each(order_barcode, function (splited_barcode) {
                    order.barcode = order.barcode + splited_barcode;
                });
            }
            var render_env = this._super();
            render_env.order.barcode = order.barcode;
            return render_env;
//            return {
//                widget: this,
//                pos: this.pos,
//                order: order,
//                receipt: order.export_for_printing(),
//                orderlines: order.get_orderlines(),
//                paymentlines: order.get_paymentlines(),
//            };
        },
        render_receipt: function () {
            this._super();
            var self = this;
            var order = this.pos.get_order();
            var image_path = $("img.barcode_class").attr("src");
            $.ajax({
                url: image_path,
                type: "HEAD",
                error: function () {
                    self.pos.get_order()["is_barcode_exit"] = false;
                    self.$(".pos-receipt-container").html(qweb.render("OrderReceipt", self.get_receipt_render_env()));
                },
                success: function () {
                    self.pos.get_order()["is_barcode_exit"] = true;
                    self.$(".pos-receipt-container").html(qweb.render("OrderReceipt", self.get_receipt_render_env()));
                },
            });
            var image_path = $("img.qr_class").attr("src");
            $.ajax({
                url: image_path,
                type: "HEAD",
                error: function () {
                    self.pos.get_order()["is_qr_exit"] = false;
                    self.$(".pos-receipt-container").html(qweb.render("OrderReceipt", self.get_receipt_render_env()));
                },
                success: function () {
                    self.pos.get_order()["is_qr_exit"] = true;
                    self.$(".pos-receipt-container").html(qweb.render("OrderReceipt", self.get_receipt_render_env()));
                },
            });

            if (this.pos.config.sh_pos_order_number) {
                var invoiced = new $.Deferred();
                
                setTimeout(function(){
                    rpc.query({
                        model: "pos.order",
                        method: "search_read",
                        domain: [["pos_reference", "=", order["name"]]],
                        fields: ["name"],
                    }).then(function (callback) {
                    	if(callback && callback[0] && callback[0]['name']){
                    		self.pos.get_order()["pos_order_number"] = callback[0]['name']
                            self.$(".pos-receipt-container").html(qweb.render("OrderReceipt", self.get_receipt_render_env()));
                    	}
                    });
                },700);
            } else {
                this._super();
            }

            if (this.pos.config.sh_pos_receipt_invoice) {
                var invoiced = new $.Deferred();
                rpc.query({
                    model: "pos.order",
                    method: "search_read",
                    domain: [["pos_reference", "=", order["name"]]],
                    fields: ["account_move","name"],
                }).then(function (orders) {
                    if (orders.length > 0 && orders[0]["account_move"] && orders[0]["account_move"][1]) {
                        var invoice_number = orders[0]["account_move"][1].split(" ")[0];
                        self.pos.get_order()["invoice_number"] = invoice_number;
                        self.$(".pos-receipt-container").html(qweb.render("OrderReceipt", self.get_receipt_render_env()));
                    }
                    invoiced.resolve();
                });
                return invoiced;
            } else {
                this._super();
            }

        },
    });

//    Matrica - LLHa
    var models = require('point_of_sale.models');

    var _super = models.Orderline;
    models.Orderline = models.Orderline.extend({
        generate_wrapped_product_name: function() {
        var MAX_LENGTH = 60; // 40 * line ratio of .6
        var wrapped = [];
        var name = this.get_product().display_name;
        var current_line = "";

        while (name.length > 0) {
            var space_index = name.indexOf(" ");

            if (space_index === -1) {
                space_index = name.length;
            }

            if (current_line.length + space_index > MAX_LENGTH) {
                if (current_line.length) {
                    wrapped.push(current_line);
                }
                current_line = "";
            }

            current_line += name.slice(0, space_index + 1);
            name = name.slice(space_index + 1);
        }

        if (current_line.length) {
            wrapped.push(current_line);
        }

        return wrapped;
    },

        get_product_name_att: function(){

            var name = this.get_product().display_name;
            var default_code = this.get_product().default_code;

            var name_att = name.replace("["+default_code+"] ", '');
            return name_att

        },
        export_for_printing: function(){
            var json = _super.prototype.export_for_printing.apply(this,arguments);
            json.name = this.get_product_name_att();
            json.default_code = this.get_product().default_code;
            return json;
        },
    });
});
