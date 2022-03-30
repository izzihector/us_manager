$(function(){
	$('#survey_bidgasbin_tbl').DataTable({
		'dom': '<f<t>p>'
	});
});

odoo.define('mcs_vendor_portal.costume', function (require) {
"use strict";
   var Model = require('web.DataModel');

   new Model("group_js").call("get_record",[]).then(function(result){
     console.log(result);//show in console Hello
   });
});