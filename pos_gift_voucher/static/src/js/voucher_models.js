odoo.define('pos_gift_voucher.pos_gift_voucher', function (require) {
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var screens = require('point_of_sale.screens');
    var _t = core._t;
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');

    var popups = require('point_of_sale.popups');
    var VoucherActivatePopupWidget = popups.extend({
        template: 'VoucherActivatePopupWidget',
        show: function ({ confirm }) {
            this._super({ confirm });
        },
    });
    gui.define_popup({ name: 'voucher-activate', widget: VoucherActivatePopupWidget });

    var SelectVoucherButton = screens.ActionButtonWidget.extend({
        template: 'SelectVoucherButton',
        button_click: function () {
            let _this = this;

            return _this.pos.gui.show_popup('voucher-activate', {
                confirm: () => {
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

                    let order_id = $('#order_id').val()
                    let voucher_codes = document.getElementsByClassName('voucher_code')
                    let arr_lengh = voucher_codes.length

                    let voucher_arr = []
                    for (let i = 0; i < arr_lengh; i++) {
                        voucher_arr.push(voucher_codes[i].value)
                    }
                    let voucher_str = voucher_arr.join(", ")

                    if (order_id && voucher_arr?.length > 0) {
                        let payload = {
                            'order_id': order_id,
                            'voucher_code': voucher_str,
                        };

                        ajax.post(`/api/voucher/activation`, payload)
                            .then((res) => {
                                let data = JSON.parse(res)
                                if (data?.by) {
                                    _this.pos.gui.show_popup('alert', {
                                        'title': _t(`Warning`),
                                        'body': _t(data?.by + ': ' + data?.message),
                                    });
                                } else {
                                    _this.pos.gui.show_popup('alert', {
                                        'title': _t(`Warning`),
                                        'body': _t(data?.message),
                                    });
                                }

                                var model = 'gift.voucher';
                                var fields = ['id', 'product_id', 'voucher_serial_no', 'source', 'voucher_name', 'redeemed_out', 'redeemed_in', 'date', 'remaining_amt', 'used_amt'];
                                var domain = [['redeemed_in', '=', false]];
                                var params = {
                                    model: model,
                                    method: 'search_read',
                                    domain: domain,
                                    fields: fields,
                                };

                                rpc.query(params).then(function (result) {
                                    _this.pos.gift_voucher = result
                                });

                                _this.chrome.loading_hide()
                                clearInterval(_handleLoadingMessage)
                            }).catch((err) => {
                                _this.chrome.loading_hide()
                                clearInterval(_handleLoadingMessage)
                            })
                    } else {
                        _this.chrome.loading_hide()
                        clearInterval(_handleLoadingMessage)

                        if (!order_id)
                            alert('Order ID cannot be blank')
                        if (voucher_arr?.length < 1)
                            alert('Voucher Code cannot be blank')
                    }
                },
            })
        },
    });
    //
    screens.define_action_button({
        'name': 'SelectVoucherButton',
        'widget': SelectVoucherButton,
    });
    //
});
