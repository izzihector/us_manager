// pos_bag_charges js
//console.log("custom callleddddddddddddddddddddd")
odoo.define('pos_bag_charges.pos', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');

    var _t = core._t;



// Start PosBagWidget
    
    var PosBagWidget = screens.ActionButtonWidget.extend({
        template: 'PosBagWidget',
        
        renderElement: function(){
            var self = this;
            this._super();
            
            this.$el.click(function(){
                var selectedOrder = self.pos.get_order();
                var category = self.pos.config.pos_bag_category_id;
                var categ = self.pos.db.get_product_by_category(category[0])
                
                var products = self.pos.db.get_product_by_category(category[0])[0];
                //console.log("productssssssssssssssssssssssssssssssssssssssssss",products)
                    
                //if (product.length == 1) {   
                if (self.pos.db.get_product_by_category(self.pos.config.pos_bag_category_id[0]).length == 1) { 
                    selectedOrder.add_product(products);
                    //console.log("lasttttttttttttttttttttttt selewcted orderrrrrrrrrrrrrr",selectedOrder)
                    self.pos.set_order(selectedOrder);
                    

                    self.gui.show_screen('products');
                }else{
                    var orderlines = self.pos.db.get_product_by_category(category[0]);
                    for(var i = 0 ; i<orderlines.length ; i++){
                         orderlines[i]['image_url'] = window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id=' + orderlines[i].id;
                     }
                    self.gui.show_popup('pos_bag_popup_widget', {'orderlines': orderlines});
                }
                //self.gui.show_popup('pos_bag_popup_widget', {'orderlines': orderlines});

            });
        },
            button_click: function(){},
            highlight: function(highlight){
            this.$el.toggleClass('highlight',!!highlight);
        },
        
        
        
    });

    screens.define_action_button({
        'name': 'Pos Bag Widget',
        'widget': PosBagWidget,
        'condition': function() {
            return true;
        },
    });
    // End CreateSalesOrderButtonWidget 



    // PosBagPopupWidget Popup start

    var PosBagPopupWidget = popups.extend({
        template: 'PosBagPopupWidget',
        init: function(parent, args) {
            this._super(parent, args);
            this.options = {};
        },
        
        events: {
            'click .product.bag-category': 'click_on_bag_product',
            'click .button.cancel': 'click_cancel',
        },
        //
        
        // get_product_image_url: function(product) {
        //     return window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id=' + product.id;
        // },
        // show: function(options) {
        //     options = options || {};
        //     //console.log("optionssssssssssssssssssssssssssssssssssssssssssssssssssss",options)
        //     var self = this;
        //     this._super(options);
        //     this.orderlines = options.orderlines || [];
        //     //console.log("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!this.orderlines",this.orderlines)
        //     var image_url = this.get_product_image_url(options);
        //     //console.log("!!!!!!!!!!!!!!!!!!!!!image_url!!!!!!!!!!!!!!!this.orderlines",image_url)

       

        // },
        
        click_on_bag_product: function(event) {
            var self = this;
            var bag_id = parseInt(event.currentTarget.dataset['productId'])
           
            //var bag_id = parseInt($(this).parent().data('id'));
            self.pos.get_order().add_product(self.pos.db.product_by_id[bag_id]);
            self.pos.gui.close_popup();
        },


    });
    gui.define_popup({
        name: 'pos_bag_popup_widget',
        widget: PosBagPopupWidget
    });

    // End Popup start



});
