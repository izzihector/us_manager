odoo.define('pos_retail.big_data', function (require) {
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var _t = core._t;
    var db = require('point_of_sale.DB');
    var rpc = require('pos.rpc');
    var indexed_db = require('pos_retail.indexedDB');
    var screens = require('point_of_sale.screens');
    var chrome = require('point_of_sale.chrome');
    var QWeb = core.qweb;

    var indexedDB = window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB || window.shimIndexedDB;

    if (!indexedDB) {
        window.alert("Your browser doesn't support a stable version of IndexedDB.")
    }

    var sync_backend_status = chrome.StatusWidget.extend({
        template: 'sync_backend_status',
        start: function () {
            var self = this;
            this.pos.bind('change:sync_backend', function (pos, sync_backend) {
                self.set_status(sync_backend.state, sync_backend.pending);
            });
            this.$el.click(function () {
                self.pos.gui.show_popup('confirm', {
                    title: 'Keep Waiting',
                    body: 'POS auto sync backend, please waiting minutes',
                });
                var status = new $.Deferred();
                self.pos._auto_refresh_products();
                self.pos._auto_refresh_partners();
                self.pos.get_modifiers_backend_all_models().then(function (total_sync) {
                    self.pos.set('sync_backend', {state: 'connected', pending: 0});
                    self.pos.gui.show_popup('confirm', {
                        title: 'Great Job !',
                        body: 'Have ' + total_sync + ' news from backend, database pos now updated succeed',
                    });
                    status.resolve()
                }, function (err) {
                    self.pos.query_backend_fail(err);
                    status.reject(err)
                });
                return status;
            });
        },
    });

    chrome.Chrome.include({
        build_widgets: function () {
            this.widgets.push(
                {
                    'name': 'sync_backend_status',
                    'widget': sync_backend_status,
                    'append': '.pos-rightheader'
                }
            );
            this._super();
        }
    });

    screens.ProductScreenWidget.include({
        do_update_products_cache: function (product_datas) {
            console.log('do_update_products_cache');
            var self = this;
            this.pos.db.add_products(_.map(product_datas, function (product) {
                var using_company_currency = self.pos.config.currency_id[0] === self.pos.company.currency_id[0];
                if (self.pos.company_currency) {
                    var conversion_rate = self.pos.currency.rate / self.pos.company_currency.rate;
                } else {
                    var conversion_rate = 1;
                }
                if (!using_company_currency) {
                    product['lst_price'] = round_pr(product.lst_price * conversion_rate, self.pos.currency.rounding);
                }
                if (self.pos.db.stock_datas && self.pos.db.stock_datas[product['id']]) {
                    product['qty_available'] = self.pos.db.stock_datas[product['id']];
                }
                product['categ'] = _.findWhere(self.pos.product_categories, {'id': product['categ_id'][0]});
                product = new models.Product({}, product);
                var current_pricelist = self.product_list_widget._get_active_pricelist();
                var cache_key = self.product_list_widget.calculate_cache_key(product, current_pricelist);
                self.product_list_widget.product_cache.cache_node(cache_key, null);
                var product_node = self.product_list_widget.render_product(product);
                product_node.addEventListener('click', self.product_list_widget.click_product_handler);
                var contents = document.querySelector(".product-list " + "[data-product-id='" + product['id'] + "']");
                if (contents) {
                    contents.replaceWith(product_node)
                }
                document.querySelector('.product-list').appendChild(product_node);
                return product;
            }));
        },
    });

    screens.ClientListScreenWidget.include({
        do_update_partners_cache: function (partners) {
            console.log('do_update_partners_cache');
            var contents = this.$el[0].querySelector('.client-list-contents');
            var client_selected = this.new_client;
            if (client_selected) {
                this.display_client_details('hide', client_selected);
                this.new_client = null;
                this.toggle_save_button();
            }
            for (var i = 0; i < partners.length; i++) {
                var partner = partners[i];
                var clientline_html = QWeb.render('ClientLine', {widget: this, partner: partners[i]});
                clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
                this.partner_cache.cache_node(partner.id, clientline);
                contents.appendChild(clientline);
            }
        }
    });

    models.load_models([
        {
            label: 'saving master datas field and domain to Parameter',
            loaded: function (self) {
                return new Promise(function (resolve, reject) {
                    var models = {};
                    for (var number in self.model_lock) {
                        var model = self.model_lock[number];
                        models[model['model']] = {
                            fields: model['fields'] || [],
                            domain: model['domain'] || [],
                            context: model['context'] || [],
                        };
                        if (model['model'] == 'res.partner') {
                            models[model['model']]['domain'] = []
                        }
                    }
                    rpc.query({
                        model: 'pos.cache.database',
                        method: 'save_parameter_models_load',
                        args: [[], models]
                    }).then(function (reinstall) {
                        if (reinstall) {
                            self.remove_indexed_db();
                            self.reload_pos();
                        }
                        resolve(reinstall);
                    }, function (err) {
                        reject(err);
                    });
                })
            },
        }
    ], {
        before: 'res.company'
    });
    models.load_models([
        {
            label: 'Reload Session',
            condition: function (self) {
                return self.pos_session.required_reinstall_cache;
            },
            loaded: function (self) {
                return new Promise(function (resolve, reject) {
                    rpc.query({
                        model: 'pos.session',
                        method: 'update_required_reinstall_cache',
                        args: [[self.pos_session.id]]
                    }).then(function (state) {
                        self.remove_indexed_db();
                        self.reload_pos();
                        resolve(state);
                    }, function (err) {
                        self.remove_indexed_db();
                        self.reload_pos();
                        reject(err)
                    })
                });
            },
        },
    ], {
        after: 'pos.config'
    });

    models.load_models([
        {
            label: 'Products',
            loaded: function (self) {
                return self.indexed_db.get_datas(self, 'product.product', self.session.model_ids['product.product']['max_id'] / 100000 + 1)
            }
        },
        {
            label: 'Installing Products',
            condition: function (self) {
                return self.total_products == 0;
            },
            loaded: function (self) {
                return self.api_install_datas('product.product')
            }
        },
        {
            label: 'Partners',
            loaded: function (self) {
                return self.indexed_db.get_datas(self, 'res.partner', self.session.model_ids['res.partner']['max_id'] / 100000 + 1)
            }
        },
        {
            label: 'Installing Partners',
            condition: function (self) {
                return self.total_clients == 0;
            },
            loaded: function (self) {
                return self.api_install_datas('res.partner')
            }
        }
    ]);

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        set_client: function (client) {
            if (client && client['id'] && this.pos.deleted['res.partner'] && this.pos.deleted['res.partner'].indexOf(client['id']) != -1) {
                client = null;
                return this.pos.gui.show_popup('confirm', {
                    title: 'Blocked action',
                    body: 'This client deleted from backend'
                })
            }
            _super_Order.set_client.apply(this, arguments);
        },
    });
    var _super_PosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        // TODO: sync backend
        sync_with_backend: function (model, datas, dont_check_write_time) {
            var self = this;
            if (datas.length == 0) {
                console.warn('Data sync is old times. Reject:' + model);
                return false;
            }
            this.db.set_last_write_date_by_model(model, datas);
            if (model == 'res.partner') {
                var partner_datas = _.filter(datas, function (partner) {
                    return !partner.deleted || partner.deleted != true
                });
                this.db.add_partners(partner_datas);
                if (this.gui.screen_instances && this.gui.screen_instances['clientlist']) {
                    this.gui.screen_instances["clientlist"].do_update_partners_cache(partner_datas);
                }
            }
            if (model == 'product.product') {
                var product_datas = _.filter(datas, function (product) {
                    return !product.deleted || product.deleted != true
                });
                if (product_datas.length) {
                    if (this.gui.screen_instances && this.gui.screen_instances['products']) {
                        this.gui.screen_instances["products"].do_update_products_cache(product_datas);
                    }
                }
            }
            for (var i = 0; i < datas.length; i++) {
                var data = datas[i];
                if (!data['deleted'] || data['deleted'] == false) {
                    self.indexed_db.write(model, [data]);
                } else {
                    self.indexed_db.unlink(model, data);
                    if (model == 'res.partner') {
                        this.remove_partner_deleted_outof_orders(data['id'])
                    }
                }
            }
        },
        remove_partner_deleted_outof_orders: function (partner_id) {
            var orders = this.get('orders').models;
            var order = orders.find(function (order) {
                var client = order.get_client();
                if (client && client['id'] == partner_id) {
                    return true;
                }
            });
            if (order) {
                order.set_client(null)
            }
            return order;
        },
        // TODO : -------- end sync -------------
        _auto_refresh_products: function () {
            var self = this;
            var product_model = this.get_model('product.product');
            if (!product_model) {
                return
            }
            rpc.query({
                model: 'product.product',
                method: 'search_read',
                domain: [['id', '<=', this.session.model_ids['product.product']['max_id']]],
                fields: product_model.fields,
            }, {
                shadow: true,
                timeout: 65000
            }).then(function (results) {
                self.indexed_db.write('product.product', results);
            });
        },
        _auto_refresh_partners: function () {
            var self = this;
            var product_model = this.get_model('res.partner');
            if (!product_model) {
                return
            }
            rpc.query({
                model: 'res.partner',
                method: 'search_read',
                domain: [['id', '<=', this.session.model_ids['res.partner']['max_id']]],
                fields: product_model.fields,
            }, {
                shadow: true,
                timeout: 65000
            }).then(function (results) {
                self.indexed_db.write('res.partner', results);
            });
        },
        query_backend_fail: function (error) {
            if (error && error.message && error.message.code && error.message.code == 200) {
                return this.gui.show_popup('error', {
                    title: error.message.code,
                    body: error.message.data.message,
                })
            }
            if (error && error.message && error.message.code && error.message.code == -32098) {
                return this.gui.show_popup('error', {
                    title: error.message.code,
                    body: 'Your Odoo Server Offline',
                })
            } else {
                return this.gui.show_popup('error', {
                    title: 'Error',
                    body: 'Odoo offline mode or backend codes have issues. Please contact your admin system',
                })
            }
        },
        get_model: function (_name) {
            var _index = this.models.map(function (e) {
                return e.model;
            }).indexOf(_name);
            if (_index > -1) {
                return this.models[_index];
            }
            return false;
        },
        sort_by: function (field, reverse, primer) {
            var key = primer ?
                function (x) {
                    return primer(x[field])
                } :
                function (x) {
                    return x[field]
                };
            reverse = !reverse ? 1 : -1;
            return function (a, b) {
                return a = key(a), b = key(b), reverse * ((a > b) - (b > a));
            }
        },
        initialize: function (session, attributes) {
            this.deleted = {};
            this.total_products = 0;
            this.total_clients = 0;
            this.load_datas_cache = false;
            this.max_load = 9999;
            this.next_load = 10000;
            this.first_load = 10000;
            this.session = session;
            this.sequence = 0;
            this.model_lock = [];
            this.model_unlock = [];
            this.model_ids = session['model_ids'];
            this.company_currency_id = session['company_currency_id'];
            for (var i = 0; i < this.models.length; i++) {
                var this_model = this.models[i];
                if (this_model.model && this.model_ids[this_model.model]) {
                    this_model['max_id'] = this.model_ids[this_model.model]['max_id'];
                    this_model['min_id'] = this.model_ids[this_model.model]['min_id'];
                    this.model_lock = _.filter(this.model_lock, function (model_check) {
                        return model_check['model'] != this_model.model;
                    });
                    this.model_lock.push(this_model);

                } else {
                    this.model_unlock.push(this_model);
                }
            }
            _super_PosModel.initialize.call(this, session, attributes);
            var pos_session_object = this.get_model('pos.session');
            if (pos_session_object) {
                pos_session_object.fields.push('required_reinstall_cache')
            }
            this.indexed_db = new indexed_db(this);
            var product_model = this.get_model('product.product');
            this.product_model = product_model;
            product_model.fields.push(
                'write_date',
            );
            var product_index = _.findIndex(this.models, function (model) {
                return model.model === "product.product";
            });
            if (product_index !== -1) {
                this.models.splice(product_index, 1);
            }
            var partner_index = _.findIndex(this.models, function (model) {
                return model.model === "res.partner";
            });
            if (partner_index !== -1) {
                this.models.splice(partner_index, 1);
            }
        },
        _get_active_pricelist: function () {
            var current_order = this.get_order();
            var default_pricelist = this.default_pricelist;
            if (current_order && current_order.pricelist) {
                var pricelist = _.find(this.pricelists, function (pricelist_check) {
                    return pricelist_check['id'] == current_order.pricelist['id']
                });
                return pricelist;
            } else {
                if (default_pricelist) {
                    var pricelist = _.find(this.pricelists, function (pricelist_check) {
                        return pricelist_check['id'] == default_pricelist['id']
                    });
                    return pricelist
                } else {
                    return null
                }
            }
        },
        get_process_time: function (min, max) {
            if (min > max) {
                return 1
            } else {
                return (min / max).toFixed(1)
            }
        },
        get_count_records_modifires: function () {
            var self = this;
            return new Promise(function (resolve, reject) {
                rpc.query({
                    model: 'pos.cache.database',
                    method: 'get_count_modifiers_backend_all_models',
                    args: [[], self.db.write_date_by_model, self.config.id]
                }).then(function (count) {
                    if (count > 0) {
                        self.set('sync_backend', {state: 'connecting', pending: count});
                        self.get_modifiers_backend_all_models();
                    } else {
                        self.set('sync_backend', {state: 'connected', pending: 0});
                    }
                    resolve()
                }, function (err) {
                    console.error(err);
                    reject()
                })
            })
        },
        get_modifiers_backend: function (model) { // TODO: when pos session online, if pos session have notification from backend, we get datas modifires and sync to pos
            var self = this;
            return new Promise(function (resolve, reject) {
                if (self.db.write_date_by_model[model]) {
                    var args = [[], self.db.write_date_by_model[model], model];
                    return rpc.query({
                        model: 'pos.cache.database',
                        method: 'get_modifiers_backend',
                        args: args
                    }).then(function (results) {
                        if (results.length) {
                            var model = results[0]['model'];
                            self.sync_with_backend(model, results);
                        }
                        self.set('sync_backend', {state: 'connected', pending: 0});
                        resolve()
                    }, function (error) {
                        if (error.code == -32098) {
                            self.gui.show_popup('confirm', {
                                title: 'Warning',
                                body: 'Odoo server offline mode, or your internet connection have problem'
                            });
                        } else {
                            self.gui.show_popup('confirm', {
                                title: 'Warning',
                                body: 'Odoo server busy busy, sync will callback 1 minutes'
                            });
                        }
                        reject()
                    })
                } else {
                    resolve()
                }
            });
        },
        get_modifiers_backend_all_models: function () { // TODO: get all modifiers of all models from backend and sync to pos
            var self = this;
            return new Promise(function (resolve, reject) {
                var model_values = self.db.write_date_by_model;
                var args = [[], model_values, self.config.id];
                rpc.query({
                    model: 'pos.cache.database',
                    method: 'get_modifiers_backend_all_models',
                    args: args
                }).then(function (results) {
                    var total = 0;
                    for (var model in results) {
                        var vals = results[model];
                        if (vals && vals.length) {
                            self.sync_with_backend(model, vals);
                            total += vals.length;
                        }
                    }
                    resolve(total);
                }, function (err) {
                    reject();
                });
            });
        },
        save_results: function (model, results) { // TODO: When loaded all results from indexed DB, we restore back to POS Odoo
            if (model == 'product.product') {
                this.total_products += results.length;
                var process_time = this.get_process_time(this.total_products, this.model_ids[model]['count']) * 100;
                this.chrome.loading_message(_t('Products Installed ' + process_time.toFixed(0) + ' %'), process_time / 100);
                console.log('-> Total Products Restored ' + this.total_products);
                console.log('-> Loaded ' + process_time + ' %');
            }
            if (model == 'res.partner') {
                this.total_clients += results.length;
                var process_time = this.get_process_time(this.total_clients, this.model_ids[model]['count']) * 100;
                this.chrome.loading_message(_t('Partners Installed ' + process_time.toFixed(0) + ' %'), process_time / 100);
                console.log('-> Total Clients Restored ' + this.total_clients);
                console.log('-> Loaded ' + process_time + ' %');
            }
            var object = _.find(this.model_lock, function (object_loaded) {
                return object_loaded.model == model;
            });
            if (object) {
                object.loaded(this, results, {})
            } else {
                console.error('Could not find model: ' + model + ' for restoring datas');
                return false;
            }
            this.load_datas_cache = true;
            this.db.set_last_write_date_by_model(model, results);
        },
        reload_pos: function () {
            location.reload();
        },
        api_install_datas: function (model_name) {
            var self = this;
            var model = _.find(this.model_lock, function (model) {
                return model.model == model_name;
            });
            var installed = new Promise(function (resolve, reject) {
                function installing_data(model_name, min_id, max_id) {
                    self.chrome.loading_message(_t('Installing Model' + model_name + ' from ID: ' + min_id + ' to ID: ' + max_id));
                    var domain = [['id', '>=', min_id], ['id', '<', max_id]];
                    var context = {};
                    if (model['model'] == 'product.product') {
                        domain.push(['available_in_pos', '=', true]);
                        var price_id = null;
                        if (self.pricelist) {
                            price_id = self.pricelist.id;
                        }
                        var stock_location_id = null;
                        if (self.config.stock_location_id) {
                            stock_location_id = self.config.stock_location_id[0]
                        }
                        context['location'] = stock_location_id;
                        context['pricelist'] = price_id;
                        context['display_default_code'] = false;
                    }
                    if (min_id == 0) {
                        max_id = self.max_load;
                    }
                    rpc.query({
                        model: 'pos.cache.database',
                        method: 'install_data',
                        args: [null, model_name, min_id, max_id]
                    }).then(function (results) {
                        min_id += self.next_load;
                        if (typeof results == "string") {
                            results = JSON.parse(results);
                        }
                        if (results.length > 0) {
                            max_id += self.next_load;
                            installing_data(model_name, min_id, max_id);
                            self.indexed_db.write(model_name, results);
                            self.save_results(model_name, results);
                        } else {
                            if (max_id < model['max_id']) {
                                max_id += self.next_load;
                                installing_data(model_name, min_id, max_id);
                            } else {
                                resolve()
                            }
                        }
                    }, function (error) {
                        console.error(error.message.message);
                        var db = self.session.db;
                        for (var i = 0; i <= 100; i++) {
                            indexedDB.deleteDatabase(db + '_' + i);
                        }
                        self.reload_pos();
                        reject()
                    })
                }

                installing_data(model_name, 0, self.first_load);
            });
            return installed;
        },
        remove_indexed_db: function () {
            var dbName = this.session.db;
            for (var i = 0; i <= 50; i++) {
                indexedDB.deleteDatabase(dbName + '_' + i);
            }
            console.log('remove_indexed_db succeed !')
        },
        load_server_data: function () {
            var self = this;
            return _super_PosModel.load_server_data.apply(this, arguments).then(function () {
                self.models = self.models.concat(self.model_lock);
                if (self.config.big_datas_sync_backend) {
                    setInterval(function () {
                        self.get_modifiers_backend_all_models()
                    }, 2500);
                }
                return self.get_modifiers_backend_all_models()
            });
        },
    });
    db.include({
        init: function (options) {
            this._super(options);
            this.write_date_by_model = {};
        },
        set_last_write_date_by_model: function (model, results) {
            for (var i = 0; i < results.length; i++) {
                var line = results[i];
                if (!this.write_date_by_model[model]) {
                    this.write_date_by_model[model] = line.write_date;
                    continue;
                }
                if (this.write_date_by_model[model] != line.write_date && new Date(this.write_date_by_model[model]).getTime() < new Date(line.write_date).getTime()) {
                    this.write_date_by_model[model] = line.write_date;
                }
            }
        },
    })
});
