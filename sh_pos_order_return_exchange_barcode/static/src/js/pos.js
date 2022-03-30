odoo.define("sh_pos_order_return_exchange_barcode.pos", function (require) {
    "use strict";

    var devices = require("point_of_sale.devices");
    var models = require("point_of_sale.models");
    var DB = require("point_of_sale.DB");
    var screens = require("point_of_sale.screens");
    var gui = require("point_of_sale.gui");
    var PopupWidget = require("point_of_sale.popups");

    models.load_models({
        model: "pos.order",
        label: "load_orders",
        domain: function (self) {
            return [["user_id", "=", self.user.id]];
        },
        loaded: function (self, all_order) {
            self.db.add_barcodes(all_order);
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        scan_product: function (parsed_code) {
            var return_scan = _super_posmodel.scan_product.call(this, parsed_code);
            if (this.config.sh_allow_return || this.config.sh_allow_exchange) {
                if (!return_scan) {
                    var self = this;

                    var order_data = this.db.order_by_barcode[parsed_code.code];
                    var order_id;
                    if (order_data) {
                        order_id = order_data.sh_uid;
                        var order_line = [];
                        if (order_data && order_data.lines) {
                            _.each(order_data.lines, function (each_order_line) {
                                var line_data = self.db.order_line_by_id[each_order_line];
                                if (!line_data) {
                                    line_data = self.db.order_line_by_uid[each_order_line[2].sh_line_id];
                                }
                                if (line_data) {
                                    if (!line_data.sh_return_qty) {
                                        line_data["sh_return_qty"] = 0;
                                    }
                                    order_line.push(line_data);
                                }
                            });
                        }
                    }
                    if (this.config.sh_allow_return) {
                        self.is_return = true;
                        self.is_exchange = false;
                    } else if (this.config.sh_allow_exchange) {
                        self.is_return = false;
                        self.is_exchange = true;
                    } else {
                        self.is_return = true;
                        self.is_exchange = false;
                    }

                    if (order_data) {
                        self.gui.show_popup("order_return_barcode_popup", { lines: order_line, order: order_id });
                    } else {
                        self.gui.show_popup("alert", {
                            title: "Message",
                            body: "Barcode/ QR Code not found",
                        });
                    }
                }
            }
            return true;
        },
    });

    DB.include({
        init: function (options) {
            this._super(options);
            this.order_by_barcode = {};
        },
        add_barcodes(all_order) {
            for (var i = 0, len = all_order.length; i < len; i++) {
                var each_order = all_order[i];
                var splited_ref = each_order.pos_reference.split(" ");
                var order_barcode = splited_ref[1].split("-");
                each_order.barcode = "";
                _.each(order_barcode, function (splited_barcode) {
                    each_order.barcode = each_order.barcode + splited_barcode;
                });
                this.order_by_barcode[each_order.barcode] = each_order;
            }
        },
    });
    
    screens.PaymentScreenWidget.include({
        validate_order: function (force_validation) {
        	var self = this;
        	self._super(force_validation);
            var order_barcode = self.pos.get_order().uid.split("-");
            self.pos.get_order().barcode = "";
            var sh_line_id = [];
            _.each(order_barcode, function (splited_barcode) {
                self.pos.get_order().barcode = self.pos.get_order().barcode + splited_barcode;
            });
            self.pos.db.order_by_uid[self.pos.get_order().export_as_JSON().sh_uid] = self.pos.get_order().export_as_JSON();
            self.pos.db.order_by_barcode[self.pos.get_order().barcode] = self.pos.get_order().export_as_JSON();
            _.each(self.pos.get_order().export_as_JSON().lines, function (each_line) {
                self.pos.db.order_line_by_uid[each_line[2].sh_line_id] = each_line[2];
                sh_line_id.push(each_line[2].sh_line_id);
            });
            self.pos.get_order()["sh_line_id"] = sh_line_id;
            
            _.each(self.pos.get_order().export_as_JSON().lines, function (each_line) {
            	
            	if (each_line[2] && each_line[2].sh_line_id) {
                    if (self.pos.get_order().export_as_JSON().is_return_order) {
                        if (each_line[2].old_line_id) {
                            if (self.pos.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"]) {
                            	each_line[2]["sh_return_qty"] = 0;
                                self.pos.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = self.pos.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] + each_line[2].qty * -1;
                                
                            } else {
                                each_line[2]["sh_return_qty"] = 0;
                                self.pos.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = each_line[2].qty * -1;
                                                                    
                                if(self.pos.db.order_line_by_id[each_line[2].line_id]){
                                	self.pos.db.order_line_by_id[each_line[2].line_id]["sh_return_qty"] = each_line[2].qty * -1;                                    	
                                }
                                
                            }
                        } else {
                            each_line[2]["sh_return_qty"] = 0;
                        }
                    } else if (self.pos.get_order().export_as_JSON().is_exchange_order) {
                        if (each_line[2].old_line_id) {
                            if (self.pos.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"]) {
                                each_line[2]["sh_return_qty"] = 0;
                                self.pos.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = self.pos.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] + each_line[2].qty * -1;
                                
                            } else {
                                each_line[2]["sh_return_qty"] = 0;
                                self.pos.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = each_line[2].qty * -1;
                                
                                if(self.pos.db.order_line_by_id[each_line[2].line_id]){
                                	self.pos.db.order_line_by_id[each_line[2].line_id]["sh_return_qty"] = each_line[2].qty * -1;
                                }
                                
                            }
                        } else {
                            each_line[2]["sh_return_qty"] = 0;
                        }
                    } else {
                        each_line[2]["sh_return_qty"] = 0;
                    }
                    self.pos.db.order_line_by_uid[each_line[2].sh_line_id] = each_line[2];
                    sh_line_id.push(each_line[2].sh_line_id);
                }
            	
            });
        	
        },
    });

    var OrderReturnBarcodePopupWidget = PopupWidget.extend({
        template: "OrderReturnBarcodePopupWidget",
        show: function (options) {
            var self = this;
            options = options || {};
            this.order = options.order;
            this.lines = options.lines;
            this.no_return_line_id = [];
            this.return_line = [];
            this._super(options);
            if (self.pos.config.sh_allow_exchange) {
                self.$(".sh_same_product_checkbox").addClass("show_checkbox");
                self.$(".sh_return_exchange_radio").addClass("sh_exchange_order");
                self.pos.is_return = false;
                self.pos.is_exchange = true;
            }
            if (self.pos.config.sh_allow_return) {
                self.$(".sh_return_exchange_radio").removeClass("sh_exchange_order");
                self.$(".sh_same_product_checkbox").removeClass("show_checkbox");
                self.pos.is_return = true;
                self.pos.is_exchange = false;
            }
            self.$("#exchange_radio").click(function () {
                self.$(".sh_same_product_checkbox").addClass("show_checkbox");
                self.$(".sh_return_exchange_radio").addClass("sh_exchange_order");
                self.pos.is_return = false;
                self.pos.is_exchange = true;
                self.$(".title").text("Exchange Products");
                self.$(".complete_return").text("Complete Exchange");
                self.$(".confirm").text("Exchange");
                self.$(".return_exchange_popup_header").text("Exchange Qty.");
            });
            self.$("#return_radio").click(function () {
                self.$(".sh_return_exchange_radio").removeClass("sh_exchange_order");
                self.$(".sh_same_product_checkbox").removeClass("show_checkbox");
                self.pos.is_return = true;
                self.pos.is_exchange = false;
                self.$(".title").text("Return Products");
                self.$(".complete_return").text("Complete Return");
                self.$(".confirm").text("Return");
                self.$(".return_exchange_popup_header").text("Return Qty.");
            });

            if ((self.pos.is_return && !self.pos.config.sh_return_more_qty) || self.pos.is_exchange) {
                this.$(".return_qty_input").keyup(function (event) {
                    if (event.currentTarget.value) {
                        if (parseInt(event.currentTarget.value) > parseInt(event.currentTarget.closest("tr").children[1].innerText)) {
                            event.currentTarget.classList.add("more_qty");
                            event.currentTarget.value = "";
                        } else {
                            event.currentTarget.classList.remove("more_qty");
                        }
                    }
                });
            }
            this.$(".complete_return").click(function (event) {
                _.each($(".return_data_line"), function (each_data_line) {
                    if (each_data_line.children[2].children[0].value != "0") {
                        var order_line = self.pos.db.order_line_by_id[each_data_line.dataset.line_id];
                        if (!order_line) {
                            order_line = self.pos.db.order_line_by_uid[each_data_line.dataset.line_id];
                        }
                        order_line["qty"] = each_data_line.children[1].innerText;
                        self.return_line.push(order_line);
                    } else {
                        self.no_return_line_id.push(parseInt(each_data_line.dataset.line_id));
                    }
                });
                self.return_product();
            });
        },
        return_product: function () {
            var self = this;
            var order_id;
            _.each($(".return_data_line"), function (each_data_line) {
                order_id = each_data_line.dataset.order_id;
            });
            var order_data = self.pos.db.order_by_uid[order_id];
            if (!order_data) {
                order_data = self.pos.db.order_by_id[order_id];
            }
            var current_order = self.pos.get_order();
            if (self.pos.config.is_table_management) {
                current_order.destroy();
                self.pos.add_new_order();
            } else {
                self.pos.get_order().destroy();
            }
            var current_order = self.pos.get_order();
            _.each(self.return_line, function (each_line) {
                if (self.pos.is_return) {
                    current_order["return_order"] = true;
                }
                if (self.pos.is_exchange) {
                    current_order["exchange_order"] = true;
                }
                var product = self.pos.db.get_product_by_id(each_line.product_id[0]);
                if (!product) {
                    product = self.pos.db.get_product_by_id(each_line.product_id);
                }
                current_order.add_product(product, {
                    quantity: -each_line.qty,
                    price: each_line.price_unit,
                    line_id: each_line.id,
                    old_line_id: each_line.sh_line_id,
                    discount: each_line.discount,
                });
                if (order_data.partner_id && order_data.partner_id[0]) {
                    self.pos.get_order().set_client(self.pos.db.get_partner_by_id(order_data.partner_id[0]));
                }else if(self.pos.db.get_partner_by_id(order_data.partner_id)){
                	self.pos.get_order().set_client(self.pos.db.get_partner_by_id(order_data.partner_id));
                }
                if (self.pos.is_exchange && self.$("#exchange_checkbox")[0].checked) {
                    current_order.add_product(product, {
                        quantity: each_line.qty,
                        price: each_line.price_unit,
                        merge: false,
                        discount: each_line.discount,
                    });
                }
                if (each_line.old_qty) {
                    each_line.qty = each_line.old_qty;
                }
            });
            current_order.old_sh_uid = order_data.sh_uid;
            if (order_data.pos_reference) {
                current_order.old_pos_reference = order_data.pos_reference;
            } else {
                current_order.old_pos_reference = order_data.name;
            }
            if (self.pos.is_return) {
                $(".pay").click();
            }
        },
        click_confirm: function () {
            var self = this;
            if (document.getElementById("return_radio") && document.getElementById("return_radio").checked) {
                self.pos.is_return = true;
                self.pos.is_exchange = false;
            }
            if (document.getElementById("exchange_radio") && document.getElementById("exchange_radio").checked) {
                self.pos.is_return = false;
                self.pos.is_exchange = true;
            }
            _.each($(".return_data_line"), function (each_data_line) {
                if (each_data_line.children[2].children[0].value != "0" && each_data_line.children[2].children[0].value != "") {
                    var order_line = self.pos.db.order_line_by_id[each_data_line.dataset.line_id];
                    if (!order_line) {
                        order_line = self.pos.db.order_line_by_uid[each_data_line.dataset.line_id];
                    }
                    order_line["old_qty"] = order_line["qty"];
                    order_line["qty"] = each_data_line.children[2].children[0].value;
                    self.return_line.push(order_line);
                } else {
                    self.no_return_line_id.push(parseInt(each_data_line.dataset.line_id));
                }
            });
            self.return_product();
            this.gui.close_popup();
        },
    });
    gui.define_popup({
        name: "order_return_barcode_popup",
        widget: OrderReturnBarcodePopupWidget,
    });
});
