odoo.define("sh_pos_order_list.pos", function (require) {
    "use strict";
    
    var models = require("point_of_sale.models");
    var DB = require("point_of_sale.DB");
    var screens = require("point_of_sale.screens");
    var gui = require("point_of_sale.gui");
    var core = require("web.core");
    var QWeb = core.qweb;
    var rpc = require("web.rpc");
    var session = require("web.session");
    var field_utils = require("web.field_utils");
    
    models.load_models({
        label: "Loading POS Order",
        loaded: function (self) {
            if (self && self.config && self.config.sh_mode && self.config.sh_mode == "offline_mode") {
                rpc.query({
                    model: "pos.order",
                    method: "search_order_length",
                    args: [self.config],
                }).then(function (orders) {
                    if (orders) {
                        if (orders["order"]) {
                            self.order_length = orders["order"].length;
                            self.db.all_orders(orders["order"]);
                            self.db.all_display_order = orders["order"];
                        }
                        if (orders["order_line"]) {
                            self.db.all_orders_line(orders["order_line"]);
                        }
                    }
                });
            }
            if (self && self.config && self.config.sh_mode && self.config.sh_mode == "online_mode") {
                rpc.query({
                    model: "pos.order",
                    method: "search_read",
                    domain: [["user_id", "=", self.user.id]],
                }).then(function (all_order) {
                	
                    self.order_length = all_order.length;
                    self.db.all_display_order = all_order;
                });
            }
        },
    });

    models.load_models({
        model: "pos.session",
        label: "load_sessions",
        domain: function (self) {
            return [["user_id", "=", self.user.id]];
        },
        loaded: function (self, all_session) {
            self.db.all_sessions(all_session);
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order.initialize.apply(this, arguments);
            this.sequence_number = this.pos.pos_session.sequence_number++;
            this.sh_uid = this.generate_sh_unique_id();
        },
        generate_sh_unique_id: function () {
            // Generates a public identification number for the order.
            // The generated number must be unique and sequential. They are made 12 digit long
            // to fit into EAN-13 barcodes, should it be needed

            function zero_pad(num, size) {
                var s = "" + num;
                while (s.length < size) {
                    s = "0" + s;
                }
                return s;
            }

            return this.sequence_number + this.name.split(" ")[1];
        },
        init_from_JSON: function (json) {
            var res = _super_order.init_from_JSON.apply(this, arguments);
            if (json.pos_session_id !== this.pos.pos_session.id) {
                this.sequence_number = this.pos.pos_session.sequence_number++;
            } else {
                this.sequence_number = json.sequence_number;
                this.pos.pos_session.sequence_number = Math.max(this.sequence_number + 1, this.pos.pos_session.sequence_number);
            }
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            var sh_line_id = [];
            json.sh_uid = this.sh_uid;
            json.sequence_number = this.sequence_number;

            if (this.orderlines.models) {
                _.each(this.orderlines.models, function (each_order_line) {
                    if (each_order_line.sh_line_id) {
                        sh_line_id.push(each_order_line.sh_line_id);
                    }
                });
            }
            this.formatted_validation_date = field_utils.format.datetime(moment(this.validation_date), {}, { timezone: false });
            json.sh_order_date = this.formatted_validation_date;
            json.sh_order_line_id = sh_line_id;

            return json;
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            _super_orderline.initialize.call(this, attr, options);
            this.sequence_number = this.pos.pos_session.sequence_number++;
            this.sh_line_id = this.generate_sh_line_unique_id();
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.call(this);
            json.sh_line_id = this.generate_sh_line_unique_id();
            return json;
        },
        generate_sh_line_unique_id: function () {
            // Generates a public identification number for the order.
            // The generated number must be unique and sequential. They are made 12 digit long
            // to fit into EAN-13 barcodes, should it be needed

            function zero_pad(num, size) {
                var s = "" + num;
                while (s.length < size) {
                    s = "0" + s;
                }
                return s;
            }
            return "sh" + this.sequence_number + this.order.name.split(" ")[1];
        },
        init_from_JSON: function (json) {
            var res = _super_orderline.init_from_JSON.apply(this, arguments);
            if (json.pos_session_id !== this.pos.pos_session.id) {
                this.sequence_number = this.pos.pos_session.sequence_number++;
            } else {
                this.sequence_number = json.sequence_number;
                this.pos.pos_session.sequence_number = Math.max(this.sequence_number + 1, this.pos.pos_session.sequence_number);
            }
        },
    });

    var OrderHistoryButton = screens.ActionButtonWidget.extend({
        template: "OrderHistoryButton",
        button_click: function () {
            var self = this;
            self.gui.show_screen("order_screen");
        },
    });

    screens.define_action_button({
        name: "order_history",
        widget: OrderHistoryButton,
        condition: function () {
            return this.pos.config.sh_enable_order_list;
        },
    });

    DB.include({
        init: function (options) {
            this._super(options);
            this.all_order = [];
            this.order_by_id = {};
            this.order_by_uid = {};
            this.order_line_by_id = {};
            this.order_line_by_uid = {};
            this.all_session = [];
            this.new_order;
            this.all_display_order = [];
            this.all_order_temp = [];
        },
        all_sessions: function (all_session) {
            this.all_session = all_session;
        },
        all_orders: function (all_order) {
            var self = this;
            var new_write_date = "";
            for (var i = 0, len = all_order.length; i < len; i++) {
                var each_order = all_order[i];
                if (!this.order_by_id[each_order.id]) {
                    this.all_order.push(each_order);
                    this.all_order_temp.push(each_order);
                    this.order_by_id[each_order.id] = each_order;
                    this.order_by_uid[each_order.sh_uid] = each_order;
                }
            }
        },
        all_orders_line: function (all_order_line) {
            var new_write_date = "";
            for (var i = 0, len = all_order_line.length; i < len; i++) {
                var each_order_line = all_order_line[i];
                this.order_line_by_id[each_order_line.id] = each_order_line;
                this.order_line_by_uid[each_order_line.sh_line_id] = each_order_line;
            }
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        get_last_session_order: function (orders) {
            var self = this;
            for (var i = 0; i < self.db.all_session.length; i++) {
                if (i < self.db.all_session.length - 1) {
                    if (self.db.all_session[i].stop_at && self.db.all_session[i + 1].stop_at) {
                        if (self.db.all_session[i].stop_at < self.db.all_session[i + 1].stop_at) {
                            var temp = self.db.all_session[i];
                            self.db.all_session[i] = self.db.all_session[i + 1];
                            self.db.all_session[i + 1] = temp;
                        }
                    }
                }
            }
            var session = [];
            for (var i = 0; i < self.config.sh_last_no_session; i++) {
                session.push(self.db.all_session[i].name);
            }
            return orders.filter(function (order) {
                return session.includes(order.session_id[1]);
            });
        },
        get_current_session_order: function (orders) {
            var self = this;
            return orders.filter(function (order) {
                return order.session_id[0] == self.pos_session.id;
            });
        },
        get_last_day_order: function (orders) {
            var self = this;
            return orders.filter(function (order) {
                var date = new Date();
                var last = new Date(date.getTime() - self.config.sh_last_no_days * 24 * 60 * 60 * 1000);
                var last = last.getFullYear() + "-" + ("0" + (last.getMonth() + 1)).slice(-2) + "-" + ("0" + last.getDate()).slice(-2);
                var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                return order.date_order.split(" ")[0] > last && order.date_order.split(" ")[0] <= today_date;
            });
        },
        get_current_day_order: function (orders) {
            return orders.filter(function (order) {
                var date = new Date();
                var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                return order.date_order.split(" ")[0] === today_date;
            });
        },
        _save_to_server: function (orders, options) {
            if (!orders || !orders.length) {
                return Promise.resolve([]);
            }

            options = options || {};

            var self = this;
            var timeout = typeof options.timeout === "number" ? options.timeout : 30000 * orders.length;

            // Keep the order ids that are about to be sent to the
            // backend. In between create_from_ui and the success callback
            // new orders may have been added to it.
            var order_ids_to_sync = _.pluck(orders, "id");

            // we try to send the order. shadow prevents a spinner if it takes too long. (unless we are sending an invoice,
            // then we want to notify the user that we are waiting on something )
            var args = [
                _.map(orders, function (order) {
                    order.to_invoice = options.to_invoice || false;
                    return order;
                }),
            ];
            args.push(options.draft || false);
            return rpc
                .query(
                    {
                        model: "pos.order",
                        method: "create_from_ui",
                        args: args,
                        kwargs: { context: session.user_context },
                    },
                    {
                        timeout: timeout,
                        shadow: !options.to_invoice,
                    }
                )
                .then(function (server_ids) {
                    _.each(order_ids_to_sync, function (order_id) {
                        self.db.remove_order(order_id);
                    });
                    self.set("failed", false);
                    return server_ids;
                })
                .catch(function (reason) {
                    var error = reason.message;
                    if (error.code === 200) {
                        // Business Logic Error, not a connection problem
                        //if warning do not need to display traceback!!
                        if (error.data.exception_type == "warning") {
                            delete error.data.debug;
                        }

                        // Hide error if already shown before ...
                        if ((!self.get("failed") || options.show_error) && !options.to_invoice) {
                            self.gui.show_popup("error-traceback", {
                                title: error.data.message,
                                body: error.data.debug,
                            });
                        }
                        self.set("failed", error);
                    }
                    console.warn("Failed to send orders:", orders);

                    self.formatted_validation_date = field_utils.format.datetime(moment(self.get_order().validation_date), {}, { timezone: false });

                    var sh_line_id = [];
                    _.each(orders, function (each_order) {
                        if (!self.db.order_by_uid[each_order.data.sh_uid]) {
                            if (each_order["data"]["amount_paid"] >= parseInt(each_order["data"]["amount_total"])) {
                                each_order["data"]["state"] = "paid";
                            } else {
                                each_order["data"]["state"] = "draft";
                            }
                            each_order["data"]["date_order"] = self.formatted_validation_date;
                            each_order["data"]["pos_reference"] = each_order.data.name;
                            self.db.all_order.push(each_order.data);
                            

//                            self.db.all_order.push(each_order.data);
                            self.db.all_display_order.push(each_order.data);
                            
                            self.db.order_by_uid[each_order.data.sh_uid] = each_order.data;
                            _.each(each_order.data.lines, function (each_line) {
                                if (each_line[2] && each_line[2].sh_line_id) {
                                    self.db.order_line_by_uid[each_line[2].sh_line_id] = each_line[2];
                                    sh_line_id.push(each_line[2].sh_line_id);
                                }
                            });
                            each_order.data["sh_line_id"] = sh_line_id;
                        }
                    });

                    self.gui.show_sync_error_popup();
                    throw error;
                });
        },
    });

    var OrderScreenWidget = screens.ScreenWidget.extend({
        template: "OrderScreenWidget",

        show: function (options) {
            var self = this;
            
            
            $(".sh_pagination").pagination({
                pages: Math.ceil(self.pos.order_length / self.pos.config.sh_how_many_order_per_page),
                displayedPages: 1,
                edges: 1,
                cssStyle: "light-theme",
                showPageNumbers: false,
                showNavigator: true,
                onPageClick: function (pageNumber) {
                    try {
                        rpc.query({
                            model: "pos.order",
                            method: "search_order",
                            args: [self.pos.config, pageNumber + 1],
                        })
                            .then(function (orders) {
                                if (orders) {
                                    if (orders["order"].length == 0) {
                                        /*$($(".next").parent()).addClass("disabled");
                                        $(".next").replaceWith(function () {
                                            $("<span class='current next'>Next</span>");
                                        });*/
                                    }
                                }
                            })
                            .catch(function (reason) {
                                var showFrom = parseInt(self.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber + 1) - 1);
                                var showTo = showFrom + parseInt(self.pos.config.sh_how_many_order_per_page);
                                self.pos.db.all_order = self.pos.db.all_order_temp.slice(showFrom, showTo);
                                if (self.pos.db.all_order && self.pos.db.all_order.length == 0) {
                                    /*$($(".next").parent()).addClass("disabled");
                                    $(".next").replaceWith(function () {
                                        $("<span class='current next'>Next</span>");
                                    });*/
                                }
                            });

                        rpc.query({
                            model: "pos.order",
                            method: "search_order",
                            args: [self.pos.config, pageNumber],
                        })
                            .then(function (orders) {
                                self.pos.db.all_order = [];
                                self.pos.db.order_by_id = {};
                                
                                if (orders) {
                                    if (orders["order"]) {
                                        self.pos.db.all_orders(orders["order"]);                                        
                                    }
                                    if (orders["order_line"]) {
                                        self.pos.db.all_orders_line(orders["order_line"]);
                                    }
                                }
                                self.all_order = self.pos.db.all_order;
                                self.render_list(self.pos.db.all_order);

                            })
                            .catch(function (reason) {
                                var showFrom = parseInt(self.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1);
                                var showTo = showFrom + parseInt(self.pos.config.sh_how_many_order_per_page);
                                self.pos.db.all_order = self.pos.db.all_display_order.slice(showFrom, showTo);
                                self.render_list(self.pos.db.all_order);
                            });
                    } catch (error) {}
                },
            });
            
            $(".sh_pagination").pagination("selectPage", 1);
            
            this._super(options);
            self.order_line = [];
            self.display_order = [];
            self.test_variable = self.pos.db.all_session;

            if (self.pos.db.all_order.length > 0) {
                var today = new Date();
                var dd = today.getDate();
                var mm = today.getMonth() + 1;
                var yyyy = today.getFullYear();
                var today_date = yyyy + "-" + mm + "-" + dd;
                if (self.pos.config.sh_load_order_by == "day_wise") {
                    if (self.pos.config.sh_day_wise_option == "current_day") {
                        self.pos.db.all_order = self.pos.get_current_day_order(self.pos.db.all_order);
                    } else if (self.pos.config.sh_day_wise_option == "last_no_day") {
                        if (self.pos.config.sh_last_no_days != 0) {
                            self.pos.db.all_order = self.pos.get_last_day_order(self.pos.db.all_order);
                        }
                    }
                } else if (self.pos.config.sh_load_order_by == "session_wise") {
                    if (self.pos.config.sh_session_wise_option == "current_session") {
                        self.pos.db.all_order = self.pos.get_current_session_order(self.pos.db.all_order);
                    } else if (self.pos.config.sh_session_wise_option == "last_no_session") {
                        if (self.pos.config.sh_last_no_session != 0) {
                            self.pos.db.all_order = self.pos.get_last_session_order(self.pos.db.all_order);
                        }
                    }
                }
            }

//            self.render_list(self.pos.db.all_order);

            this.$("#date1").change(function (e) {
                var selected_orders = self.get_orders_by_date(e.target.value);
                if (selected_orders.length > 0) {
                    self.render_list(selected_orders);
                } else {
                    self.render_list([]);
                }
            });
            this.$(".custom_searchbox input").keyup(function (e) {
            	if(e.target.value){
            		var selected_orders = self.get_orders_by_name(e.target.value);
                    if (selected_orders.length > 0) {
                        self.render_list(selected_orders);
                    } else {
                        self.render_list([]);
                    }
            	}else{
            		$(".sh_pagination").pagination("selectPage", 1);
            	}
            });
            
            
        },
        get_orders_by_date: function (date) {
            return _.filter(this.pos.db.all_order, function (template) {
                if (template.date_order.indexOf(date) > -1) {
                    return true;
                } else {
                    return false;
                }
            });
        },
        get_orders_by_name: function (name) {
            var self = this;
            return _.filter(self.pos.db.all_display_order, function (template) {
                if (template.name.indexOf(name) > -1) {
                    return true;
                } else if (template["pos_reference"].indexOf(name) > -1) {
                    return true;
                } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                    return true;
                } else {
                    return false;
                }
            });
        },
        events: {
            "click .button.back": "click_back",
            "click tr.sh_order_line": "click_line",
            "click .print_order": "print_order",
            "click .re_order_icon": "re_order",
        },
        re_order: function (event) {
            var self = this;
            var order_id = event.currentTarget.closest("tr").attributes[0].value;
            var order_data = self.pos.db.order_by_uid[order_id];
            if (!order_data) {
                order_data = self.pos.db.order_by_id[order_id];
            }
            var order_line = [];
            var current_order = self.pos.get_order();
            if (self.pos.config.is_table_management) {
                current_order.destroy();
                self.pos.add_new_order();
            } else {
                self.pos.get_order().destroy();
            }
            var current_order = self.pos.get_order();

            _.each(order_data.lines, function (each_order_line) {
                var line_data = self.pos.db.order_line_by_id[each_order_line];
                if (!line_data) {
                    line_data = self.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                }
                var product = self.pos.db.get_product_by_id(line_data.product_id[0]);
                if (!product) {
                    product = self.pos.db.get_product_by_id(line_data.product_id);
                }
                if (product) {
                    current_order.add_product(product, {
                        quantity: line_data.qty,
                        price: line_data.price_unit,
                        discount: line_data.discount,
                    });
                }
            });
            if (order_data.partner_id && order_data.partner_id[0]) {
                self.pos.get_order().set_client(self.pos.db.get_partner_by_id(order_data.partner_id[0]));
            }
            current_order.assigned_config = order_data.assigned_config;
        },
        print_order: function (event) {
            var self = this;
            var order_id = event.currentTarget.closest("tr").attributes[0].value;

            var order_data = self.pos.db.order_by_uid[order_id];
            if (!order_data) {
                order_data = self.pos.db.order_by_id[order_id];
            }
            var order_line = [];
            var current_order = self.pos.get_order();
            if (self.pos.config.is_table_management) {
                current_order.destroy();
                self.pos.add_new_order();
            } else {
                self.pos.get_order().destroy();
            }
            var current_order = self.pos.get_order();

            _.each(order_data.lines, function (each_order_line) {
                var line_data = self.pos.db.order_line_by_id[each_order_line];
                if (!line_data) {
                    line_data = self.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                }

                var product = self.pos.db.get_product_by_id(line_data.product_id[0]);
                if (!product) {
                    product = self.pos.db.get_product_by_id(line_data.product_id);
                }
                if (product) {
                    current_order.add_product(product, {
                        quantity: line_data.qty,
                        price: line_data.price_unit,
                        discount: line_data.discount,
                    });
                }
            });
            current_order.name = order_data.pos_reference;
            current_order.assigned_config = order_data.assigned_config;
            self.pos.gui.show_screen("receipt");
        },
        click_line: function (event) {
            var self = this;
            self.hasclass = true;
            if ($(event.currentTarget).hasClass("highlight")) {
                self.hasclass = false;
            }
            self.$(".sh_order_list .highlight").removeClass("highlight");
            $(event.currentTarget).closest("table").find(".show_order_detail").removeClass("show_order_detail");
            $(event.currentTarget).closest("table").find(".show_order_detail").removeClass("show_order_detail");
            $(event.currentTarget).closest("table").find(".show_order_detail").removeClass("show_order_detail");
            var order_id = $(event.currentTarget).data("id");
            var order_data = self.pos.db.order_by_uid[order_id];

            if (order_data && self.hasclass) {
                self.selected_pos_order = order_id;

                if (order_data.sh_line_id) {
                    _.each(order_data.sh_line_id, function (pos_order_line) {
                        $(event.currentTarget).addClass("highlight");
                        $(event.currentTarget)
                            .closest("table")
                            .find("tr#" + order_data.pos_reference.split(" ")[1])
                            .addClass("show_order_detail");
                        $(event.currentTarget)
                            .closest("table")
                            .find("#" + pos_order_line)
                            .addClass("show_order_detail");
                    });
                } else {
                    _.each(order_data.lines, function (pos_order_line) {
                        $(event.currentTarget).addClass("highlight");
                        $(event.currentTarget)
                            .closest("table")
                            .find("tr#" + order_data.pos_reference.split(" ")[1])
                            .addClass("show_order_detail");
                        $(event.currentTarget)
                            .closest("table")
                            .find("#" + self.pos.db.order_line_by_id[pos_order_line].id)
                            .addClass("show_order_detail");
                    });
                }
            }
        },
        click_refresh: function () {
            var self = this;

            rpc.query({
                model: "pos.order",
                method: "search_read",
                domain: [["user_id", "=", self.pos.user.id]],
            }).then(function (orders) {
                self.pos.db.all_order = [];
                self.pos.db.order_by_id = {};
                if (orders) {
                    rpc.query({
                        model: "pos.order.line",
                        method: "search_read",
                    }).then(function (order_line) {
                        self.pos.db.order_line_by_id = {};
                        if (order_line) {
                            self.pos.db.all_orders_line(order_line);
                            self.pos.db.all_orders(orders);
                            self.show();
                        }
                    });
                }
            });
        },
        click_back: function () {
            this.gui.back();
        },
        render_list: function (orders) {
            var self = this;
            var contents = self.$el[0].querySelector(".order-list-contents");
            contents.innerHTML = "";
            for (var i = 0, len = Math.min(orders.length, 1000); i < len; i++) {
                var order = self.pos.db.order_by_uid[orders[i].sh_uid];
                if (order) {
                    order.amount_total = parseFloat(order.amount_total).toFixed(2);
                    if (order.state != "cancel") {
                        var assigned_config_name = "";
                        if (order.assigned_config) {
                            _.each(order.assigned_config, function (each_assigned_config) {
                                if (self.pos.db.config_by_id[each_assigned_config] && self.pos.db.config_by_id[each_assigned_config].sh_nick_name) {
                                    assigned_config_name = assigned_config_name + self.pos.db.config_by_id[each_assigned_config].sh_nick_name + ",";
                                } else if (self.pos.db.config_by_id[each_assigned_config] && self.pos.db.config_by_id[each_assigned_config].name) {
                                    assigned_config_name = assigned_config_name + self.pos.db.config_by_id[each_assigned_config].name + ",";
                                }
                            });
                        }
                        order["assigned_config_name"] = assigned_config_name;

                        var clientline_html = QWeb.render("OrderlistLine", { widget: self, each_order: order });
                        var clientline = document.createElement("tbody");
                        clientline.innerHTML = clientline_html;
                        clientline = clientline.childNodes[1];
                        contents.appendChild(clientline);

                        var clientline_html = QWeb.render("OrderDetail", { widget: self, order: order });
                        var clientline = document.createElement("tbody");
                        clientline.innerHTML = clientline_html;
                        clientline = clientline.childNodes[1];
                        contents.appendChild(clientline);
                    }
                }
            }
        },
    });
    gui.define_screen({
        name: "order_screen",
        widget: OrderScreenWidget,
    });
    
    screens.PaymentScreenWidget.include({
    	finalize_validation: function () {
            this._super();
            this.pos.order_length = this.pos.order_length + 1;
        },
    });
    return {
        OrderScreenWidget: OrderScreenWidget,
        OrderHistoryButton: OrderHistoryButton,
    };
});
