/* Copyright 2020 Pablo Carrio Garcia <pablocarrio@stylecre.es>
*/

odoo.define('pos_mobile_ui.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var chrome = require('point_of_sale.chrome');
    var PosBaseWidget = require('point_of_sale.BaseWidget');

    var MobileHideCatsButtonWidget = PosBaseWidget.extend({
        template: 'MobileHideCatsButton',
        init: function(parent, options){
            options = options || {};
            this._super(parent,options);
        },
        renderElement: function(){
            var self = this;
            this._super();
        },
        hide: function(){
            this.$el.addClass('oe_hidden');
        },
        show: function(){
            this.$el.removeClass('oe_hidden');
        },
        start: function(){
            var self = this;
            this._super();
            this.$el.click(function(){
                self.getParent().$('.categories').toggleClass('collapsed');
            });
        }
    });

    screens.ProductCategoriesWidget.include({
        renderElement: function(){
            var self = this;
            this._super();
            this.$el = $(this.el)
            if(this.subcategories.length){
                var widget = new MobileHideCatsButtonWidget(this,{});
                widget.appendTo(this.$('.categories'));
            }
        }
    });

    var mobile_show_left_pane_index = null;
    screens.OrderWidget.include({
      orderline_add: function(){
        var self = this;
        this._super();
        self.pos.chrome.widget.mobile_show_left_pane.renderElement()
      },
      orderline_remove: function(line){
        var self = this;
        this._super(line);
        console.log(self.pos.chrome.widget);
        self.pos.chrome.widget.mobile_show_left_pane.renderElement()
      },
      change_selected_order: function(line){
        var self = this;
        this._super();
        self.pos.chrome.widget.mobile_show_left_pane.renderElement()
      }
    });

    var MobileHideKbButtonWidget = PosBaseWidget.extend({
        template: 'MobileHideKbButton',
        init: function(parent, options){
            options = options || {};
            this._super(parent,options);
        },
        renderElement: function(){
            var self = this;
            this._super();
        },
        hide: function(){
            this.$el.addClass('oe_hidden');
        },
        show: function(){
            this.$el.removeClass('oe_hidden');
        },
        start: function(){
            var self = this;
            this._super();

            var kb = self.getParent().$('.leftpane>.window>.subwindow.collapsed');
            this.$el.click(function(){
                kb.toggleClass('collapsed');
            });
        }
    });

    chrome.Chrome.include({
        build_widgets: function(){
            this.widgets.push({
                'name':   'mobile_show_left_pane',
                'widget': MobileLeftPaneButtonWidget,
                'append':  '.pos-rightheader'
            });
            this._super();
            this.$el.find('.order-selector').after("<span id=\"rightheader-separator\"></span>");
        }
    });

    var MobileLeftPaneButtonWidget = PosBaseWidget.extend({
        template: 'MobileLeftPaneButton',
        init: function(parent, options){
            options = options || {};
            this._super(parent,options);
        },
        renderElement: function(){
            var self = this;
            this._super();
            if(this.pos.config.iface_floorplan){
                if(this.pos.get_order()){
                    this.$el.removeClass("oe_hidden");
                }else{
                    this.$el.addClass("oe_hidden");
                }
            }

            this.$el.click(function(event){
              self.getParent().$('.leftpane').toggleClass('show');
              event.preventDefault();
              event.stopPropagation();
            });
        },
        hide: function(){
            this.$el.addClass('oe_hidden');
        },
        show: function(){
            this.$el.removeClass('oe_hidden');
        }
    });

    var MobileMoreControlsButton = screens.ActionButtonWidget.extend({
        template: 'MobileMoreControlsButton',
        start: function(){
            var self = this;

            this._super();

            this.$el.click(function(){
                self.$el.closest('.control-buttons').toggleClass('show');
            });

            $(window).click(function(event) {
                if(!$(event.target).closest('.control-buttons').length && !$(event.target).closest('.popup').length)
                    self.$el.closest('.control-buttons').removeClass('show');
            });
        }
    });

    screens.ProductScreenWidget.include({
        start: function(){
            var self = this;
            this._super();
            var widget = new MobileHideKbButtonWidget(this,{});
            widget.prependTo(this.$('.leftpane>.window>.subwindow.collapsed .pads'));

            var widget2 = new MobileMoreControlsButton(this,{});
            widget2.prependTo(this.$('.control-buttons'));

            $(window).click(function(event) {
                if(!$(event.target).closest('.orderline').length && !$(event.target).closest('.leftpane').length && !$(event.target).closest('.popup').length)
                    self.$('.leftpane').removeClass('show');
            });

            if(this.$('.leftpane').height()>500)
                this.$('.leftpane>.window>.subwindow.collapsed').removeClass('collapsed');
        },
        show: function(){
            this._super();
            this.chrome.widget.mobile_show_left_pane.show();
        },
        close: function(){
            this._super();
            this.chrome.widget.mobile_show_left_pane.hide();
        }
    });

    return {
        MobileLeftPaneButtonWidget: MobileLeftPaneButtonWidget,
        MobileMoreControlsButton: MobileMoreControlsButton,
        MobileHideKbButtonWidget: MobileHideKbButtonWidget,
        MobileHideCatsButtonWidget: MobileHideCatsButtonWidget
    };
});
