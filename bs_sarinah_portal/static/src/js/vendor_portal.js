// This script override the original file.
  odoo.define('bs_sarinah_portal.vendor_portal', function(require) {
    'use strict';

    var core = require('web.core');
    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');
    var Widget = require('web.Widget');
    var qweb = core.qweb;
    var rpc = require("web.rpc");
    var _t = core._t;
    var session = require('web.session');

    var loadXML = ajax.loadXML('/bs_sarinah_portal/static/src/xml/vendor_portal.xml', qweb);


    $('document').ready(function () {
      // Product Update
      $('.edit_product_vp').off('click').on('click', function (ev) {
        var productID = parseInt(ev.currentTarget.id);
        rpc.query({
          model: 'vendor.product',
          method: 'get_this_product_values',
          args: [[productID]],
          context: session.user_context,
        }).then(function(values) {
          var select = new VendorProductDialogUpdate(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
          return def.then(function (res) {
            location.reload();
          })
        });
      });
      // Product Create
      $('.create_product_vp').off('click').on('click', function (ev) {
        rpc.query({
          model: 'vendor.product',
          method: 'get_this_product_values',
          args: [[]],
          context: session.user_context,
        }).then(function(values) {
          var select = new VendorProductDialogCreate(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
          return def.then(function (res) {
            location.reload();
          })
        });
      });
      // Product Toggle Active
      $('.toggle_active_product_vp').off('click').on('click', function (ev) {
        var productID = parseInt(ev.currentTarget.id);
        var select = new ConfirmToggleDialog(this, {}, {"id": productID});
        var def = $.Deferred();
        select.on('save', this, function (root) {
          def.resolve(root);
        });
        select.open();
        return def.then(function (res) {
          location.reload();
        })
      });
      // Import Products and Prices
      $('.import_prices_vp').off('click').on('click', function (ev) {
        rpc.query({
          model: 'vendor.product',
          method: 'return_import_configs',
          context: session.user_context,
        }).then(function(values) {
          var select = new VendorProductImportPrices(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
        });
      });
      // Import Products and Stocks
      $('.import_stocks_vp').off('click').on('click', function (ev) {
        rpc.query({
          model: 'vendor.product',
          method: 'return_import_configs',
          context: session.user_context,
        }).then(function(values) {
          var select = new VendorProductImportStocks(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
        });
      });
      // Edit price
      $('.edit_price').off('click').on('click', function (ev) {
        var priceID = parseInt(ev.currentTarget.id);
        rpc.query({
          model: 'product.supplierinfo',
          method: 'get_this_price_values',
          args: [[priceID]],
          context: session.user_context,
        }).then(function(values) {
          if(values.state != 'validate') {
            var select = new VendorPriceDialogUpdate(this, {}, values);
            var def = $.Deferred();
            select.on('save', this, function (root) {
              def.resolve(root);
            });
            select.open();
            return def.then(function (res) {
              location.reload();
            })
          }
        });
      });
      // Register new price
      $('.add_price').off('click').on('click', function (ev) {
        var productID = parseInt(ev.currentTarget.id);
        var variantID = parseInt(ev.currentTarget.dataset['variant']);
        rpc.query({
          model: 'product.supplierinfo',
          method: 'get_dialog_options',
          args: [productID],
          context: session.user_context,
        }).then(function(values) {
          values.id = productID;
          values.variant_id = variantID || false;
          var select = new VendorPriceDialogCreate(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
          return def.then(function (res) {
            location.reload();
          })
        });
      });
      // Archive price
      $('.remove_price').off('click').on('click', function (ev) {
        var priceID = parseInt(ev.currentTarget.id);
        rpc.query({
          model: 'product.supplierinfo',
          method: 'get_this_price_values',
          args: [[priceID]],
          context: session.user_context,
        }).then(function(values) {
          if(values.state != 'validate') {
            var select = new ArchivePriceDialog(this, {}, values);
            var def = $.Deferred();
            select.on('save', this, function (root) {
              def.resolve(root);
            });
            select.open();
            return def.then(function (res) {
              location.reload();
            })
          }
        });
      });
      // Edit stock
      $('.edit_quant').off('click').on('click', function (ev) {
        var priceID = parseInt(ev.currentTarget.id);
        rpc.query({
          model: 'vendor.quant',
          method: 'get_this_stock_values',
          args: [[priceID]],
          context: session.user_context,
        }).then(function(values) {
          var select = new VendorQuantDialogUpdate(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
          return def.then(function (res) {
            location.reload();
          })
        });
      });
      // Register new stock
      $('.add_quant').off('click').on('click', function (ev) {
        var productID = parseInt(ev.currentTarget.id);
        rpc.query({
          model: 'vendor.quant',
          method: 'return_options',
          args: [ productID],
          context: session.user_context,
        }).then(function(values) {
          values.id = productID;
          var select = new VendorStockDialogCreate(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
          return def.then(function (res) {
            location.reload();
          })
        });
      });
      // Archive stock
      $('.remove_quant').off('click').on('click', function (ev) {
        var stockID = parseInt(ev.currentTarget.id);
        rpc.query({
          model: 'vendor.quant',
          method: 'get_this_stock_values',
          args: [[stockID]],
          context: session.user_context,
        }).then(function(values) {
          var select = new ArchiveStockDialog(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
          return def.then(function (res) {
            location.reload();
          })
        });
      });
      // Location Update
      $('.edit_location_vp').off('click').on('click', function (ev) {
        var locationID = parseInt(ev.currentTarget.id);
        rpc.query({
          model: 'vendor.location',
          method: 'get_this_location_values',
          args: [[locationID]],
          context: session.user_context,
        }).then(function(values) {
          var select = new VendorLocationDialogUpdate(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
          return def.then(function (res) {
            location.reload();
          })
        });
      });
      // Location Create
      $('.create_location_vp').off('click').on('click', function (ev) {
        var select = new VendorLocationDialogCreate(this, {}, {});
        var def = $.Deferred();
        select.on('save', this, function (root) {
          def.resolve(root);
        });
        select.open();
        return def.then(function (res) {
          location.reload();
        })
      });
      // Location Toggle Active
      $('.toggle_active_location_vp').off('click').on('click', function (ev) {
        var locationID = parseInt(ev.currentTarget.id);
        var select = new ConfirmLocationToggleDialog(this, {}, {"id": locationID});
        var def = $.Deferred();
        select.on('save', this, function (root) {
          def.resolve(root);
        });
        select.open();
        return def.then(function (res) {
          location.reload();
        })
      });
      // Picking Update
      $('.edit_picking_vp').off('click').on('click', function (ev) {
        var portalID = parseInt(ev.currentTarget.id);
        rpc.query({
          model: 'vendor.stock.picking',
          method: 'get_portal_values',
          args: [[portalID]],
          context: session.user_context,
        }).then(function(values) {
          values.id = portalID
          var select = new VendorPickingDialogUpdate(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
          return def.then(function (res) {
            location.reload();
          })
        });
      });
      // Picking Create
      $('.create_picking_vp').off('click').on('click', function (ev) {
        var operation_type = ev.currentTarget.value;
        rpc.query({
          model: 'vendor.stock.picking',
          method: 'get_portal_values',
          args: [[]],
          context: session.user_context,
        }).then(function(values) {
          values.operation_type = operation_type;
          var select = new VendorPickingDialogCreate(this, {}, values);
          var def = $.Deferred();
          select.on('save', this, function (root) {
            def.resolve(root);
          });
          select.open();
          return def.then(function (res) {
            location.reload();
          })
        });
      });
      // Picking Delete
      $('.delete_picking_vp').off('click').on('click', function (ev) {
        var values = {
          'id': parseInt(ev.currentTarget.id),
          'name': ev.currentTarget.dataset['name'],
        }
        var select = new VendorPickingDialogDelete(this, {}, values);
        var def = $.Deferred();
        select.on('delete', this, function (root) {
          def.resolve(root);
        });
        select.open();
        return def.then(function (res) {
          location.reload();
        })
      });
      loadXML.then(() => {
        if($('section#product_images').length) {
          var productImageList = new ProductImageList(this);
          productImageList.replace($('section#product_images'));
        }
        if($('section#product_variants').length) {
          var productVariantList = new ProductVariantList(this);
          productVariantList.replace($('section#product_variants'));

          if($('section#product_attributes').length) {
            var productAttributeList = new ProductAttributeList(this, productVariantList);
            productAttributeList.replace($('section#product_attributes'));
          }

        }
      });
    });

    var VendorProductDialogUpdate = Dialog.extend({
      template: 'vendor_portal_management.vendor_product_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate dialog form with default values
        if (values.partner_consignment_margin) {this.partner_consignment_margin = values.partner_consignment_margin}
        if (values.product_margin) {this.product_margin = values.product_margin}
        else {this.product_margin = ""};
        if (values.product_category_id) {this.product_category_id = values.product_category_id}
        else {this.product_category_id = ""};
        if (values.product_category_ids) {this.product_category_ids = values.product_category_ids}
        else {this.product_category_ids = []};
        if (values.product_manufacture_code) {this.product_manufacture_code = values.product_manufacture_code}
        else {this.product_manufacture_code = ""};
        if (values.product_name) {this.product_name = values.product_name}
        else {this.product_name = ""};
        if (values.product_brand_id) {this.product_brand_id = values.product_brand_id}
        else {this.product_brand_id = ""};
        if (values.product_brand_ids) {this.product_brand_ids = values.product_brand_ids}
        else {this.product_brand_ids = []};
        if (values.product_uom_id) {this.product_uom_id = values.product_uom_id}
        else {this.product_uom_id = ""};
        if (values.product_uom_ids) {this.product_uom_ids = values.product_uom_ids}
        else {this.product_uom_ids = []};
        if (values.product_minimum_quantity) {this.product_minimum_quantity = values.product_minimum_quantity}
        else {this.product_minimum_quantity = 0};
        if (values.description) {this.description = values.description}
        else {this.description = ""};
        if (values.product_brand_margin_ids) {this.product_brand_margin_ids = values.product_brand_margin_ids}
        else {this.product_brand_margin_ids = []};
        this.vendor_product_id = values.id;
        this._super(parent, _.extend({}, {
          title: _t("Product Update"),
          buttons: [
            {text: options.save_text || _t("Update"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.product_name = this.$el.find('#product_name')[0].value;
        vals.product_manufacture_code = this.$el.find('#product_manufacture_code')[0].value;
        vals.product_category_id = parseInt(this.$el.find('#product_category_id')[0].value);
        vals.product_brand_id = parseInt(this.$el.find('#product_brand_id')[0].value);
        vals.product_uom_id = parseInt(this.$el.find('#product_uom_id')[0].value);
        vals.minimum_quantity = parseInt(this.$el.find('#product_minimum_quantity')[0].value);
        vals.description = this.$el.find('#description')[0].value;
        vals.success = _t("The product has been successfully updated");
        return vals
      },
      renderElement: function() {
        this._super()
        this.$('#product_category_id').off('change').on('change', this.update_product_margin.bind(this));
        this.$('#product_brand_id').off('change').on('change', this.update_product_margin.bind(this));
        this.$el.find("select").select2();
      },
      update_product_margin: function () {
        var self = this;
        $('#product_margin').val('');
        if (self.partner_consignment_margin) {
          $('#product_margin').val(self.partner_consignment_margin + '%');
        }

        var margin_id = self.product_brand_ids.filter(margin => {
          var product_brand_id = parseInt(self.$el.find('#product_brand_id')[0].value);
          return margin.id == product_brand_id && margin.margin > 0
        });
        if (margin_id.length) {
          $('#product_margin').val(margin_id[0].margin + '%');
        }

        var margin_id = self.product_brand_margin_ids.filter(margin => {
          var product_category_id = parseInt(self.$el.find('#product_category_id')[0].value);
          var product_brand_id = parseInt(self.$el.find('#product_brand_id')[0].value);
          var category_true = margin.category_id == product_category_id
          var brand_true = margin.brand_id == product_brand_id
          return category_true && brand_true && margin.margin > 0
        });
        if (margin_id.length) {
          $('#product_margin').val(margin_id[0].margin + '%');
        }
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'vendor.product',
          method: 'write',
          args: [[this.vendor_product_id], values],
          context: session.user_context,
        }).then(function(result) {
          self.destroyAction = "save";
          self.close();
          return
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorProductDialogCreate = Dialog.extend({
      template: 'vendor_portal_management.vendor_product_dialog',
      init: function (parent, options, values) {
        if (values.partner_consignment_margin) {this.partner_consignment_margin = values.partner_consignment_margin}
        if (values.product_margin) {this.product_margin = values.product_margin}
        else {this.product_margin = ""};
        if (values.product_category_id) {this.product_category_id = values.product_category_id}
        else {this.product_category_id = ""};
        if (values.product_category_ids) {this.product_category_ids = values.product_category_ids}
        else {this.product_category_ids = []};
        if (values.product_manufacture_code) {this.product_manufacture_code = values.product_manufacture_code}
        else {this.product_manufacture_code = ""};
        if (values.product_brand_id) {this.product_brand_id = values.product_brand_id}
        else {this.product_brand_id = ""};
        if (values.product_brand_ids) {this.product_brand_ids = values.product_brand_ids}
        else {this.product_brand_ids = []};
        if (values.product_uom_id) {this.product_uom_id = values.product_uom_id}
        else {this.product_uom_id = ""};
        if (values.product_uom_ids) {this.product_uom_ids = values.product_uom_ids}
        else {this.product_uom_ids = []};
        if (values.product_minimum_quantity) {this.product_minimum_quantity = values.product_minimum_quantity}
        else {this.product_minimum_quantity = 0};
        if (values.product_brand_margin_ids) {this.product_brand_margin_ids = values.product_brand_margin_ids}
        else {this.product_brand_margin_ids = []};
        // Re-write to create clean popup
        this._super(parent, _.extend({}, {
          title: _t("Product Create"),
          buttons: [
            {text: options.save_text || _t("Create"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.product_manufacture_code = this.$el.find('#product_manufacture_code')[0].value;
        vals.product_name = this.$el.find('#product_name')[0].value;
        vals.product_category_id = parseInt(this.$el.find('#product_category_id')[0].value);
        vals.product_brand_id = parseInt(this.$el.find('#product_brand_id')[0].value);
        vals.product_uom_id = parseInt(this.$el.find('#product_uom_id')[0].value);
        vals.description = this.$el.find('#description')[0].value;
        vals.minimum_quantity = parseInt(this.$el.find('#product_minimum_quantity')[0].value);
        vals.success = _t("The product has been successfully created");
        return vals
      },
      renderElement: function() {
        this._super()
        this.$('#product_category_id').off('change').on('change', this.update_product_margin.bind(this));
        this.$('#product_brand_id').off('change').on('change', this.update_product_margin.bind(this));
        this.$el.find("select").select2();
      },
      update_product_margin: function () {
        var self = this;
        $('#product_margin').val('');
        if (self.partner_consignment_margin) {
          $('#product_margin').val(self.partner_consignment_margin + '%');
        }

        var margin_id = self.product_brand_ids.filter(margin => {
          var product_brand_id = parseInt(self.$el.find('#product_brand_id')[0].value);
          return margin.id == product_brand_id && margin.margin > 0
        });
        if (margin_id.length) {
          $('#product_margin').val(margin_id[0].margin + '%');
        }

        var margin_id = self.product_brand_margin_ids.filter(margin => {
          var product_category_id = parseInt(self.$el.find('#product_category_id')[0].value);
          var product_brand_id = parseInt(self.$el.find('#product_brand_id')[0].value);
          var category_true = margin.category_id == product_category_id
          var brand_true = margin.brand_id == product_brand_id
          return category_true && brand_true && margin.margin > 0
        });
        if (margin_id.length) {
          $('#product_margin').val(margin_id[0].margin + '%');
        }
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'vendor.product',
          method: 'create_product_from_portal',
          args: [values],
          context: session.user_context,
        }).then(function(url) {
          self.destroyAction = "save";
          self.url_to_open = url;
          self.close();
          return
        });
      },
      close: function() {
        this.$modal.modal('hide');
        window.location = this.url_to_open;
      }
    });

    var ConfirmToggleDialog = Dialog.extend({
      template: 'vendor_portal_management.confirm_toggle_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate confirm dialog
        this.vendor_product_id = values.id;
        this._super(parent, _.extend({}, {
          title: _t("Are you sure?"),
          buttons: [
            {text: options.save_text || _t("Yes"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("No, cancel"), close: true}
          ]
        }, options || {}));
      },
      save: function (ev) {
        // The method to toggle active fueld of vendor product
        var self = this;
        rpc.query({
          model: 'vendor.product',
          method: 'toggle_vendor_product_active',
          args: [[this.vendor_product_id]],
          context: session.user_context,
        }).then(function(result) {
          self.destroyAction = "save";
          self.close();
          return
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorProductImportPrices = Dialog.extend({
      template: 'vendor_portal_management.vendor_product_import_prices',
      events: _.extend({}, Dialog.prototype.events, {
        "change #import_chosen_lines": "_changeVisibility",
        "change #archive_products": "_changeVisibility",
      }),
      init: function (parent, options, values) {
        // Re-write to initiate dialog form with default values
        this.vendor_product_help = values.vendor_product_help;
        this.template_table = values.prices_table;
        this.cur_help = values.cur_help;
        this._super(parent, _.extend({}, {
          title: _t("Import products and prices"),
          buttons: [
            {text: options.save_text || _t("Import"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      readBinary: function(file) {
        // The method to get binary content of the table
        var def = $.Deferred();
        var reader = new FileReader();
        reader.onload = function (file) {def.resolve(file.target.result)};
        reader.readAsDataURL(file);
        return def.then(function (res) {
          var base64res = res.split(',').pop();
          return base64res
        })
      },
      get_field_values: function() {
        // The method to parse values from form
        var def = $.Deferred();
        var fileTable = this.$el.find('#table_bin')[0].files;
        if (fileTable.length == 0) {def.resolve({})} else {
          var importLines = this.$el.find('#import_chosen_lines')[0].checked;
          var lineStart = this.$el.find('#lines_start')[0].value;
          var lineEnd = this.$el.find('#lines_end')[0].value;
          var archiveProducts = this.$el.find('#archive_products')[0].checked;
          var archivePrices = this.$el.find('#archive_prices')[0].checked;
          this.readBinary(fileTable[0]).then(function (file) {
            def.resolve({
              'basis': file,
              'import_chosen_lines': importLines,
              'lines_start': lineStart,
              'lines_end': lineEnd,
              'archive_products': archiveProducts,
              'archive_prices': archivePrices,
            });
          })
        };
        return def.then(function (res) {
          return res
        })
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        this.get_field_values().then(function (values) {
          rpc.query({
            model: 'vendor.product',
            method: 'import_product_prices_portal',
            args: [values],
            context: session.user_context,
          }).then(function(res_values) {
            self.destroyAction = "save";
            self.close();
            var select = new ImportResultsDialog(this, {}, res_values);
            var def = $.Deferred();
            select.on('save', this, function (root) {
              def.resolve(root);
            });
            select.open();
            return def.then(function (res) {
              location.reload();
            })
          });
        });
      },
      close: function() {
        this.$modal.modal('hide');
      },
      _changeVisibility: function(event) {
        // Method to hide / unhide settings based on other settings
        var importLines = this.$el.find('#import_chosen_lines')[0].checked;
        if (importLines) {
          this.$el.find("#lines_range").removeClass("hidden_input");
          this.$el.find("#archive_products_div").addClass("hidden_input");
          this.$el.find("#archive_prices_div").addClass("hidden_input");
        }
        else {
          this.$el.find("#lines_range").addClass("hidden_input");
          this.$el.find("#archive_products_div").removeClass("hidden_input");
          var archiveProducts = this.$el.find('#archive_products')[0].checked;
          if (archiveProducts) {
            this.$el.find("#archive_prices_div").addClass("hidden_input");
          }
          else {
            this.$el.find("#archive_prices_div").removeClass("hidden_input");
          }
        }
      },
    });

    var VendorProductImportStocks = Dialog.extend({
      template: 'vendor_portal_management.vendor_product_import_stocks',
      events: _.extend({}, Dialog.prototype.events, {
        "change #import_chosen_lines": "_changeVisibility",
        "change #archive_products": "_changeVisibility",
      }),
      init: function (parent, options, values) {
        // Re-write to initiate dialog form with default values
        this.vendor_stocks_help = values.vendor_stocks_help;
        this.template_table = values.stocks_table;
        this.uoms_help = values.uoms_help;
        this._super(parent, _.extend({}, {
          title: _t("Import products and stocks"),
          buttons: [
            {text: options.save_text || _t("Import"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      readBinary: function(file) {
        // The method to get binary content of the table
        var def = $.Deferred();
        var reader = new FileReader();
        reader.onload = function (file) {def.resolve(file.target.result)};
        reader.readAsDataURL(file);
        return def.then(function (res) {
          var base64res = res.split(',').pop();
          return base64res
        })
      },
      get_field_values: function() {
        // The method to parse values from form
        var def = $.Deferred();
        var fileTable = this.$el.find('#table_bin')[0].files;
        if (fileTable.length == 0) {def.resolve({})} else {
          var importLines = this.$el.find('#import_chosen_lines')[0].checked;
          var lineStart = this.$el.find('#lines_start')[0].value;
          var lineEnd = this.$el.find('#lines_end')[0].value;
          var archiveProducts = this.$el.find('#archive_products')[0].checked;
          var archiveStocks = this.$el.find('#archive_stocks')[0].checked;
          this.readBinary(fileTable[0]).then(function (file) {
            def.resolve({
              'basis': file,
              'import_chosen_lines': importLines,
              'lines_start': lineStart,
              'lines_end': lineEnd,
              'archive_products': archiveProducts,
              'archive_stocks': archiveStocks,
            });
          })
        };
        return def.then(function (res) {
          return res
        })
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        this.get_field_values().then(function (values) {
          rpc.query({
            model: 'vendor.product',
            method: 'import_product_stocks_portal',
            args: [values],
            context: session.user_context,
          }).then(function(res_values) {
            self.destroyAction = "save";
            self.close();
            var select = new ImportResultsDialog(this, {}, res_values);
            var def = $.Deferred();
            select.on('save', this, function (root) {
              def.resolve(root);
            });
            select.open();
            return def.then(function (res) {
              location.reload();
            })
          });
        });
      },
      close: function() {
        this.$modal.modal('hide');
      },
      _changeVisibility: function(event) {
        // Method to hide / unhide settings based on other settings
        var importLines = this.$el.find('#import_chosen_lines')[0].checked;
        if (importLines) {
          this.$el.find("#lines_range").removeClass("hidden_input");
          this.$el.find("#archive_products_div").addClass("hidden_input");
          this.$el.find("#archive_prices_div").addClass("hidden_input");
        }
        else {
          this.$el.find("#lines_range").addClass("hidden_input");
          this.$el.find("#archive_products_div").removeClass("hidden_input");
          var archiveProducts = this.$el.find('#archive_products')[0].checked;
          if (archiveProducts) {
            this.$el.find("#archive_prices_div").addClass("hidden_input");
          }
          else {
            this.$el.find("#archive_prices_div").removeClass("hidden_input");
          }
        }
      },
    });

    var ImportResultsDialog = Dialog.extend({
      template: 'vendor_portal_management.import_results',
      init: function (parent, options, values) {
        // Re-write to initiate confirm dialog
        this.results = values.results;
        this.num_updated = values.num_updated;
        this.errors = values.errors;
        this._super(parent, _.extend({}, {
          title: _t("Results of Import"),
          buttons: [
            {text: options.save_text || _t("Okay"), classes: "btn-primary o_save_button", click: this.save},
          ]
        }, options || {}));
      },
      save: function (ev) {
        // The method to toggle active fueld of vendor product
        var self = this;
        self.destroyAction = "save";
        self.close();
        return
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorPriceDialogUpdate = Dialog.extend({
      template: 'vendor_portal_management.vendor_price_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate dialog form with default values
        if (values.product_margin) {this.product_margin = values.product_margin}
        else {this.product_margin = 0};
        if (values.portal_input_price) {this.portal_input_price = values.portal_input_price}
        else {this.portal_input_price = 0};
        if (values.is_margin_included) {this.is_margin_included = values.is_margin_included}
        else {this.is_margin_included = 0};
        if (values.min_qty) {this.min_qty = values.min_qty}
        else {this.min_qty = 0};
        if (values.date_start) {this.date_start = values.date_start}
        else {this.date_start = ""};
        if (values.date_end) {this.date_end = values.date_end}
        else {this.date_end = ""};
        if (values.currency_id) {this.currency_id = values.currency_id}
        else {this.currency_id = 0};
        if (values.currency_ids) {this.currency_ids = values.currency_ids}
        else {this.currency_ids = []};
        if (values.location_id) {this.location_id = values.location_id}
        else {this.location_id = 0};
        if (values.location_ids) {this.location_ids = values.location_ids}
        else {this.location_ids = []};
        this.price_id = values.id;
        this.vendor_product_id = values.vendor_product_id;
        this._super(parent, _.extend({}, {
          title: _t("Price Update"),
          buttons: [
            {text: options.save_text || _t("Update"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.portal_input_price = this.$el.find('#portal_input_price')[0].value;
        vals.min_qty = this.$el.find('#min_qty')[0].value;
        vals.date_start = this.$el.find('#date_start')[0].value;
        vals.date_end = this.$el.find('#date_end')[0].value;
        vals.currency_id = parseInt(this.$el.find('#currency_id')[0].value);
        vals.location_id = parseInt(this.$el.find('#location_id')[0].value);
        return vals
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'product.supplierinfo',
          method: 'write_price_from_portal',
          args: [[this.price_id], values],
          context: session.user_context,
        }).then(function(success) {
          rpc.query({
            model: 'vendor.product',
            method: 'write',
            args: [[self.vendor_product_id], {"success": success}],
            context: session.user_context,
          }).then(function(res) {
            self.destroyAction = "save";
            self.close();
            return
          });
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorPriceDialogCreate = Dialog.extend({
      template: 'vendor_portal_management.vendor_price_dialog',
      init: function (parent, options, values) {
        // Re-write to create clean popup
        this.vendor_product_id = values.id;
        this.vendor_product_variant_id = values.variant_id;
        this.is_margin_included = true
        if (values.product_margin) {this.product_margin = values.product_margin}
        else {this.product_margin = 0};
        if (values.is_margin_included) {this.is_margin_included = values.is_margin_included}
        else {this.is_margin_included = 0};
        if (values.currency_ids) {this.currency_ids = values.currency_ids}
        else {this.currency_ids = []};
        if (values.location_ids) {this.location_ids = values.location_ids}
        else {this.location_ids = []};
        this.price = 0;
        this.min_qty = 0;
        this._super(parent, _.extend({}, {
          title: _t("New Price"),
          buttons: [
            {text: options.save_text || _t("Create"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.portal_input_price = this.$el.find('#portal_input_price')[0].value;
        vals.min_qty = this.$el.find('#min_qty')[0].value;
        vals.date_start = this.$el.find('#date_start')[0].value;
        vals.date_end = this.$el.find('#date_end')[0].value;
        vals.currency_id = parseInt(this.$el.find('#currency_id')[0].value);
        vals.location_id = parseInt(this.$el.find('#location_id')[0].value);
        vals.vendor_product_id = this.vendor_product_id;
        vals.vendor_product_variant_id = this.vendor_product_variant_id;
        return vals
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'product.supplierinfo',
          method: 'create_price_from_portal',
          args: [values],
          context: session.user_context,
        }).then(function(success) {
          rpc.query({
            model: 'vendor.product',
            method: 'write',
            args: [[self.vendor_product_id], {"success": success}],
            context: session.user_context,
          }).then(function(res) {
            self.destroyAction = "save";
            self.close();
            return
          });
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var ArchivePriceDialog = Dialog.extend({
      template: 'vendor_portal_management.confirm_toggle_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate confirm dialog
        this.price_id = values.id;
        this.vendor_product_id = values.vendor_product_id;
        this._super(parent, _.extend({}, {
          title: _t("Are you sure?"),
          buttons: [
            {text: options.save_text || _t("Yes"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("No, cancel"), close: true}
          ]
        }, options || {}));
      },
      save: function (ev) {
        // The method to toggle active fueld of vendor product
        var self = this;
        rpc.query({
          model: 'product.supplierinfo',
          method: 'write',
          args: [[this.price_id], {"active": false}],
          context: session.user_context,
        }).then(function(result) {
          rpc.query({
            model: 'vendor.product',
            method: 'write',
            args: [[self.vendor_product_id], {"success": _t("The price has been successfully archived")}],
            context: session.user_context,
          }).then(function(res) {
            self.destroyAction = "save";
            self.close();
            return
          });
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorQuantDialogUpdate = Dialog.extend({
      template: 'vendor_portal_management.vendor_quant_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate dialog form with default values
        if (values.supplier_quantity) {this.supplier_quantity = values.supplier_quantity}
        else {this.supplier_quantity = 0};
        if (values.location_id) {this.location_id = values.location_id}
        else {this.location_id = 0};
        if (values.location_ids) {this.location_ids = values.location_ids}
        else {this.location_ids = []};
        if (values.product_uom_name) {this.product_uom_name = values.product_uom_name}
        else {this.product_uom_name = ''};
        this.stock_id = values.id;
        this.vendor_product_id = values.vendor_product_id;
        this._super(parent, _.extend({}, {
          title: _t("Stocks Update"),
          buttons: [
            {text: options.save_text || _t("Update"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.supplier_quantity = this.$el.find('#supplier_quantity')[0].value;
        vals.vendor_location_id = parseInt(this.$el.find('#location_id')[0].value);
        return vals
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'vendor.quant',
          method: 'write_stock_from_portal',
          args: [[this.stock_id], values],
          context: session.user_context,
        }).then(function(success) {
          rpc.query({
            model: 'vendor.product',
            method: 'write',
            args: [[self.vendor_product_id], {"success": success}],
            context: session.user_context,
          }).then(function(res) {
            self.destroyAction = "save";
            self.close();
            return
          });
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorStockDialogCreate = Dialog.extend({
      template: 'vendor_portal_management.vendor_quant_dialog',
      init: function (parent, options, values) {
        // Re-write to create clean popup
        this.vendor_product_id = values.id;
        this.location_id = 0;
        this.supplier_quantity = 0;
        if (values.location_ids) {this.location_ids = values.location_ids}
        else {this.location_ids = []};
        if (values.product_uom_name) {this.product_uom_name = values.product_uom_name}
        else {this.product_uom_name = ''};
        this._super(parent, _.extend({}, {
          title: _t("New Stocks"),
          buttons: [
            {text: options.save_text || _t("Register"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.supplier_quantity = this.$el.find('#supplier_quantity')[0].value;
        vals.vendor_location_id = parseInt(this.$el.find('#location_id')[0].value);
        vals.vendor_product_id = this.vendor_product_id;
        return vals
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'vendor.quant',
          method: 'create_stock_from_portal',
          args: [values],
          context: session.user_context,
        }).then(function(success) {
          rpc.query({
            model: 'vendor.product',
            method: 'write',
            args: [[self.vendor_product_id], {"success": success}],
            context: session.user_context,
          }).then(function(res) {
            self.destroyAction = "save";
            self.close();
            return
          });
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var ArchiveStockDialog = Dialog.extend({
      template: 'vendor_portal_management.confirm_toggle_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate confirm dialog
        this.stock_id = values.id;
        this.vendor_product_id = values.vendor_product_id;
        this._super(parent, _.extend({}, {
          title: _t("Are you sure?"),
          buttons: [
            {text: options.save_text || _t("Yes"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("No, cancel"), close: true}
          ]
        }, options || {}));
      },
      save: function (ev) {
        // The method to toggle active fueld of vendor product
        var self = this;
        rpc.query({
          model: 'vendor.quant',
          method: 'write',
          args: [[this.stock_id], {"active": false}],
          context: session.user_context,
        }).then(function(result) {
          rpc.query({
            model: 'vendor.product',
            method: 'write',
            args: [[self.vendor_product_id], {"success": _t("The stock level has been successfully archived")}],
            context: session.user_context,
          }).then(function(res) {
            self.destroyAction = "save";
            self.close();
            return
          });
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorLocationDialogUpdate = Dialog.extend({
      template: 'vendor_portal_management.vendor_location_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate dialog form with default values
        if (values.name) {this.loc_name = values.name}
        else {this.loc_name = ""};
        if (values.address) {this.address = values.address}
        else {this.address = ""};
        if (values.description) {this.description = values.description}
        else {this.description = ""};
        if (values.delivery_time) {this.delivery_time = values.delivery_time}
        else {this.delivery_time = 0};
        this.vendor_location_id = values.id;
        this._super(parent, _.extend({}, {
          title: _t("Location Update"),
          buttons: [
            {text: options.save_text || _t("Update"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.name = this.$el.find('#loc_name')[0].value;
        vals.address = this.$el.find('#address')[0].value;
        vals.delivery_time = this.$el.find('#delivery_time')[0].value;
        vals.description = this.$el.find('#description')[0].value;
        vals.success = _t("The location has been successfully updated");
        return vals
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'vendor.location',
          method: 'write',
          args: [[this.vendor_location_id], values],
          context: session.user_context,
        }).then(function(result) {
          self.destroyAction = "save";
          self.close();
          return
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorLocationDialogCreate = Dialog.extend({
      template: 'vendor_portal_management.vendor_location_dialog',
      init: function (parent, options, values) {
        // Re-write to create clean popup
        this._super(parent, _.extend({}, {
          title: _t("Location Create"),
          buttons: [
            {text: options.save_text || _t("Create"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.name = this.$el.find('#loc_name')[0].value;
        vals.address = this.$el.find('#address')[0].value;
        vals.delivery_time = this.$el.find('#delivery_time')[0].value;
        vals.description = this.$el.find('#description')[0].value;
        vals.success = _t("The location has been successfully created");
        return vals
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'vendor.location',
          method: 'create_location_from_portal',
          args: [values],
          context: session.user_context,
        }).then(function(url) {
          self.destroyAction = "save";
          self.url_to_open = url;
          self.close();
          return
        });
      },
      close: function() {
        this.$modal.modal('hide');
        window.location = this.url_to_open;
      }
    });

    var ConfirmLocationToggleDialog = Dialog.extend({
      template: 'vendor_portal_management.confirm_toggle_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate confirm dialog
        this.vendor_location_id = values.id;
        this._super(parent, _.extend({}, {
          title: _t("Are you sure?"),
          buttons: [
            {text: options.save_text || _t("Yes"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("No, cancel"), close: true}
          ]
        }, options || {}));
      },
      save: function (ev) {
        // The method to toggle active fueld of vendor product
        var self = this;
        rpc.query({
          model: 'vendor.location',
          method: 'toggle_vendor_location_active',
          args: [[this.vendor_location_id]],
          context: session.user_context,
        }).then(function(result) {
          self.destroyAction = "save";
          self.close();
          return
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorPickingDialogUpdate = Dialog.extend({
      template: 'bs_sarinah_portal.vendor_picking_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate dialog form with default values
        if (values.reference) {this.reference = values.reference}
        else {this.reference = ""};
        if (values.location_id) {this.location_id = values.location_id}
        else {this.location_id = ""};
        if (values.location_ids) {this.location_ids = values.location_ids}
        else {this.location_ids = []};
        if (values.product_ids) {this.product_ids = values.product_ids}
        else {this.product_ids = []};
        if (values.uom_ids) {this.uom_ids = values.uom_ids}
        else {this.uom_ids = []};
        if (values.move_ids) {this.move_ids = values.move_ids}
        else {this.move_ids = []};
        this.picking_id = values.id;
        this._super(parent, _.extend({}, {
          title: _t("Delivery Order Update"),
          buttons: [
            {text: options.save_text || _t("Update"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.reference = this.$el.find('#reference').val();
        vals.location_id = parseInt(this.$el.find('#location_id').val());
        vals.move_lines = []
        for (var i = 1; i <= $('.move_line').length; i++) {
          vals.move_lines.push({
            'id': this.$el.find('.move_line:nth-child(' + i + ')').data('id'),
            'vendor_product_variant_id': parseInt(this.$el.find('.move_line:nth-child(' + i + ') select.move_product').val()),
            'quantity': parseFloat(this.$el.find('.move_line:nth-child(' + i + ') .move_quantity').val()),
            'product_uom_id': parseInt(this.$el.find('.move_line:nth-child(' + i + ') .move_uom').val()),
          })
        }
        return vals
      },
      renderElement: function() {
        this._super()
        var self = this;
        // Remove move line
        this.$('.remove_move').off('click').on('click', function (ev) {
          $(ev.target).parents('tr').remove()
        });
        // Onchange product
        this.$('.move_product').off('click').on('click', function (ev) {
          var product = self.product_ids.filter(el => el['id'] == ev.target.value)
          if(product.length) {
            $(ev.target).parents('tr').find('.move_uom').val(product[0].product_uom_id[0])
          }
        });
        this.$('.move_product').trigger('click');
        // Add new move line
        this.$('.add_move').off('click').on('click', function (ev) {
          var lineElement = self.$('#line-template').html()
          var tableElement = $(ev.target).parents('tr').before('<tr class="move_line">'+lineElement+'</tr>')
          self.$el.find("tr:not(#line-template) select:not([disabled])").select2();
          self.$('.remove_move').off('click').on('click', function (ev) {
            $(ev.target).parents('tr').remove()
          });
          // Onchange product
          self.$('.move_product').off('click').on('click', function (ev) {
            var product = self.product_ids.filter(el => el['id'] == ev.target.value)
            if(product.length) {
              $(ev.target).parents('tr').find('.move_uom').val(product[0].product_uom_id[0])
            }
          });
          self.$('.move_product').trigger('click');
        });
        this.$el.find("tr:not(#line-template) select:not([disabled])").select2();
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'vendor.stock.picking',
          method: 'create_from_portal',
          args: [[this.picking_id], values],
          context: session.user_context,
        }).then(function(result) {
          self.destroyAction = "save";
          self.close();
          return
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var VendorPickingDialogCreate = Dialog.extend({
      template: 'bs_sarinah_portal.vendor_picking_dialog',
      init: function (parent, options, values) {
        if (values.location_ids) {this.location_ids = values.location_ids}
        else {this.location_ids = []};
        if (values.product_ids) {this.product_ids = values.product_ids}
        else {this.product_ids = []};
        if (values.uom_ids) {this.uom_ids = values.uom_ids}
        else {this.uom_ids = []};
        if (values.move_ids) {this.move_ids = values.move_ids}
        else {this.move_ids = []};
        if (values.operation_type) {this.operation_type = values.operation_type}
        else {this.operation_type = False};
        // Re-write to create clean popup
        let title = "Delivery Order Create"
        if (this.operation_type == 'outgoing')
          title = "Delivery Order Return Create"
        this._super(parent, _.extend({}, {
          title: _t(title),
          buttons: [
            {text: options.save_text || _t("Create"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("Cancel"), close: true}
          ]
        }, options || {}));
      },
      get_field_values: function() {
        // The method to parse values from form
        var vals = {};
        vals.reference = this.$el.find('#reference').val();
        vals.location_id = parseInt(this.$el.find('#location_id').val());
        vals.operation_type = this.operation_type;
        vals.move_lines = []
        for (var i = 1; i <= $('.move_line').length; i++) {
          vals.move_lines.push({
            'id': this.$el.find('.move_line:nth-child(' + i + ')').data('id'),
            'vendor_product_variant_id': parseInt(this.$el.find('.move_line:nth-child(' + i + ') select.move_product').val()),
            'quantity': parseFloat(this.$el.find('.move_line:nth-child(' + i + ') .move_quantity').val()),
            'product_uom_id': parseInt(this.$el.find('.move_line:nth-child(' + i + ') .move_uom').val()),
          })
        }
        return vals
      },
      renderElement: function() {
        this._super()
        var self = this;
        // Remove move line
        this.$('.remove_move').off('click').on('click', function (ev) {
          $(ev.target).parents('tr').remove()
        });
        // Onchange product
        this.$('.move_product').off('click').on('click', function (ev) {
          var product = self.product_ids.filter(el => el['id'] == ev.target.value)
          if(product.length) {
            $(ev.target).parents('tr').find('.move_uom').val(product[0].product_uom_id[0])
          }
        });
        this.$('.move_product').trigger('click');
        // Add new move line
        this.$('.add_move').off('click').on('click', function (ev) {
          var lineElement = self.$('#line-template').html()
          var tableElement = $(ev.target).parents('tr').before('<tr class="move_line">'+lineElement+'</tr>')
          self.$el.find("tr:not(#line-template) select:not([disabled])").select2();
          self.$('.remove_move').off('click').on('click', function (ev) {
            $(ev.target).parents('tr').remove()
          });
          // Onchange product
          self.$('.move_product').off('click').on('click', function (ev) {
            var product = self.product_ids.filter(el => el['id'] == ev.target.value)
            if(product.length) {
              $(ev.target).parents('tr').find('.move_uom').val(product[0].product_uom_id[0])
            }
          });
          self.$('.move_product').trigger('click');
        });
        this.$el.find("tr:not(#line-template) select:not([disabled])").select2();
      },
      save: function (ev) {
        // The method to save values to vendor product
        var self = this;
        var values = this.get_field_values();
        rpc.query({
          model: 'vendor.stock.picking',
          method: 'create_from_portal',
          args: [[], values],
          context: session.user_context,
        }).then(function(url) {
          self.destroyAction = "save";
          self.url_to_open = url;
          self.close();
          return
        });
      },
      close: function() {
        this.$modal.modal('hide');
        if (this.url_to_open) {
          window.location = this.url_to_open;
          return
        }
        window.location.reload();
      }
    });

    var VendorPickingDialogDelete = Dialog.extend({
      template: 'bs_sarinah_portal.vendor_picking_dialog_delete',
      init: function (parent, options, values) {
        // Re-write to initiate dialog form with default values
        this.picking_id = values.id;
        this.picking_name = values.name;
        this._super(parent, _.extend({}, {
          title: _t("Delivery Order Delete"),
          buttons: [
            {text: options.delete_text || _t("Delete"), classes: "btn-danger o_delete_button", click: this.delete},
            {text: _t("Cancel"), classes: "text-danger", close: true}
          ]
        }, options || {}));
      },
      renderElement: function() {
        this._super()
        var self = this;
        // Remove move line
        this.$('.remove_move').off('click').on('click', function (ev) {
          $(ev.target).parents('tr').remove()
        });
        // Onchange product
        this.$('.move_product').off('click').on('click', function (ev) {
          var product = self.product_ids.filter(el => el['id'] == ev.target.value)
          if(product.length) {
            $(ev.target).parents('tr').find('.move_uom').val(product[0].product_uom_id[0])
          }
        });
        this.$('.move_product').trigger('click');
        // Add new move line
        this.$('.add_move').off('click').on('click', function (ev) {
          var lineElement = self.$('#line-template').html()
          var tableElement = $(ev.target).parents('tr').before('<tr class="move_line">'+lineElement+'</tr>')
          self.$el.find("tr:not(#line-template) select:not([disabled])").select2();
          self.$('.remove_move').off('click').on('click', function (ev) {
            $(ev.target).parents('tr').remove()
          });
          // Onchange product
          self.$('.move_product').off('click').on('click', function (ev) {
            var product = self.product_ids.filter(el => el['id'] == ev.target.value)
            if(product.length) {
              $(ev.target).parents('tr').find('.move_uom').val(product[0].product_uom_id[0])
            }
          });
          self.$('.move_product').trigger('click');
        });
        this.$el.find("tr:not(#line-template) select:not([disabled])").select2();
      },
      delete: function (ev) {
        // The method to delete vendor picking
        var self = this;
        rpc.query({
          model: 'vendor.stock.picking',
          method: 'delete_from_portal',
          args: [[this.picking_id]],
          context: session.user_context,
        }).then(function(url) {
          self.destroyAction = "delete";
          self.close();
          window.location = url;
        });
      },
      close: function() {
        this.$modal.modal('hide');
      }
    });

    var DeleteProductAttributeDialog = Dialog.extend({
      template: 'vendor_portal_management.confirm_toggle_dialog',
      init: function (parent, options, values) {
        // Re-write to initiate confirm dialog
        this.id = values.id;
        this.attribute_id = values.attribute_id;
        this._super(parent, _.extend({}, {
          title: _t("Are you sure?"),
          buttons: [
            {text: options.save_text || _t("Yes"), classes: "btn-primary o_save_button", click: this.save},
            {text: _t("No, cancel"), close: true}
          ]
        }, options || {}));
      },
      save: function (ev) {
        // The method to toggle active fueld of vendor product
        var self = this;
        rpc.query({
          model: 'vendor.product',
          method: 'delete_attribute_from_portal',
          args: [[this.id], this.attribute_id],
          context: session.user_context,
        }).then(function(result) {
          self.destroyAction = "save";
          self.close();
        });
      },
      close: function() {
        this.$modal.modal('hide');
        location.reload();
      }
    });

    var ProductAttributeList = Widget.extend({
      template: 'bs_sarinah_portal.product_attribute_list',
      events: {
        "change .value_ids>select[multiple]": "_onValueChange",
        "change #action-change-attribute": "_onAttributeChange",
        "click .add_attribute": "_onAttributeAdd",
        "click .remove_attribute": "_onAttributeDelete",
      },
      init: function (parent, productVariantList) {
        this._super(parent);
        this.id = parseInt($('section#product_attributes').data('product'));
        this.productVariantList = productVariantList;
      },
      willStart: function() {
        var self = this;
        var def = rpc.query({
          model: 'vendor.product',
          method: 'get_attributes',
          args: [[self.id]]
        }).then(function (result) {
          self.data = result;
        });
        return Promise.all([this._super.apply(this, arguments), def]);
      },
      renderElement: function() {
        this._super()
        var self = this;

        self.$el.find("select[multiple]").select2();
      },
      _onValueChange: function (ev) {
        if (!this.data.is_readonly) {
          var self = this;
          var ids = ev.val.map(val => parseInt(val));
          var line_id = parseInt($(ev.currentTarget).parents('tr').data('line-id'));
          rpc.query({
            model: 'vendor.product.attr.line',
            method: 'update_value_from_portal',
            args: [[line_id], ids],
            context: session.user_context,
          }).then(function(res) {
            self.replace($('section#product_attributes'));
            self.productVariantList.replace($('section#product_variants'));
          });
        };
      },
      _onAttributeChange: function (ev) {
        var self = this;
        $('#value_ids').html(JSON.parse($('#action-change-attribute')[0]
          .selectedOptions[0].dataset['values'])
          .reduce((bank, val) => bank+`<option value='${val.id}'>${val.name}</option>`, ''));
      },
      _onAttributeAdd: function (ev) {
        if (!this.data.is_readonly) {
          var self = this;
          var id = parseInt(ev.currentTarget.id);
          var attr = parseInt($(ev.currentTarget).parents('tr').find('td #attribute_id > select').val());
          var values = $(ev.currentTarget).parents('tr').find('#value_ids').val().map(val => parseInt(val));
          rpc.query({
            model: 'vendor.product',
            method: 'create_attribute_from_portal',
            args: [[id], attr, values],
            context: session.user_context,
          }).then(function(res) {
            if (res) {
              self.replace($('section#product_attributes'));
              self.productVariantList.replace($('section#product_variants'));
            }
          });
        };
      },
      _onAttributeDelete: function (ev) {
        if (!this.data.is_readonly) {
          var self = this;
          var id = parseInt(ev.currentTarget.dataset['product']);
          var attribute_id = parseInt(ev.currentTarget.id);
          rpc.query({
            model: 'vendor.product',
            method: 'delete_attribute_from_portal',
            args: [[id], attribute_id],
            context: session.user_context,
          }).then(function(result) {
            if (result) {
              self.replace($('section#product_attributes'));
              self.productVariantList.replace($('section#product_variants'));
            }
          });
        };
      }

    });

    var ProductVariantList = Widget.extend({
      template: 'bs_sarinah_portal.product_variant_list',
      init: function (parent) {
        this._super(parent);
        this.id = parseInt($('section#product_variants').data('product'));
      },
      willStart: function() {
        var self = this;
        var def = rpc.query({
          model: 'vendor.product',
          method: 'get_variants',
          args: [[self.id]]
        }).then(function (result) {
          self.variants = result;
        });
        return Promise.all([this._super.apply(this, arguments), def]);
      },
    });

    var ProductImageList = Widget.extend({
      template: 'bs_sarinah_portal.product_image_list',
      events: {
        "click #add-image": "_onAddImage",
        // "change #new-image-input": "_onImageAdded",
        "click .change-image": "_onChangeImage",
        "click .remove-image": "_onImageRemoved",
        // "click #remove-image": "_onRemoveImage",
      },
      init: function (parent) {
        this._super(parent);
        this.id = parseInt($('section#product_images').data('product'));
      },
      willStart: function() {
        var self = this;
        var def = rpc.query({
          model: 'vendor.product',
          method: 'get_images',
          args: [[self.id]]
        }).then(function (result) {
          self.images = result;
        });
        return Promise.all([this._super.apply(this, arguments), def]);
      },
      _onAddImage: function(ev) {
        var $input = this.$el.siblings('#new-image-input')
        $input.click();
        $input.change(this._onImageAdded.bind(this));
      },
      _onChangeImage: function(ev) {
        var $input = this.$el.siblings('#change-image-input')
        $input.click();
        $input.change(this._onImageChanged.bind(this));
        $input.data('image_id', ev.currentTarget.id);
      },
      _onImageRemoved: function(ev) {
        ev.stopPropagation();
        var self = this;
        var image_id = parseInt(ev.currentTarget.id);
        rpc.query({
          model: 'vendor.product.image',
          method: 'unlink',
          args: [[image_id]],
          context: session.user_context,
        }).then(function(result) {
          if (result) {
            self.replace($('section#product_images'));
          }
        });
      },
      _onImageAdded: function(ev) {
        var self = this;
        Array.from(ev.currentTarget.files).forEach(file => {
            var reader = new FileReader();
            reader.readAsBinaryString(file);
            reader.onerror = console.log;
            reader.onload = function (res) {
                var values = {
                    product_id: self.id,
                    image_1920: btoa(res.target.result),
                }
                rpc.query({
                model: 'vendor.product.image',
                method: 'create',
                args: [values],
                context: session.user_context,
                }).then(function(result) {
                if (result) {
                    self.replace($('section#product_images'));
                }
                });
            };
        });
      },
      _onImageChanged: function(ev) {
        var self = this;
        var reader = new FileReader();
        reader.readAsBinaryString(ev.currentTarget.files[0]);
        reader.onerror = console.log;
        reader.onload = function (res) {
            var image_id = parseInt($(ev.currentTarget).data('image_id'));
            var values = {
                image_1920: btoa(res.target.result),
            }
            rpc.query({
            model: 'vendor.product.image',
            method: 'write',
            args: [[image_id], values],
            context: session.user_context,
            }).then(function(result) {
            if (result) {
                self.replace($('section#product_images'));
            }
            });
        };
      },
    });
  });
