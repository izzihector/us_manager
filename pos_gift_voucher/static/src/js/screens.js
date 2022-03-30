odoo.define('pos_gift_voucher.screens', function (require) {
	"use strict";

	var PosBaseWidget = require('point_of_sale.BaseWidget');
	var chrome = require('point_of_sale.chrome');
	var gui = require('point_of_sale.gui');
	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var rpc = require('web.rpc');

	var voucher_code_array = new Array();
	var name_template_array = new Array();
	var temp_voucher_array = new Array();
	var updated_sale_price = 0.0;
	var sale_price_total = 0.0;
	var coupon_id = new Array();
	var coupon_qty = new Array();
	var coupon_unit_price = new Array();
	var cnt = 0;
	var ajax = require('web.ajax');
	var voucher_selected = new Array();
	var voucher_scanned = new Array();
	var voucher_amount = 0;

	var tendered = 0;

	var isVoucherPaymentActive = false

	var QWeb = core.qweb;
	var _t = core._t;
	screens.NumpadWidget.include({
		start: function () {
			this._super();
			var self = this;
			var orderlines = this.pos.get_order().get_orderlines();
			$(".mode-button[data-mode='discount']").on('click', function () {
				if (orderlines.length && orderlines[0].product.coupon) {
					self.state.reset();
					//      			alert("Your not allowed to set Discount");
					self.gui.show_popup('alert', {
						'title': _t('Warning: Discount'),
						'body': _t('Your not allowed to set Discount.'),
					});
				}
			});
			$(".mode-button[data-mode='price']").on('click', function () {
				if (orderlines.length && orderlines[0].product.coupon) {
					self.state.reset();
					//      			alert("Your not allowed to change Price");
					self.gui.show_popup('alert', {
						'title': _t('Warning: Price'),
						'body': _t('Your not allowed to change Price.'),
					});
				}
			});
		},
	});
	screens.PaymentScreenWidget.include({
		show: function () {
			this._super();
			$('.gift-coupon-line').hide();

			if (isVoucherPaymentActive) {
				$('body').off('keypress', this.keyboard_handler);
				$('body').off('keydown', this.keyboard_keydown_handler);
			}
		},
		click_paymentline: function (cid) {
			var self = this;
			var lines = this.pos.get_order().get_paymentlines();
			for (var i = 0; i < lines.length; i++) {
				if (lines[i].cid === cid) {
					this.pos.get_order().select_paymentline(lines[i]);
					this.reset_input();
					if (lines[i].payment_method.for_gift_coupens) {
						$('.payment-numpad').hide();
						$('.gift-coupon-line').show();
						$('#gift-coupon').focus();
						self.remove_listner();
					} else {
						$('.gift-coupon-line').hide();
						$('.payment-numpad').show();
						self.add_listner();
					}
					this.render_paymentlines();
					return;
				}
			}
		},

		click_paymentmethods: function (id) {
			//		this._super(id);
			var payment_method = this.pos.payment_methods_by_id[id]
			var self = this;
			var order = self.pos.get_order();
			if (!order) {
				return;
			}
			var lines = order.get_paymentlines();

			let tender = document.getElementsByClassName('col-tendered')
			var due = this.$('.paymentline .col-due')

			let tender_total = 0
			for (let i = 0; i < tender.length; i++) {
				let tv = parseFloat(tender[i].innerText.replace(/,/g, ""))
				tender_total += tv
			}

			// var current_amount = parseFloat(this.$('.paymentline.selected .edit').text())
			var current_amount = tender_total

			// this.$('.paymentline.selected .edit').text(999);
			console.log('current_amount', current_amount);
			console.log('payment_method', payment_method);

			if (payment_method?.for_gift_coupens == true) isVoucherPaymentActive = true

			console.log('isVoucherPaymentActive', isVoucherPaymentActive);
			if (!isVoucherPaymentActive) {
				console.log('isVoucherPaymentActive tidak ada');
				$('.payment-numpad').show();
			} else {
				var method_detail_gift = this.pos.payment_methods;
				console.log('lines', lines);
				$.each(lines, function (index, line) {
					for (var i = 0; i < method_detail_gift.length; i++) {
						if (method_detail_gift[i].for_gift_coupens) {
							var m_name = method_detail_gift[i].name;
							if (!line.name?.search(m_name)) {
								let g_amt = line.get_amount();
								if (!g_amt)
									line.set_amount(0);
								break;
							}
						}
					}
				});
			}

			var is_coupon_line = false;
			if (lines.length > 0) {
				for (var i = 0; i < lines.length; i++) {
					if (lines[i].payment_method.for_gift_coupens) {
						is_coupon_line = true;
					}
				}
				if (!is_coupon_line || !payment_method.for_gift_coupens) {
					if (payment_method.for_gift_coupens) {
						$('.payment-numpad').hide();
						self.remove_listner();
						isVoucherPaymentActive = true
					} else {
						self.add_listner();
						$('.payment-numpad').show();
						isVoucherPaymentActive = false
					}
					self._super(id);
					is_coupon_line = false;
				}
				else {
					self.remove_listner();
				}
			} else {
				if (payment_method.for_gift_coupens) {
					self.remove_listner();
					$('.payment-numpad').hide();
					isVoucherPaymentActive = true
				}
				else {
					self.add_listner();
					$('.payment-numpad').show();
					isVoucherPaymentActive = false
				}

				this._super(id);
			}

			var currentOrderLines = self.pos.get_order().get_orderlines();
			var order = self.pos.get_order();

			order.reset_global_serial_no();
			for (var line in currentOrderLines) {
				if (currentOrderLines[line].get_product().coupon) {
					var orderline_prod_id = currentOrderLines[line].get_product().id;
					var product_qty = currentOrderLines[line].get_quantity();
					for (var i = 0; i < product_qty; i++) {
						var line = order.orderlines.at(order.orderlines.length - 1);
						line.uniqueSerialNo(i);
						order.set_coupon_id(orderline_prod_id);
					}
				}
			}
		},
		add_listner: function () {
			$('body').off('keypress', this.keyboard_handler);
			$('body').off('keydown', this.keyboard_keydown_handler);
			$('body').keypress(this.keyboard_handler);
			$('body').keydown(this.keyboard_keydown_handler);
		},
		remove_listner: function () {
			$('body').off('keypress', this.keyboard_handler);
			$('body').off('keydown', this.keyboard_keydown_handler);
			// window.document.body.removeEventListener('keypress', this.keyboard_handler);
			// window.document.body.removeEventListener('keydown', this.keyboard_keydown_handler);
		},
		render_paymentlines: function () {
			var self = this;
			var order = this.pos.get_order();
			if (!order) {
				return;
			}
			console.log('order', order);
			var lines = order.get_paymentlines();
			var due = order.get_due();
			var extradue = 0;
			if (due && lines.length && due !== order.get_due(lines[lines.length - 1])) {
				extradue = due;
			}
			var is_coupon_line = false;
			for (var i = 0; i < lines.length; i++) {
				if (lines[i].payment_method.for_gift_coupens) {
					is_coupon_line = true;
				}
			}
			if (is_coupon_line) {
				this.$('.paymentlines-container').empty();
				var lines = $(QWeb.render('PaymentScreen-Paymentlines', {
					widget: this,
					order: order,
					paymentlines: lines,
					extradue: extradue,
					is_gift_coupon: 1,
				}));
			}
			else {
				this.$('.paymentlines-container').empty();
				var lines = $(QWeb.render('PaymentScreen-Paymentlines', {
					widget: this,
					order: order,
					paymentlines: lines,
					extradue: extradue,
					is_gift_coupon: 0,
				}));
			}
			lines.on('click', '.delete-button', function () {
				self.click_delete_paymentline($(this).data('cid'));
			});

			lines.on('click', '.paymentline', function () {
				self.click_paymentline($(this).data('cid'));
			});

			lines.on('click', '.cancel-coupon-button', function () {
				self.cancelgiftVoucher();
			});

			lines.on('click', '.add-coupon-button', function () {
				self.addgiftVoucher();
				//            $('.next').addClass('highlight');
			});

			lines.appendTo(this.$('.paymentlines-container'));

			var new_lines = order.get_paymentlines();
			$.each(new_lines, function (index, value) {
				if (value.selected && !value.payment_method.for_gift_coupens) {
					$('.gift-coupon-line').hide();
				}
				if (value.selected && value.payment_method.for_gift_coupens) {
					$(".paymentlines").ready(function () {
						$(this).val('');
						//        			$(this).focus();
					});
					$("#gift-coupon").focus();
				}
			});

			if (is_coupon_line) {
				console.log('is_coupon_line', is_coupon_line);
				this.$('.paymentline.selected .edit').empty();
				this.$('.paymentline.selected .edit').text(0);
				this.$('.paymentline.selected .edit').html(0);

				console.log('tendered', tendered);
				if (tendered < 1) {
					console.log('No tender');
					this.getAmount(0);
					$('.next').removeClass('highlight');
				} else {
					$('.next').addClass('highlight');
				}
			}

			// if (is_coupon_line) {
			// 	this.$('.paymentline.selected .edit').empty();
			// 	this.$('.paymentline.selected .edit').text(0);
			// 	this.$('.paymentline.selected .edit').html(0);

			// 	// if (parseFloat(this.$('.paymentline.selected .edit').text()) == 0 || typeof (parseFloat(this.$('.paymentline.selected .edit').text()) == 0) == undefined) {
			// 	// this.getAmount(0);
			// 	$('.next').removeClass('highlight');
			// 	// }
			// }

			this.render_payment_terminal();
		},

		getAmount: function (amt) {
			var ret_amt;
			var method_detail_gift = this.pos.payment_methods;
			var order = this.pos.get_order();
			if (!order) {
				return;
			}

			var paymentlines = order.get_paymentlines();
			//		paymentlinesss.each(function(line){
			$.each(paymentlines, function (index, line) {
				for (var i = 0; i < method_detail_gift.length; i++) {
					if (method_detail_gift[i].for_gift_coupens) {
						var m_name = method_detail_gift[i].name;
						if (!line.name?.search(m_name)) {
							line.set_amount(amt);
							ret_amt = line.get_amount();
							break;
						}
					}
				}
			});
			return ret_amt;
		},
		addgiftVoucher: function () {
			let _this = this;
			_this.chrome.loading_show()
			_this.chrome.loading_message(_t('Loading .'))
			let dot = 2
			let _handleLoadingMessage = setInterval(() => {
				if (dot == 1) {
					_this.chrome.loading_message(_t('Loading .'))
					dot = 2
				} else if (dot == 2) {
					_this.chrome.loading_message(_t('Loading ..'))
					dot = 3
				} else if (dot == 3) {
					_this.chrome.loading_message(_t('Loading ...'))
					dot = 1
				}
			}, 1000)

			var flag = true;
			var scanned_flag = true;
			var redeemed_flag = true;
			var valid_voucher_flag = false;
			var valid_flag = false;
			var voucher_validity;
			var products = this.pos.products;
			var gift_voucher_obj = this.pos.gift_voucher;
			var entered_voucher_code = $("#gift-coupon").val();
			var voucher_source;
			var voucher_name;
			var creation_date;
			var name_template;
			var order = this.pos.get_order();
			if (!order) {
				return;
			}

			var lines = order.get_paymentlines(); // line transaksi
			var remaining = order.get_due();

			if (remaining < 1) {
				let due = this.$('.paymentline .col-due')
				for (let i = 0; i < due.length; i++) {
					let tv = parseFloat(due[i].innerText.replace(/,/g, ""))
					remaining += tv
				}
			}

			if (entered_voucher_code == '') {
				_this.chrome.loading_hide()
				return $.msgBox({
					title: "Warning",
					content: "Coupon field is empty",
					type: "error",
					opacity: 0.6,
					buttons: [{ value: "Ok" }],
				});
			} else {
				if (voucher_scanned.includes(entered_voucher_code)) {
					_this.chrome.loading_hide()
					return $.msgBox({
						title: "Warning",
						content: "Voucher has been scanned",
						type: "error",
						opacity: 0.6,
						buttons: [{ value: "Ok" }],
					});
				}

				let payload = {
					'voucher_code': entered_voucher_code,
				}

				ajax.post(`/api/voucher/check`, payload)
					.then((res) => {
						_this.chrome.loading_hide()
						let data = JSON.parse(res);

						if (data?.success === true) {
							for (var voucher in gift_voucher_obj) {
								if (gift_voucher_obj[voucher].voucher_serial_no == entered_voucher_code) { // jika voucher yg di scan ada di dalam temp voucher
									voucher_source = gift_voucher_obj[voucher].source; // ambil source voucher
									voucher_name = gift_voucher_obj[voucher].voucher_name; // ambil nama voucher
									creation_date = gift_voucher_obj[voucher].date; // ambil tanggal buat voucher
									valid_voucher_flag = true; // tandai voucher valid
									var check_remaining_amount = data?.data?.remainValue; // ambil sisa voucher
									break;
								}
							}
							valid_flag = true
							if (valid_flag == true) {
								if (temp_voucher_array.length > 0) {
									for (sold_voucher in temp_voucher_array) {
										if ((temp_voucher_array[sold_voucher] == entered_voucher_code) && (check_remaining_amount <= 0.0)) {
											$.msgBox({
												title: "Warning",
												content: "This coupon is already scanned",
												type: "error",
												opacity: 0.6,
												buttons: [{ value: "Ok" }],
											});
											scanned_flag = false;
											flag = false;
											break;
										} else {
											flag = true;
										}

									}
									if (flag == true) {
										for (voucher in gift_voucher_obj) {
											if (gift_voucher_obj[voucher].voucher_serial_no == entered_voucher_code) {
												voucher_code_array.push(entered_voucher_code)
												temp_voucher_array.push(entered_voucher_code)
												voucher_selected.push(entered_voucher_code)
												voucher_scanned.push(entered_voucher_code)
												// pushed_amount = voucher_amount + gift_voucher_obj[voucher].amount
												// voucher_amount = pushed_amount
												name_template = gift_voucher_obj[voucher].voucher_name;
												name_template_array.push(gift_voucher_obj[voucher].voucher_name)
												flag = true;
												break;
											}
											else {
												flag = false;
											}
										}
									}
								} else {
									for (var voucher in gift_voucher_obj) {
										if (gift_voucher_obj[voucher].voucher_serial_no == entered_voucher_code) {
											var is_sold = gift_voucher_obj[voucher].redeemed_out;
											var is_redeemed = gift_voucher_obj[voucher].redeemed_in;
											if (is_sold == true) {
												voucher_code_array.push(entered_voucher_code)
												temp_voucher_array.push(entered_voucher_code)
												voucher_selected.push(entered_voucher_code)
												voucher_scanned.push(entered_voucher_code)
												// pushed_amount = voucher_amount + gift_voucher_obj[voucher].amount
												// voucher_amount = pushed_amount
												name_template = gift_voucher_obj[voucher].voucher_name;
												name_template_array.push(gift_voucher_obj[voucher].voucher_name)
												flag = true;
												break;
											} else {
												flag = false;
											}
										} else {
											flag = false;
										}
									}
								}
							} else {
								flag = false;
							}

							for (var product in products) {
								if (products[product].name == name_template) {
									var coupon_price = data?.data?.remainValue;
									if (remaining >= coupon_price) {
										var coupon_code = document.getElementById("gift-coupon").value;
										sessionStorage['coupon_code'] = coupon_code
										sessionStorage['used_amount'] = remaining
										var total = this.getAmount(updated_sale_price);
										var current_amount = parseFloat(this.$('.paymentline.selected .edit').text())
										current_amount = current_amount == 1 ? 0 : current_amount

										for (var lot in gift_voucher_obj) {
											if (gift_voucher_obj[lot].voucher_serial_no == coupon_code) {
												if (data?.data?.remainValue < coupon_price) {
													updated_sale_price = data?.data?.remainValue
												}
												else {
													updated_sale_price = parseFloat(current_amount) + coupon_price
												}
												console.log('current_amount', current_amount)
												console.log('coupon_price', coupon_price)
												console.log('updated_sale_price', updated_sale_price)
												var remaining_amount = data?.data?.remainValue;
												var redeemed_in_on_deduction = remaining_amount - remaining
											}
										}
										if (data?.data?.remainValue < remaining) {
											var deducted_amt = remaining - data?.data?.remainValue
											var alert_message = "Your amount is greater than your coupon amount<br><br>Current Amount = " + remaining + "<br>Coupon Amount = " + data?.data?.remainValue + "<br><br>Your need to pay the following amount by cash = " + deducted_amt
											$.msgBox({
												title: "Warning",
												content: alert_message,
												type: "error",
												opacity: 0.6,
												buttons: [{ value: "Ok" }],
											});
											tendered += updated_sale_price
											this.getAmount(updated_sale_price);
											this.renderElement();
											this.$('.paymentline.selected .edit').text(parseFloat(updated_sale_price).toFixed(2));
										} else {
											console.log('a');
											let xx = order.get_total_with_tax();
											// let xx = 777;
											var alert_message = "Your amount is smaller than your coupon amount<br><br>Current Amount = " + remaining + "<br>Coupon Amount = " + data?.data?.remainValue
											$.msgBox({
												title: "Warning",
												content: alert_message,
												type: "success",
												opacity: 0.6,
												buttons: [{ value: "Ok" }],
											});
											tendered += xx
											this.getAmount(xx);
											this.renderElement();
											this.$('.paymentline.selected .edit').text(parseFloat(xx).toFixed(2));
										}

										$("#gift_coupon_desc").show();
										$("#gift-voucher-code").show();
										document.getElementById("gift-coupon").value = "";
										document.getElementById("gift-coupon").focus();
										$('.payment-numpad').hide();

										break;
									} else {
										if (remaining < coupon_price) {
											var coupon_code = document.getElementById("gift-coupon").value;
											sessionStorage['coupon_code'] = coupon_code
											sessionStorage['used_amount'] = remaining
											var total = this.getAmount(updated_sale_price);
											var current_amount = parseFloat(this.$('.paymentline.selected .edit').text())
											updated_sale_price = coupon_price
											for (var lot in gift_voucher_obj) {
												if (gift_voucher_obj[lot].voucher_serial_no == coupon_code) {
													var redeemed_in_on_deduction = data?.data?.remainValue - remaining
													updated_sale_price = data?.data?.remainValue
													console.log('updated_sale_price', updated_sale_price)
												}
											}

											if (data?.data?.remainValue < remaining) {
												var deducted_amt = remaining - data?.data?.remainValue
												var alert_message = "Your amount is greater than your coupon amount<br><br>Current Amount = " + remaining + "<br>Coupon Amount = " + data?.data?.remainValue + "<br><br>Your need to pay the following amount by cash = " + deducted_amt
												$.msgBox({
													title: "Warning",
													content: alert_message,
													type: "error",
													opacity: 0.6,
													buttons: [{ value: "Ok" }],
												});
												tendered += updated_sale_price
												this.getAmount(updated_sale_price);
												this.renderElement();
												this.$('.paymentline.selected .edit').text(parseFloat(updated_sale_price).toFixed(2));
											}
											else {
												console.log('b');
												let xx = order.get_total_with_tax();
												// let xx = 777;
												var alert_message = "Your amount is smaller than your coupon amount<br><br>Current Amount = " + remaining + "<br>Coupon Amount = " + data?.data?.remainValue
												$.msgBox({
													title: "Warning",
													content: alert_message,
													type: "success",
													opacity: 0.6,
													buttons: [{ value: "Ok" }],
												});
												tendered += xx
												this.getAmount(xx);
												this.renderElement();
												this.$('.paymentline.selected .edit').text(parseFloat(xx).toFixed(2));
											}

											$("#gift_coupon_desc").show();
											$("#gift-voucher-code").show();
											document.getElementById("gift-coupon").value = "";
											document.getElementById("gift-coupon").focus();
											$('.payment-numpad').hide();
											break;
										}

										if (temp_voucher_array.length > 0) {
											for (var sold_voucher in temp_voucher_array) {
												if (temp_voucher_array[sold_voucher] == entered_voucher_code) {
													var index = temp_voucher_array.indexOf(entered_voucher_code);
													temp_voucher_array.splice(index, 1);
													var code_index = voucher_code_array.indexOf(entered_voucher_code);
													voucher_code_array.splice(code_index, 1);
													break;
												}
											}
										}
									}
								}
							}
							for (var lot in gift_voucher_obj) {
								if (gift_voucher_obj[lot].voucher_serial_no == coupon_code) {
									if ((data?.data?.remainValue == 0.0) || (redeemed_in_on_deduction < 0.0)) {
										order.set_coupon_redeemed(voucher_code_array);
										gift_voucher_obj[lot].redeemed_in = true
										return voucher_code_array;
									}
								}
							}
						} else {
							return $.msgBox({
								title: "Warning",
								content: data?.message,
								type: "error",
								opacity: 0.6,
								buttons: [{ value: "Ok" }],
							});
						}
					}).catch((err) => {
						_this.chrome.loading_hide()
						return $.msgBox({
							title: "Warning",
							content: err,
							type: "error",
							opacity: 0.6,
							buttons: [{ value: "Ok" }],
						});
					})
			}
		},

		cancelgiftVoucher: function () {
			var coupon_exist_flag = true;
			var products = this.pos.products;
			var gift_voucher_obj = this.pos.gift_voucher;
			var sale_price = 0.0;
			var sum = 0.0;
			var coup_name = "";
			var coupon_code = document.getElementById("gift-coupon").value;
			if (coupon_code == '') {
			}
			else {
				for (var coupon in voucher_code_array) {
					if (voucher_code_array[coupon] == coupon_code) {
						var index = voucher_code_array.indexOf(coupon_code);
						voucher_code_array.splice(index, 1);
						coupon_exist_flag = true;
						break;
					}
					else {
						coupon_exist_flag = false;
					}
				}
				if (coupon_exist_flag == false) {
					$.msgBox({
						title: "Warning",
						content: "We can not cancel this Gift Voucher Code as it is not Added for Redemption",
						type: "error",
						opacity: 0.6,
						buttons: [{ value: "Ok" }],
					});

				}
				else {
					for (var lot in gift_voucher_obj) {
						if (gift_voucher_obj[lot].voucher_serial_no == coupon_code) {
							coup_name = gift_voucher_obj[lot].voucher_name;
							break;
						}
					}
					for (var product in products) {
						var toggle = true; // Require to avoids multiple warning
						// messages
						for (var template in name_template_array) {
							if (products[product].name == coup_name) {
								sale_price = products[product].list_price;
								sum = this.getAmount(updated_sale_price);
								if (sum == 0.0) {

									if (toggle == true) {
										$.msgBox({
											title: "Warning",
											content: "No more gift coupon to cancel",
											type: "error",
											opacity: 0.6,
											buttons: [{ value: "Ok" }],
										});
										toggle = false;
									}
									document.getElementById("gift-coupon").value = ""
								}
								else {
									updated_sale_price = sum - sale_price;
									if (temp_voucher_array.length > 0) {
										for (var voucher in temp_voucher_array) {
											if (temp_voucher_array[voucher] == coupon_code) {
												var index = temp_voucher_array.indexOf(coupon_code);
												temp_voucher_array.splice(index, 1);

												var index2 = voucher_scanned.indexOf(coupon_code);
												voucher_scanned.splice(index2, 1);
												break;
											}
										}
									}
									else {
										$.msgBox({
											title: "Warning",
											content: "No such coupon to cancel",
											type: "error",
											opacity: 0.6,
											buttons: [{ value: "Ok" }],
										});
									}
									this.getAmount(updated_sale_price);
									this.renderElement();
									$("#gift_coupon_desc").show();
									$("#gift-voucher-code").show();
									document.getElementById("gift-coupon").value = ""
									document.getElementById("gift-coupon").focus()
									$('#coupon-calculated-price').trigger('keyup');
									$('.payment-numpad').hide();
									break;
								}
							}
						}
					}
				}
			}
		},
		validate_order: function (force_validation) {
			this._super(force_validation);
			var self = this;
			var updated_sale_price = 0.0;
			// Barcode Generation=============>>
			var element = document.getElementById("canv");
			var currentOrderLines = self.pos.get_order().get_orderlines();
			var orderline_product_id;
			var is_coupon_flag = false;
			var products = self.pos.products;
			var order = this.pos.get_order();
			//--------------------------------------------------------
			// var coupon_code = sessionStorage['coupon_code']
			var coupon_code = voucher_selected
			var u_amount = sessionStorage['used_amount']
			var used_amount = parseFloat(u_amount)

			var gift_voucher_obj = this.pos.gift_voucher;
			var name_template;

			//--------------------------------------------------------
			for (var line in currentOrderLines) {
				var orderline_product_id = currentOrderLines[line].get_product().product_tmpl_id;
			}
			for (var product_id in products) {
				if (products[product_id].id == orderline_product_id) {
					if (products[product_id].coupon == true) {
						is_coupon_flag = true;
						break;
					} else {
						is_coupon_flag = false;
						break;
					}
				}
			}

			//------------------CODE TO USE THE COUPON WITH ANY AMOUNT OF REDEMPTION----------------------------
			for (var voucher in gift_voucher_obj) {
				if (coupon_code.includes(gift_voucher_obj[voucher].voucher_serial_no)) {
					name_template = gift_voucher_obj[voucher].voucher_name;
					for (var product in products) {
						if (products[product].name == name_template) {
							var coupon_price = parseFloat(products[product].list_price);

							if (used_amount < coupon_price) {
								gift_voucher_obj[voucher].remaining_amt = gift_voucher_obj[voucher].remaining_amt - used_amount
								gift_voucher_obj[voucher].used_amt = gift_voucher_obj[voucher].used_amt + used_amount
								rpc.query({
									model: 'gift.voucher',
									method: 'update_coupon_amount',
									args: [{ 'voucher_serial_no': gift_voucher_obj[voucher].voucher_serial_no, 'amt': used_amount }],
								}).then(function (result) {
									// self.pos.gift_voucher = result
								});
							} else {
								rpc.query({
									model: 'gift.voucher',
									method: 'update_coupon_amount',
									args: [{ 'voucher_serial_no': gift_voucher_obj[voucher].voucher_serial_no, 'amt': used_amount }],
								}).then(function (result) {
									// self.pos.gift_voucher = result
								});
							}
						}
					}
				}
			}
			voucher_selected = []
			sessionStorage['coupon_code'] = 0
			sessionStorage['used_amount'] = 0

			//----------------------------------------------------------------------------------------------------------------
			if (is_coupon_flag == true) {
				var serial = self.pos.get_order().get_voucher_number();
				for (var x in serial) {

					var canvas_div = document.createElement('div');
					canvas_div.id = serial[x];
					var elem = document.createElement('canvas');
					elem.id = serial[x];

					var barcode_div = document.createElement('div');
					barcode_div.id = "barcode";
					barcode_div.style.color = "black";
					barcode_div.style.visibility = 'visible';
					barcode_div.innerHTML = serial[x];

					var text = serial[x].replace(/^\s+/, '').replace(/\s+$/, '');
					var elt = symdesc[9];
					var altx = serial[x].replace(/^\s+/, '').replace(/\s+$/, '');
					var opts = "includetext parsefnc".replace(/^\s+/, '').replace(/\s+$/, '');
					var bw = new BWIPJS;

					// Convert the options to a dictionary object, so we can pass alttext with
					// spaces.
					var tmp = opts.split(' ');
					opts = {};
					for (var i = 0; i < tmp.length; i++) {
						if (!tmp[i])
							continue;
						var eq = tmp[i].indexOf('=');
						if (eq == -1)
							opts[tmp[i]] = bw.value(true);
						else
							opts[tmp[i].substr(0, eq)] = bw.value(tmp[i].substr(eq + 1));
					}

					// Add the alternate text
					if (altx)
						opts.alttext = bw.value(altx);

					// Add any hard-coded options required to fix problems in the javascript
					// emulation.
					opts.inkspread = bw.value(0);
					if (needyoffset[elt.sym] && !opts.textxalign && !opts.textyalign &&
						!opts.alttext && opts.textyoffset === undefined)
						opts.textyoffset = bw.value(-10);

					var rot = 'N';
					bw.bitmap(new Bitmap);
					bw.scale("1", "1");


					var div = document.getElementById('output');
					if (div)
						div.innerHTML = '';

					bw.push(text);
					bw.push(opts);

					try {

						bw.call(elt.sym);
						bw.bitmap().show(elem, rot);

					} catch (e) {
						var s = '';
						if (e.fileName)
							s += e.fileName + ' ';
						if (e.lineNumber)
							s += '[line ' + e.lineNumber + '] ';
					}
					canvas_div.appendChild(elem);
					canvas_div.appendChild(barcode_div);
					element.appendChild(canvas_div);
				}
			}
			//self.pos.get('selectedOrder').set_voucher_number();
			tendered = 0
		},

	});

});