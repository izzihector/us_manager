odoo.define("sh_pos_order_return_exchange.pos", function (require) {
    "use strict";


    var models = require("point_of_sale.models");
    var DB = require("point_of_sale.DB");
    var PopupWidget = require("point_of_sale.popups");
    var gui = require("point_of_sale.gui");
    var screens = require("point_of_sale.screens");
    var core = require("web.core");
    var QWeb = core.qweb;
    var rpc = require("web.rpc");
    var session = require("web.session");
    var field_utils = require("web.field_utils");

    // hs:begin
    var tampungan_minus = 0;
    var is_exchange_active = false;
    // hs:end

    models.load_fields("product.product", ["sh_product_non_returnable", "sh_product_non_exchangeable"]);

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

    models.load_models({
        label: 'Loading POS Order',
        loaded: function (self) {
            if (self && self.config && self.config.sh_mode && self.config.sh_mode == 'offline_mode') {

                rpc.query({
                    model: "pos.order",
                    method: "search_return_order_length",
                    args: [self.config]

                }).then(function (orders) {

                    if (orders) {
                        if (orders['order']) {
                            _.each(orders['order'], function (each_order) {
                                if (each_order.is_return_order || each_order.is_exchange_order) {
                                    self.db.all_return_order.push(each_order)
                                } else if (!each_order.is_return_order && !each_order.is_exchange_order) {
                                    self.db.all_non_return_order.push(each_order)
                                }
                            });
                            self.order_length = orders['order'].length
                            self.db.all_orders(orders['order']);
                            self.db.all_display_order = orders['order'];
                        }
                        if (orders['order_line']) {
                            self.db.all_orders_line(orders['order_line']);
                        }
                    }
                });


            } if (self && self.config && self.config.sh_mode && self.config.sh_mode == 'online_mode') {

                rpc.query({
                    model: "pos.order",
                    method: "search_read",
                    domain: [['user_id', '=', self.user.id]],

                }).then(function (all_order) {
                    self.order_length = all_order.length
                    self.db.all_display_order = all_order;
                    if (all_order && all_order.length > 0) {
                        self.db.all_orders(all_order);
                        _.each(all_order, function (each_order) {
                            if (each_order.is_return_order || each_order.is_exchange_order) {
                                self.db.all_return_order.push(each_order)
                            } else if (!each_order.is_return_order && !each_order.is_exchange_order) {
                                self.db.all_non_return_order.push(each_order)
                            }
                        });
                    }
                });
            }
        }
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
            this.all_display_order = [];
            this.all_order_temp = [];
            this.all_return_order = [];
            this.all_non_return_order = [];
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
                    this.order_by_id[each_order.id] = each_order;
                    this.order_by_uid[each_order.sh_uid] = each_order;
                    this.all_order_temp.push(each_order);
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
        initialize: function (session, attributes) {
            self.is_return = false;
            self.is_exchange = false;
            _super_posmodel.initialize.apply(this, arguments);
        },

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
                    //own
                    self.formatted_validation_date = field_utils.format.datetime(moment(self.get_order().validation_date), {}, { timezone: false });

                    var sh_line_id = [];
                    _.each(orders, function (each_order) {
                        if (!self.db.order_by_uid[each_order.data.sh_uid]) {
                            var new_line = [];
                            if (each_order["data"]["amount_paid"] >= parseInt(each_order["data"]["amount_total"])) {
                                each_order["data"]["state"] = "paid";
                            } else {
                                each_order["data"]["state"] = "draft";
                            }
                            each_order["data"]["date_order"] = self.formatted_validation_date;
                            each_order["data"]["pos_reference"] = each_order.data.name;
                            self.db.all_order.push(each_order.data);

                            self.db.all_display_order.push(each_order.data);
                            self.db.order_by_uid[each_order.data.sh_uid] = each_order.data;
                            if (each_order && each_order.data && each_order.data.old_sh_uid && self.db.order_by_uid[each_order.data.old_sh_uid]) {
                                if (self.db.order_by_uid[each_order.data.old_sh_uid]["old_pos_reference"]) {
                                    self.db.order_by_uid[each_order.data.old_sh_uid]["old_pos_reference"] = self.db.order_by_uid[each_order.data.old_sh_uid]["old_pos_reference"] + " , " + each_order.data.name;
                                } else {
                                    self.db.order_by_uid[each_order.data.old_sh_uid]["old_pos_reference"] = each_order.data.name;
                                }
                            }
                            _.each(each_order.data.lines, function (each_line) {
                                if (each_line[2] && each_line[2].sh_line_id) {
                                    if (each_order.data.is_return_order) {
                                        if (each_line[2].old_line_id) {
                                            if (self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"]) {
                                                each_line[2]["sh_return_qty"] = 0;
                                                self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] + each_line[2].qty * -1;
                                            } else {
                                                each_line[2]["sh_return_qty"] = 0;
                                                self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = each_line[2].qty * -1;
                                            }
                                        } else {
                                            each_line[2]["sh_return_qty"] = 0;
                                        }
                                    } else if (each_order.data.is_exchange_order) {
                                        if (each_line[2].old_line_id) {
                                            if (self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"]) {
                                                each_line[2]["sh_return_qty"] = 0;
                                                self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] + each_line[2].qty * -1;
                                            } else {
                                                each_line[2]["sh_return_qty"] = 0;

                                                self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = each_line[2].qty * -1;
                                            }
                                        } else {
                                            each_line[2]["sh_return_qty"] = 0;
                                        }
                                    } else {
                                        each_line[2]["sh_return_qty"] = 0;
                                    }
                                    self.db.order_line_by_uid[each_line[2].sh_line_id] = each_line[2];
                                    sh_line_id.push(each_line[2].sh_line_id);
                                }
                            });
                            each_order.data["sh_line_id"] = sh_line_id;
                            self.db.order_by_uid[each_order.data.sh_uid] = each_order.data;
                        }

                        if (each_order.data.old_sh_uid) {
                            var old_order = self.db.order_by_uid[each_order.data.old_sh_uid];

                            var flag = true;
                            if (old_order && old_order.sh_line_id) {
                                _.each(old_order.sh_line_id, function (each_old_line) {
                                    var old_order_line = self.db.order_line_by_uid[each_old_line];
                                    if (flag) {
                                        if (old_order_line.qty > old_order_line.sh_return_qty) {
                                            flag = false;
                                        }
                                    }
                                });
                                if (flag) {
                                    old_order["return_status"] = "fully_return";
                                } else {
                                    old_order["return_status"] = "partialy_return";
                                }
                            } else if (old_order && old_order.lines) {
                                _.each(old_order.lines, function (each_old_line) {
                                    var old_order_line = self.db.order_line_by_id[each_old_line];
                                    if (old_order_line) {
                                        if (flag) {
                                            if (old_order_line.qty > old_order_line.sh_return_qty) {
                                                flag = false;
                                            }
                                        }
                                    }
                                });
                                if (flag) {
                                    old_order["return_status"] = "fully_return";
                                } else {
                                    old_order["return_status"] = "partialy_return";
                                }
                            }
                        }
                    });
                    //finish

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
                    self.gui.show_sync_error_popup();
                    throw error;
                });
        },
    });

    var _super_orderline = models.Orderline;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            _super_orderline.prototype.initialize.call(this, attr, options);
            this.sequence_number = this.pos.pos_session.sequence_number++;
            this.sh_line_id = this.generate_sh_line_unique_id();
        },
        set_line_id: function (line_id) {
            this.line_id = line_id;
        },
        set_old_line_id: function (old_line_id) {
            this.old_line_id = old_line_id;
        },
        export_as_JSON: function () {
            var json = _super_orderline.prototype.export_as_JSON.apply(this, arguments);
            json.line_id = this.line_id;
            json.old_line_id = this.old_line_id;
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
            return "sh" + this.sequence_number;
        },
        init_from_JSON: function (json) {
            _super_orderline.prototype.init_from_JSON.apply(this, arguments);
            this.line_id = json.line_id;
            if (json.pos_session_id !== this.pos.pos_session.id) {
                this.sequence_number = this.pos.pos_session.sequence_number++;
            } else {
                this.sequence_number = json.sequence_number;
                this.pos.pos_session.sequence_number = Math.max(this.sequence_number + 1, this.pos.pos_session.sequence_number);
            }
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function () {
            var self = this;
            self.return_order = false;
            self.old_pos_reference = false;
            self.old_sh_uid = false;
            _super_order.initialize.apply(this, arguments);
            self.sequence_number = self.pos.pos_session.sequence_number++;
            self.sh_uid = self.generate_sh_unique_id();
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
            return this.sequence_number;
        },
        is_return_order: function (is_return_order) {
            this.return_order = is_return_order;
            return this.return_order;
        },
        is_exchange_order: function (is_exchange_order) {
            this.exchange_order = is_exchange_order;
            return this.is_exchange_order;
        },
        set_old_pos_reference: function (old_pos_reference) {
            this.old_pos_reference = old_pos_reference;
        },
        get_old_pos_reference: function (old_pos_reference) {
            return this.old_pos_reference;
        },
        set_old_sh_uid: function (old_sh_uid) {
            this.old_sh_uid = old_sh_uid;
        },
        get_old_sh_uid: function () {
            return this.old_sh_uid;
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.is_return_order = this.return_order || null;
            json.is_exchange_order = this.exchange_order || null;
            json.old_pos_reference = this.old_pos_reference || null;
            json.old_sh_uid = this.old_sh_uid || null;
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
        export_for_printing: function () {
            var self = this;
            var orders = _super_order.export_for_printing.call(this);
            var new_val = {
                is_return_order: this.return_order || false,
                is_exchange_order: this.exchange_order || false,
                old_pos_reference: this.old_pos_reference || false,
            };
            $.extend(orders, new_val);
            return orders;
        },
        add_product: function (product, options) {
            // hs:begin
            this._super();
            console.log('is_exchange_active', is_exchange_active);
            console.log(product);
            let prlObj = false;
            product?.pos?.pricelists[0]?.items?.map(val => {
                if (prlObj == false) {
                    if (val.product_id[0] == product.id) {
                        prlObj = val;
                    }
                }
            })

            let price = prlObj.fixed_price || 0
            let stock = product.bi_on_hand || 0

            if (is_exchange_active == true) {
                if (options === undefined) {
                    if (!isNaN(tampungan_minus)) {
                        if (tampungan_minus < 0) {
                            tampungan_minus += price;

                            let aa = tampungan_minus
                            if (aa > 0) {
                                options = {
                                    ...options,
                                    'price': aa,
                                }
                            } else {
                                options = {
                                    ...options,
                                    'price': 0,
                                }
                            }
                        }
                    }
                } else {
                    if (options.quantity > 0) {
                        if (!isNaN(tampungan_minus)) {
                            if (tampungan_minus < 0) {
                                tampungan_minus += (price * options.quantity);
                            }
                        }
                    }
                }
            } else {
                if (product?.type == 'product') {
                    if (stock < 1) {
                        this.pos.gui.show_popup("error", {
                            'title': "Deny Order",
                            'body': `Deny Order(${product.display_name}) is out of stock`
                        });
                        return false;
                    }
        
                    if (price < 1) {
                        this.pos.gui.show_popup("error", {
                            'title': "Deny Order",
                            'body': `Deny Order(${product.display_name}) is zero price`
                        });
                        return false;
                    }
                }
            }
            // hs:end

            var order = this.pos.get_order();
            _super_order.add_product.call(this, product, options);
            if (options !== undefined) {
                if (options.line_id !== undefined) {
                    order.selected_orderline.set_line_id(options.line_id);
                    order.selected_orderline.set_old_line_id(options.old_line_id);
                }
            }
        },
    });

    screens.PaymentScreenWidget.include({
        show: function (options) {
            var self = this;
            this._super(options);
            if (!self.pos.get_order().return_order) {
                self.$(".cancel").css({ display: "none" });
            }
        },
        renderElement: function () {
            var self = this;
            this._super();
            this.$(".cancel").click(function () {
                if (self.pos.config.is_table_management) {
                    self.pos.get_order().destroy();
                    self.pos.add_new_order();
                } else {
                    self.pos.get_order().destroy();
                }
            });
        },
        finalize_validation: function () {
            // hs:begin
            is_exchange_active = false;
            // hs:end
            console.log('is_exchange_active', is_exchange_active);
            var self = this;
            var order = this.pos.get_order();

            if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) {
                this.pos.proxy.printer.open_cashbox();
            }

            order.initialize_validation_date();
            order.finalized = true;
            if (order.is_to_invoice()) {
                var invoiced = this.pos.push_and_invoice_order(order);

                this.invoicing = true;

                invoiced.catch(this._handleFailedPushForInvoice.bind(this, order, false));

                invoiced.then(function (server_ids) {
                    self.invoicing = false;
                    var post_push_promise = [];
                    post_push_promise = self.post_push_order_resolve(order, server_ids);
                    post_push_promise
                        .then(function () {
                            self.gui.show_screen("receipt");
                        })
                        .catch(function (error) {
                            self.gui.show_screen("receipt");
                            if (error) {
                                self.gui.show_popup("error", {
                                    title: "Error: no internet connection",
                                    body: error,
                                });
                            }
                        });
                });
            } else {
                var ordered = this.pos.push_order(order);
                if (order.wait_for_push_order()) {
                    var server_ids = [];
                    ordered
                        .then(function (ids) {
                            server_ids = ids;
                        })
                        .finally(function () {
                            var post_push_promise = [];
                            post_push_promise = self.post_push_order_resolve(order, server_ids);
                            post_push_promise
                                .then(function () {
                                    if (order.return_order) {
                                        order.is_return_order(true);
                                        if (order.old_pos_reference) {
                                            order.set_old_pos_reference(order.old_pos_reference);
                                            order.set_old_sh_uid(order.old_sh_uid);
                                        }
                                    }
                                    if (order.exchange_order) {
                                        order.is_exchange_order(true);
                                        if (order.old_pos_reference) {
                                            order.set_old_pos_reference(order.old_pos_reference);
                                            order.set_old_sh_uid(order.old_sh_uid);
                                        }
                                    }
                                    self.gui.show_screen("receipt");
                                })
                                .catch(function (error) {
                                    if (order.return_order) {
                                        order.is_return_order(true);
                                        if (order.old_pos_reference) {
                                            order.set_old_pos_reference(order.old_pos_reference);
                                            order.set_old_sh_uid(order.old_sh_uid);
                                        }
                                    }
                                    if (order.exchange_order) {
                                        order.is_exchange_order(true);
                                        if (order.old_pos_reference) {
                                            order.set_old_pos_reference(order.old_pos_reference);
                                            order.set_old_sh_uid(order.old_sh_uid);
                                        }
                                    }
                                    self.gui.show_screen("receipt");
                                    if (error) {
                                        self.gui.show_popup("error", {
                                            title: "Error: no internet connection",
                                            body: error,
                                        });
                                    }
                                });
                        });
                } else {
                    if (order.return_order) {
                        order.is_return_order(true);
                        if (order.old_pos_reference) {
                            order.set_old_pos_reference(order.old_pos_reference);
                            order.set_old_sh_uid(order.old_sh_uid);
                            var order_data = order.export_as_JSON();
                            order_data['pos_reference'] = order_data['name'];
                            self.pos.db.all_return_order.push(order_data)
                        }
                    }
                    if (order.exchange_order) {
                        order.is_exchange_order(true);
                        if (order.old_pos_reference) {
                            order.set_old_pos_reference(order.old_pos_reference);
                            order.set_old_sh_uid(order.old_sh_uid);
                            var order_data = order.export_as_JSON();
                            order_data['pos_reference'] = order_data['name'];
                            self.pos.db.all_return_order.push(order_data)
                        }
                    }
                    if (!order.export_as_JSON().is_return_order && !order.export_as_JSON().is_exchange_order) {
                        var order_data = order.export_as_JSON();
                        order_data['pos_reference'] = order_data['name'];
                        self.pos.db.all_non_return_order.push(order_data)
                    }
                    self.gui.show_screen("receipt");
                }
            }
        },
    });

    var OrderScreenWidget = screens.ScreenWidget.extend({
        template: "OrderScreenWidget",

        show: function (options) {
            var self = this;
            self.return_filter = false;
            $(".sh_pagination").pagination({
                pages: Math.ceil(self.pos.db.all_non_return_order.length / self.pos.config.sh_how_many_order_per_page),
                displayedPages: 1,
                edges: 1,
                cssStyle: "light-theme",
                showPageNumbers: false,
                showNavigator: true,
                onPageClick: function (pageNumber) {

                    try {
                        if (!self.return_filter) {
                            rpc.query({
                                model: "pos.order",
                                method: "search_return_order",
                                args: [self.pos.config, pageNumber]
                            }).then(function (orders) {
                                console.log('orders', orders)

                                self.pos.db.all_order = [];
                                self.pos.db.order_by_id = {};

                                if (orders) {
                                    if (orders['order']) {
                                        self.pos.db.all_orders(orders['order']);
                                    }
                                    if (orders['order_line']) {
                                        self.pos.db.all_orders_line(orders['order_line']);
                                    }
                                }
                                self.all_order = self.pos.db.all_order;

                                self.render_list(self.pos.db.all_order);
                            }).catch(function (reason) {
                                var showFrom = parseInt(self.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1)
                                var showTo = showFrom + parseInt(self.pos.config.sh_how_many_order_per_page)
                                self.pos.db.all_order = self.pos.db.all_non_return_order.slice(showFrom, showTo)
                                self.pos.db.all_display_order = self.pos.db.all_order;
                                self.all_order = self.pos.db.all_order;
                                self.render_list(self.pos.db.all_order);
                            });

                        } else {
                            rpc.query({
                                model: "pos.order",
                                method: "search_return_exchange_order",
                                args: [self.pos.config, pageNumber + 1]
                            }).then(function (orders) {
                                if (orders) {
                                    if (orders['order'].length == 0) {
                                    }
                                }
                            }).catch(function (reason) {

                                var showFrom = parseInt(self.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber + 1) - 1)
                                var showTo = showFrom + parseInt(self.pos.config.sh_how_many_order_per_page)
                                var order = self.pos.db.all_return_order.slice(showFrom, showTo)
                                if (order && order.length == 0) {
                                }

                            });

                            rpc.query({
                                model: "pos.order",
                                method: "search_return_exchange_order",
                                args: [self.pos.config, pageNumber]
                            }).then(function (orders) {
                                self.pos.db.all_order = [];
                                self.pos.db.order_by_id = {};

                                if (orders) {
                                    if (orders['order']) {
                                        self.pos.db.all_orders(orders['order']);
                                    }
                                    if (orders['order_line']) {
                                        self.pos.db.all_orders_line(orders['order_line']);
                                    }
                                }
                                self.all_order = self.pos.db.all_order;
                                self.pos.db.all_display_order = self.pos.db.all_order;
                                self.render_list(self.pos.db.all_order);
                            }).catch(function (reason) {

                                var showFrom = parseInt(self.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1)
                                var showTo = showFrom + parseInt(self.pos.config.sh_how_many_order_per_page)
                                self.pos.db.all_order = self.pos.db.all_return_order.slice(showFrom, showTo)
                                self.all_order = self.pos.db.all_order;
                                self.render_list(self.pos.db.all_order);

                            });
                        }

                    } catch (error) {
                    }

                }
            });

            $(".sh_pagination").pagination("selectPage", 1);

            this._super(options);
            self.order_line = [];
            self.test_variable = self.pos.db.all_session;
            if ($(".return").hasClass("highlight")) {
                self.click_return();
            }

            self.render_list(self.pos.db.all_order);

            this.$("#date1").change(function (e) {
                var selected_orders = self.get_orders_by_date(e.target.value);
                if (selected_orders.length > 0) {
                    self.render_list(selected_orders);
                } else {
                    self.render_list([]);
                }
            });
            this.$(".custom_searchbox input").keyup(function (e) {
                if (e.target.value) {
                    var selected_orders = self.get_orders_by_name(e.target.value);
                    if (selected_orders.length > 0) {
                        self.render_list(selected_orders);
                    } else {
                        self.render_list([]);
                    }
                } else {
                    $(".sh_pagination").pagination("selectPage", 1);
                }

            });
        },
        get_orders_by_date: function (date) {
            return _.filter(this.pos.db.all_order, function (template) {
                if (template.date_order && template.date_order.indexOf(date) > -1) {
                    return true;
                } else {
                    return false;
                }
            });
        },
        get_orders_by_name: function (name) {
            var self = this;
            if (self.return_filter) {
                return _.filter(self.pos.db.all_return_order, function (template) {
                    if (template.name.indexOf(name) > -1) {
                        return true;
                    } else if (template["pos_reference"].indexOf(name) > -1) {
                        return true;
                    } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                        return true;
                    } else if (template["date_order"] && template["date_order"].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
            } else {
                return _.filter(self.pos.db.all_non_return_order, function (template) {
                    if (template.name.indexOf(name) > -1) {
                        return true;
                    } else if (template["pos_reference"].indexOf(name) > -1) {
                        return true;
                    } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                        return true;
                    } else if (template["date_order"] && template["date_order"].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
            }
        },
        events: {
            "click .button.back": "click_back",
            "click .button.refresh": "click_refresh",
            "click .order_exchange": "click_order_exchange",
            "click .order_return": "click_order_return",
            "click .return": "click_return",
            "click .sh_order_line": "click_line",
            "click .print_order": "click_order_print",
            "click .re_order_icon": "click_order_reorder",
        },
        click_order_reorder: function (event) {
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
                current_order.add_product(product, {
                    quantity: line_data.qty,
                    price: line_data.price_unit,
                    discount: line_data.discount,
                });
            });
            if (order_data.partner_id && order_data.partner_id[0]) {
                self.pos.get_order().set_client(self.pos.db.get_partner_by_id(order_data.partner_id[0]));
            }
            current_order.assigned_config = order_data.assigned_config;
        },
        click_order_print: function (event) {
            var self = this;
            var order_id = event.currentTarget.closest("tr").attributes[0].value;

            console.log("order_id", order_id)

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
                current_order.add_product(product, {
                    quantity: line_data.qty,
                    price: line_data.price_unit,
                    discount: line_data.discount,
                });
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
        click_back: function () {
            this.gui.back();
        },
        render_list: function (orders) {
            var self = this;
            self.order_no_return = [];
            var contents = self.$el[0].querySelector(".order-list-contents");
            contents.innerHTML = "";
            for (var i = 0, len = Math.min(orders.length, 1000); i < len; i++) {
                // var order = self.pos.db.order_by_uid[orders[i].sh_uid];
                var order = orders[i];
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
                        self.order_no_return.push(order);
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
        click_order_return: function (event) {
            var self = this;
            self.pos.is_return = true;
            self.pos.is_exchange = false;
            var order_line = [];
            var order_id = event.currentTarget.closest("tr").attributes[0].value;
            if (order_id) {
                var order_data = self.pos.db.order_by_uid[order_id];
                if (!order_data) {
                    order_data = self.pos.db.order_by_id[order_id];
                }
                if (order_data && order_data.lines) {
                    _.each(order_data.lines, function (each_order_line) {
                        var line_data = self.pos.db.order_line_by_id[each_order_line];
                        if (!line_data) {
                            line_data = self.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                        }
                        if (line_data) {
                            order_line.push(line_data);
                        }
                    });
                }
            }
            self.pos.gui.show_popup("order_return_popup", { lines: order_line, order: order_id });
        },
        click_order_exchange: function (event) {
            var self = this;
            self.pos.is_return = false;
            self.pos.is_exchange = true;
            var order_line = [];
            var order_id = event.currentTarget.closest("tr").attributes[0].value;
            if (order_id) {
                var order_data = self.pos.db.order_by_uid[order_id];
                if (!order_data) {
                    order_data = self.pos.db.order_by_id[order_id];
                }
                if (order_data && order_data.lines) {
                    _.each(order_data.lines, function (each_order_line) {
                        var line_data = self.pos.db.order_line_by_id[each_order_line];
                        if (!line_data) {
                            line_data = self.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                        }
                        if (line_data) {
                            order_line.push(line_data);
                        }
                    });
                }
            }
            self.pos.gui.show_popup("order_return_popup", { lines: order_line, order: order_id });
        },
        click_return: function (event) {
            var self = this;
            var orders = this.pos.db.all_order;

            var contents = self.$el[0].querySelector(".order-list-contents");
            var return_order = [];
            contents.innerHTML = "";
            if (!$(".return").hasClass("highlight")) {
                self.return_filter = true;
                $(".return").addClass("highlight");
                $('.sh_pagination').pagination('updateItems', Math.ceil(self.pos.db.all_return_order.length / self.pos.config.sh_how_many_order_per_page));
                $('.sh_pagination').pagination('selectPage', 1);
            } else {
                $(".return").removeClass("highlight");
                self.return_filter = false;
                $('.sh_pagination').pagination('updateItems', Math.ceil(self.pos.db.all_non_return_order.length / self.pos.config.sh_how_many_order_per_page));
                $('.sh_pagination').pagination('selectPage', 1);
            }
        },
    });
    gui.define_screen({
        name: "order_screen",
        widget: OrderScreenWidget,
    });

    var OrderReturnPopupWidget = PopupWidget.extend({
        template: "OrderReturnPopupWidget",
        show: function (options) {
            var self = this;
            options = options || {};
            this.order = options.order;
            this.lines = options.lines;
            this.no_return_line_id = [];
            this.return_line = [];
            this._super(options);
            if (self.pos.is_return && !self.pos.config.sh_return_more_qty) {
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
            if (self.pos.is_exchange) {
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
                if (order_data.partner_id[0]) {
                    self.pos.get_order().set_client(self.pos.db.get_partner_by_id(order_data.partner_id[0]));
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
            current_order.old_pos_reference = order_data.pos_reference;
            if (self.pos.is_return) {
                $(".pay").click();
            }
        },
        click_confirm: function () {
            console.log('is_exchange_active', is_exchange_active);
            var self = this;
            _.each($(".return_data_line"), function (each_data_line) {
                if (each_data_line.children[2].children[0].value != "0" && each_data_line.children[2].children[0].value != "") {
                    var order_line = self.pos.db.order_line_by_id[each_data_line.dataset.line_id];
                    if (!order_line) {
                        order_line = self.pos.db.order_line_by_uid[each_data_line.dataset.line_id];
                    }
                    order_line["old_qty"] = order_line["qty"];
                    order_line["qty"] = each_data_line.children[2].children[0].value;

                    // hs:begin
                    tampungan_minus -= (order_line["price_unit"] * order_line["qty"]);
                    console.log('confirm tampungan_minus', tampungan_minus);
                    order_line["price_unit"] = 0;
                    is_exchange_active = true;
                    // hs:end

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
        name: "order_return_popup",
        widget: OrderReturnPopupWidget,
    });
});
