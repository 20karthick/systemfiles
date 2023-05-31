odoo.define('mena_hr_dashboard.Dashboard', function (require){
"use strict";
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var ajax = require('web.ajax');
var Model = require('web.Model');
var widget = require('web.Widget');
var _t = core._t;

var hedDashboard = AbstractAction.extend({
   template: 'hedDashboard',
   events: {
        'click .hr-dashboard':'get_hr_view',
        'click .emp-timesheet':'get_timesheet_view',
        'click .emp-attendances':'get_attendances_view',
        'click .emp-calender':'get_calender_view',
        'click .emp-time-off':'get_time_off_view',
    },
   init: function(parent, context) {
       this._super(parent, context);
       this.dashboards_templates = ['DashboardProject'];
   },

       willStart: function() {
       var self = this;
       return $.when(ajax.loadLibs(this), this._super()).then(function() {
           return self.get_tiles_data();
       });
   },
   start: function() {
           var self = this;
           this.set("title", 'Dashboard');
           return this._super().then(function() {
               self.render_dashboards();
           });
       },
       get_hr_view: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("HR Dashboard"),
            type: 'ir.actions.client',
            tag: 'custom_hr_dashboard_tags',
            target: 'current'
        }, options)
    },
    get_timesheet_view: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };

        this.do_action({
            name: _t("Timesheet"),
            type: 'ir.actions.act_window',
            res_model: 'account.analytic.line',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        }, options)
    },
    get_attendances_view: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Attendance"),
            type: 'ir.actions.act_window',
            res_model: 'hr.attendance',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        }, options)
    },
get_calender_view: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Calender"),
            type: 'ir.actions.act_window',
            res_model: 'calendar.event',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        }, options)
    },
get_time_off_view: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Time Off"),
            type: 'ir.actions.act_window',
            res_model: 'hr.leave',
            view_mode: 'calendar,tree,form,activity',
            view_type: 'form',
            views: [[false, 'calendar'],[false, 'list'],[false, 'form'],[false, 'activity']],
            search_view_id: [false, "search"],
            target: 'current'
        }, options)


    },
       render_dashboards: function(){
       var self = this;
       _.each(this.dashboards_templates, function(template) {
               self.$('.o_pos_dashboard').append(QWeb.render(template, {widget: self}));
           });
   },
    get_tiles_data: function() {
           var self = this;
           var def1 = this._rpc({
                   model: 'hr.dashboard',
                   method: 'get_tiles_data'
       }).then(function(result)
        {
      self.total_projects = result['total_projects'],
      self.total_tasks = result['total_tasks'],
      self.total_employees = result['total_employees']
   });
       return $.when(def1);
   },
})
core.action_registry.add('custom_dashboard_tags', hedDashboard);
return hedDashboard;
})


