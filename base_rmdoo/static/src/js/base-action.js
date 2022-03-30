odoo.define('base_rmdoo.BaseAction', function(require) {
    "use strict";

    var core = require('web.core');
    var _t = core._t;
    // var FavoriteMenu = require('web.FavoriteMenu');

    function PrintView(parent, action) {
        window.print();
    }

    function AddToDash(parent, action) {
        for (var key in parent.actions) {
            return parent._rpc({
                    route: '/board/add_to_dashboard',
                    params: {
                        action_id: parent.actions[key].id || false,
                        context_to_save: parent.actions[key].context,
                        domain: parent.actions[key].domain || [],
                        view_mode: parent.actions[key].view_mode,
                        name: parent.actions[key].name,
                    },
                })
                .then(function(r) {
                    if (r) {
                        parent.do_notify(
                            _t('Please refresh your browser for the changes to take effect.')
                        );
                    } else {
                        parent.do_warn(_t("Could not add filter to dashboard"));
                    }
                });
        }
    }

    core.action_registry.add("print_view", PrintView);
    core.action_registry.add("add_to_dash", AddToDash);

    return {
        core: core
    };
});

// odoo.define('base_rmdoo.UserMenu', function(require) {
//     var widget = require('web.UserMenu');

//     var UserMenu = widget.include({
//         _onMenuDocumentation: function() {
//             window.open('https://www.rmdoo.com/user-doc/', '_blank');
//         },
//         _onMenuSupport: function() {
//             window.open('https://www.rmdoo.com/contactus', '_blank');
//         },
//     });

//     return {
//         UserMenu: UserMenu
//     };
// });

// $(document).ready(function() {
//     $('.pvtUi *').contextmenu(function() {
//         $('.pvtUiCell').show(100);
//     });
//     $('.pvtUi').mouseleave(function() {
//         $('.pvtUiCell').hide(100);
//     });
// });