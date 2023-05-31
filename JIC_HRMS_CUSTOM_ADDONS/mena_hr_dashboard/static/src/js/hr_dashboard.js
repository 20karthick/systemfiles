odoo.define('mena_hr_dashboard.hr_Dashboard', function (require){
"use strict";
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var ajax = require('web.ajax');
var Model = require('web.Model');
var widget = require('web.Widget');
var _t = core._t;

var HRDashboard = AbstractAction.extend({
   template: 'HRDashboard',
   events: {
        'click .hr-employee':'get_employee_view',
//        'click .hr-department':'get_department_view',
        'click .hr-jd':'get_jd_view',
        'click .hr-recruitment':'get_recruitment_view',
        'click .hr-payroll':'get_payroll_view',
    },

   init: function(parent, context) {
       this._super(parent, context);
       this.dashboards_templates = ['HRDashboardProject'];
       this.url = false;
       this.recruitment_url = false;
       this.payroll = false;
   },

    willStart: function() {
       var self = this;
       return $.when(ajax.loadLibs(this),
        this._super()).then(function() {
           return self.get_employee_menu(), self.get_recruitment_menu(), self.get_payroll_menu();
       });
   },

   start: function() {
           var self = this;
           this.set("title", 'Hr');
           return this._super().then(function() {
               self.render_dashboards();
           });
           },

   get_employee_menu: function() {
           var self = this;
           var def1 =  this._rpc({
                   model: 'hr.dashboard',
                   method: 'get_employee_menu'
                   }).then(function(result)
                    {
                    self.url = result.redirect;
                   });
                       return $.when(def1);
       },

       get_employee_view: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        self.do_action({type: 'ir.actions.act_url', url: this.url, target: 'self'});
        },

   get_recruitment_menu: function() {
           var self = this;
           var def1 =  this._rpc({
                   model: 'hr.dashboard',
                   method: 'get_recruitment_menu'
                   }).then(function(result)
                    {
                    self.recruitment_url = result.redirect;
                   });
                       return $.when(def1);
       },

       get_recruitment_view: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        self.do_action({type: 'ir.actions.act_url', url: this.recruitment_url, target: 'self'});
        },


        get_payroll_menu: function() {
                   var self = this;
                   var def1 =  this._rpc({
                           model: 'hr.dashboard',
                           method: 'get_payroll_menu'
                           }).then(function(result)
                            {
                            self.payroll_url = result.redirect;
                           });
                               return $.when(def1);
               },

               get_payroll_view: function(e){
                var self = this;
                e.stopPropagation();
                e.preventDefault();
                self.do_action({type: 'ir.actions.act_url', url: this.payroll_url, target: 'self'});
                },


//       get_department_view: function(e){
//        var self = this;
//        e.stopPropagation();
//        e.preventDefault();
//        this.do_action({
//            name: "Department",
//            type: 'ir.actions.act_window',
//            res_model: 'hr.department',
//            view_mode: 'kanban,tree,form',
//            views: [[false, 'kanban'],[false, 'list'],[false, 'form']],
//            target: 'self',
//
//        })
//        },
       get_jd_view: function(e){
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            this.do_action({
                name: "Department",
                type: 'ir.actions.act_window',
                res_model: 'job.description',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                target: 'self',

            })
        },




       render_dashboards: function(){
       var self = this;
       _.each(this.dashboards_templates, function(template) {
               self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}));
           });
   },
})
core.action_registry.add('custom_hr_dashboard_tags', HRDashboard);
return HRDashboard;
})





