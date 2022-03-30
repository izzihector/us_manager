odoo.define('pos_gift_voucher.models', function (require) {
"use strict";

var PosBaseWidget = require('point_of_sale.BaseWidget');
var chrome = require('point_of_sale.chrome');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var rpc = require('web.rpc');
var time = require('web.time');
var temp_voucher_array=new Array();

var global_serial_no = new Array();
var coupon_id = new Array();
var element = null;

var QWeb = core.qweb;
var _t = core._t;

function formatDate(value)
{
   return value.getMonth()+1 + "/" + value.getDate() + "/" + value.getFullYear();
}

//At POS Startup, load gift voucher related account journals model
//models.load_fields('account.journal',['name','for_gift_coupens','is_loyalty_journal']);
models.load_fields('pos.payment.method',['name','for_gift_coupens']);
// models.load_fields('product.product',['coupon'])

//At POS Startup, load gift voucher model
models.load_models({
    model: 'gift.voucher',
    fields: ['id','product_id','voucher_serial_no','source','voucher_name','redeemed_out','redeemed_in','date','remaining_amt','used_amt'],
    // domain: function(self){ return [['redeemed_in','=',false],['last_date','>', time.date_to_str(new Date())]]; },
    loaded: function(self,gift_voucher){
        self.gift_voucher = gift_voucher;
    },
});

//At POS Startup, load gift voucher related fields from product.template model
models.load_models({
    model: 'product.template',
    fields: ['id','name','coupon','list_price','default_code','property_account_income_id','barcode','validity'],
    loaded: function(self,products){
        self.products = products;
    },
});

// Extended the Order model
var _super_order = models.Order.prototype;
models.Order = models.Order.extend({
	initialize: function(attributes,options){
		_super_order.initialize.call(this,attributes,options);
		
		var synch = this.pos.get('synch');
        if(synch.state === "disconnected"){
	        g = this.pos.get('gift_voucher');
	        for(i=0;i<g.length;i++){
	       	 for(j=0;j<temp_voucher_array.length;j++){
	       		 if(g[i].voucher_serial_no == temp_voucher_array[j]){
	       			 g.splice(i, 1);
	       		 }
	       	 }
	        }
        }
		
		this.cust_name;
        this.coupon_name;
        this.coupon_id=new Array();
        this.serial_nos = new Array();
        this.coupon_redeemed = new Array();
        this.voucher_number = new Array();
        this.coupon_unit_price=new Array();
        this.coupon_qty=new Array();
        this.journal_id;
        
        this.quantity = 1;
        this.quantityStr = '1';
        this.voucher_serial_no = new Date().getTime()+ "0"
        this.global_serial_no=[];
        this.element = document.getElementById("canv");
        
	},
	remove_orderline: function( line ){
    	var prod_id = line.product.id;
    	if (this.coupon_id){
	    	var index = this.coupon_id.indexOf(prod_id);
	    	if(line.product.coupon && this.coupon_id.length > 0 && index >= 0){
	    		this.coupon_id.splice(index, 1);
	    		this.assert_editable();
	            this.orderlines.remove(line);
	            this.select_orderline(this.get_last_orderline());
	    	}else{
	    		_super_order.remove_orderline.call(this,line);
	    	}
    	}},
	add_product: function(product, options){
		var self = this;
    	var start_flag = false;
    	var currentOrderLines = this.pos.get_order().get_orderlines()
    	var products=this.pos.products;
    	var selected_product_id=product.product_tmpl_id;
    	if(currentOrderLines.length == 0)
    	{
    		start_flag = true;
    		for(var product_id in products)
    		{
	    		if(products[product_id].id==selected_product_id)	
	    		{
	    			coupon_id.push(products[product_id].id)
	    			if(products[product_id].coupon==true)
					{
	    				this.pos.get('selectedOrder').set_coupon_name(true);
						var is_coupon_flag=true;
						break;
					}
	    			break;
	    		}
    		}
    	}
    	else
    	{
    		var is_coupon_flag=false;
    		for(var line in currentOrderLines)
			{	
    		var orderline_product_id = currentOrderLines[line].get_product().product_tmpl_id;
    		var selected_product_id=product.product_tmpl_id;
    		for(var product_id in products)
    		{
    			if(products[product_id].id==selected_product_id)
    			{
    				if(products[product_id].coupon==true)
    				{
    					is_coupon_flag=true;
    					break;
    				}
    			}
    		}
			}
    		for (var product_id in products)
    		{
    			if(products[product_id].id==orderline_product_id)
    			{
    				if(products[product_id].coupon==true && is_coupon_flag==true)
    				{
    					start_flag = true;
    					this.pos.get_order().set_coupon_name(true);
    					for(product_id in products)
    					{
    						if(products[product_id].id==selected_product_id)	
    						{
    							coupon_id.push(products[product_id].id)
    							break;
    						}
    					}
    					break;
    				}
    				else if(products[product_id].coupon==false && is_coupon_flag==false)
    				{
    					start_flag = true;
    					this.pos.get_order().set_coupon_name(false);
    					for(product_id in products)
    					{
    						if(products[product_id].id==selected_product_id)	
    						{
    							break;
    						}
    					}
    					break;
    				}
    			}
			}
    	}
    	if(start_flag == true)
    		{
    			_super_order.add_product.call(this,product, options);
    		}
	},
	
	export_as_JSON: function(){
        var Json = _super_order.export_as_JSON.call(this);
		var d = new Date();
		var creation_date = ""+String(d.getMonth()+1)+"-"+String(d.getDate())+"-"+String(d. getFullYear());
		Json.coupon_name = this.get_coupon_name(),
		Json.coupon_id = this.get_coupon_id(),
		Json.company = this.pos.company.name,
		Json.date = creation_date,
		Json.coupon_redeemed = this.get_coupon_redeemed(),
		Json.coupon_qty = this.get_coupon_qty(),
		Json.coupon_unit_price = this.get_coupon_unit_price(),
		Json.coupon_unique_no = this.get_voucher_number()
		return Json;
	},
	export_for_printing : function(){
		var Json = _super_order.export_for_printing.call(this);
		Json.coupon_unique_nos = this.get_voucher_number();
		return Json;
	},
	finalize: function(){
		var self = this;
		var order = self.pos.get_order();
		var lines = order.get_orderlines();
		for(var i=0; i<lines.length; i++){
			var product = lines[i].get_product();
			break;
		}
		if(product.coupon){
			var model = 'gift.voucher';
	        var fields = ['id','product_id','voucher_serial_no','source','voucher_name','redeemed_out','redeemed_in','date', 'remaining_amt','used_amt'];
	        var domain = [['redeemed_in','=',false],['last_date','>', time.date_to_str(new Date())]];
			var params = {
                    model  : model,
                    method : 'search_read',
                    domain : domain,
                    fields : fields,
                };
			rpc.query(params).then(function(result){
				self.pos.gift_voucher = result;
			});
		}
		_super_order.finalize.call(self);
	},
	set_voucher_number:function(){
    	global_serial_no.length=0;
    },


    get_voucher_number:function(){
    	return global_serial_no;
    },
    set_coupon_name:function(coupon_name){
    	this.set('coupon_name',coupon_name);
    },
    get_coupon_name:function(){
    	return this.get('coupon_name');
    },
    get_coupon_qty:function(){
    	return this.get('coupon_qty');
    },
    set_coupon_qty:function(coupon_qty){
     	this.set('coupon_qty',coupon_qty);
    },
    get_coupon_unit_price:function(){
       return this.get('coupon_unit_price');
    },
    set_coupon_unit_price:function(coupon_unit_price){
       	this.set('coupon_unit_price',coupon_unit_price);

    },

    set_coupon_redeemed:function(coupon_redeemed){
     	this.set('coupon_redeemed',coupon_redeemed);
    },
    get_coupon_redeemed:function(){
    	return this.get('coupon_redeemed');
    },
    set_coupon_id:function(coupon_id){
    	this.coupon_id.push(coupon_id);
    },
    get_coupon_id:function(){
      return this.coupon_id;
    },
    reset_global_serial_no:function(){
    	  global_serial_no = [];
   },
});

// Extended the Orderline model
var _super_orderline = models.Orderline.prototype;
models.Orderline = models.Orderline.extend({
	initialize: function(attr,options){
		_super_orderline.initialize.call(this, attr,options);
        this.serial_nos = new Array();
        this.voucher_serial_no = new Date().getTime()+ "0";
        this.cust_id;
        this.global_serial_no=[];
	},
	uniqueSerialNo: function(i) {
		this.voucher_serial_no = new Date().getTime()+Math.floor(Math.random()*101)+i.toString();
      	global_serial_no.push(this.voucher_serial_no);
	},
	getUniqueId:function(){
		return this.global_serial_no;
    },
    set_serial_no:function(serial_nos){
    	this.serial_nos=serial_nos;
	},
	get_serial_no:function(){
    	return this.serial_nos;
    },
    export_as_JSON: function(){
		var orderLineJson = _super_orderline.export_as_JSON.call(this);
		orderLineJson.voucher_no = this.voucher_serial_no;
		return orderLineJson;
	},
	export_for_printing : function() {
		var Json = _super_orderline.export_for_printing.call(this);
		Json.voucher_no = this.voucher_serial_no || '';
		Json.is_coupon = this.get_product().coupon;
		return Json;
	},
});


});