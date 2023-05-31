odoo.define('youmodule.yourmodule', function (require) {
   "use strict";

   var core = require('web.core');
   var field_utils = require('web.field_utils');

   const session = require('web.session');

   var MyAttendances = require('hr_attendance.my_attendances');

   var _t = core._t;
   var QWeb = core.qweb;

   MyAttendances.include({
       // You need to redefine the function here

        update_attendance: function () {
            var self = this;
            var new_context = false;
            var ip = false;
            var latitude = false;
            var longitude = false;

            var items = [];
            $.getJSON('https://api.ipify.org?format=json', function(data) {

                ip = data.ip;

                new_context = session.user_context;
                self._rpc({
                        model: 'hr.employee',
                        method: 'attendance_manual',
                        args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
                        context: _.extend({}, new_context, {'ip': ip, 'latitude': latitude, 'longitude': longitude}),
                    })
                    .then(function(result) {
                        if (result.action) {
                            self.do_action(result.action);
                        } else if (result.warning) {
                            self.displayNotification({ title: result.warning, type: 'danger' });
                        }
                    });

            });

        },

    });

});