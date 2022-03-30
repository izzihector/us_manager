odoo.define('branch.AbstractWebClient', function (require) {
"use strict";
var AbstractWebClient = require('web.AbstractWebClient');
var ActionManager = require('web.ActionManager');
var concurrency = require('web.concurrency');
var core = require('web.core');
var config = require('web.config');
var WarningDialog = require('web.CrashManager').WarningDialog;
var data_manager = require('web.data_manager');
var dom = require('web.dom');
var KeyboardNavigationMixin = require('web.KeyboardNavigationMixin');
var Loading = require('web.Loading');
var local_storage = require('web.local_storage');
var RainbowMan = require('web.RainbowMan');
var ServiceProviderMixin = require('web.ServiceProviderMixin');
var session = require('web.session');
var utils = require('web.utils');
var Widget = require('web.Widget');

var _t = core._t;
AbstractWebClient.include({

    start: function () {
        var self = this;

        var state = $.bbq.getState();
        // If not set on the url, retrieve bids from the local storage
        // of from the default branch on the user
        var current_branch_id = session.user_branches.current_branch[0]
        if (!state.bids) {
            state.bids = utils.get_cookie('bids') !== null ? utils.get_cookie('bids') : String(current_branch_id);
        }
        
        var stateBranchIDS = _.map(state.bids.split(','), function (bid) { return parseInt(bid) });
        var userBranchIDS = _.map(session.user_branches.allowed_branch, function(branch) {return branch[0]});
        
        // Check that the user has access to all the branches
        if (!_.isEmpty(_.difference(stateBranchIDS, userBranchIDS))) {
            state.bids = String(current_branch_id);
            stateBranchIDS = [current_branch_id];
        }
        // Update the user context with this configuration
        session.user_context.allowed_branch_ids = stateBranchIDS;
        return this._super.apply(this, arguments).then(() => {
            $.bbq.pushState(state);
        });
    },

    _onPushState: function (e) {
        this.do_push_state(_.extend(e.data.state, {'cids': $.bbq.getState().cids,
            'bids': $.bbq.getState().bids}));
    },

    });
});
