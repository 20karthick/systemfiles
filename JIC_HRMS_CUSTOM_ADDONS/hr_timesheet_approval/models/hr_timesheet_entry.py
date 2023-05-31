# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import MissingError, UserError, ValidationError, AccessError
from odoo.osv import expression
from datetime import datetime, timedelta


class HrTimesheetEntry(models.Model):
    """
    Employee timesheet management temporary table
    """
    _name = 'hr.timesheet.entry'
    _inherit = ['mail.thread']
    _order = 'date desc'

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    @api.model
    def _default_employee(self):
        user_id = self.env.context.get('user_id', self.env.user.id)
        employee_id = self.env['hr.employee'].search(
            [('user_id', '=', user_id)],
            limit=1)
        if not employee_id:
            raise AccessError(_("You have no employee linked with."))
        return employee_id.id

    def _domain_project_id(self):
        domain = [('allow_timesheets', '=', True),('avoid_manual_timesheet', '=', False)]
        if not self.user_has_groups('hr_timesheet.group_timesheet_manager'):
            return expression.AND([domain,
                ['|', ('privacy_visibility', '!=', 'followers'), ('message_partner_ids', 'in', [self.env.user.partner_id.id])]
            ])
        return domain

    name = fields.Text('Description', required=True)
    date = fields.Date('Date', required=True, index=True, default=fields.Date.context_today, tracking=True)
    amount = fields.Monetary('Amount', required=True, default=0.0)
    unit_amount = fields.Float('Quantity', default=0.0, required=True, tracking=True)
    account_id = fields.Many2one('account.analytic.account', 'Analytic Account', required=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True, store=True,
                                  compute_sudo=True)
    group_id = fields.Many2one('account.analytic.group', related='account_id.group_id', store=True, readonly=True,
                               compute_sudo=True)

    task_id = fields.Many2one(
        'project.task', 'Task', required=True, index=True,
        domain="[('company_id', '=', company_id), ('project_id.allow_timesheets', '=', True), ('project_id', '=?', project_id)]")
    project_id = fields.Many2one(
        'project.project', 'Project', readonly=False, domain=_domain_project_id)
    user_id = fields.Many2one("res.users", default=_default_user, store=True, readonly=False, tracking=True)
    employee_id = fields.Many2one('hr.employee', "Employee", default=_default_employee, context={'active_test': False})
    department_id = fields.Many2one('hr.department', "Department", compute='_compute_department_id', store=True,
                                    compute_sudo=True)
    encoding_uom_id = fields.Many2one('uom.uom', compute='_compute_encoding_uom_id')
    partner_id = fields.Many2one('res.partner', compute='_compute_partner_id', store=True, readonly=False)
    state = fields.Selection(
        [
            ('draft','Draft'),('submitted','Submitted'),('approved','Approved')
        ], default='draft', string="Status", required=True, tracking=True
    )
    weekday = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string="Weekday", compute="_get_weekday", store=True)
    account_analytic_line_id = fields.Many2one("account.analytic.line", string="Timesheet Entry")

    # Computed methods

    @api.depends('user_id')
    def _compute_employee_id(self):
        for rec in self:
            if rec.user_id:
                employee_id = self.env['hr.employee'].search(
                    [('user_id', '=', rec.user_id.id)],
                    limit=1).id
                rec.employee_id = employee_id.id

    def _compute_encoding_uom_id(self):
        for analytic_line in self:
            analytic_line.encoding_uom_id = analytic_line.company_id.timesheet_encode_uom_id

    @api.depends('task_id.partner_id', 'project_id.partner_id')
    def _compute_partner_id(self):
        for timesheet in self:
            if timesheet.project_id:
                if timesheet.task_id.partner_id:
                    timesheet.partner_id = timesheet.task_id.partner_id.id
                elif timesheet.project_id.partner_id:
                    timesheet.partner_id = timesheet.project_id.partner_id.id
                else:
                    timesheet.partner_id = False
            else:
                timesheet.partner_id = False

    @api.onchange('project_id')
    def _onchange_project_id(self):
        # TODO KBA in master - check to do it "properly", currently:
        # This onchange is used to reset the task_id when the project changes.
        # Doing it in the compute will remove the task_id when the project of a task changes.
        if self.project_id != self.task_id.project_id:
            self.task_id = False

    @api.depends('employee_id')
    def _compute_department_id(self):
        for line in self:
            line.department_id = line.employee_id.department_id

    @api.depends("date")
    def _get_weekday(self):
        for rec in self:
            if rec.date:
                rec.weekday = str(rec.date.weekday())

    # Custom methods

    def validate_access_rights_approval(self):
        """
        This method will validate the action before execution in case of approval.
        :return:
        """
        for rec in self:
            if not self.user_has_groups(
                    'hr_timesheet.group_hr_timesheet_approver, hr_timesheet.group_timesheet_manager'
            ) and self.env.user.id != rec.project_id.user_id.id and not self.env.su:
                raise ValidationError(
                    _("You cannot approve/reject this timesheet")
                )

            if not rec.employee_id:
                raise ValidationError(
                    _("You cannot do this type of action to timesheet without employee mapped")
                )
        return True

    def validate_access_rights_submit(self):
        """
        Do check here before submit the sheet
        :return:
        """

    def create_timesheet_entry(self):
        time_line = self.env['account.analytic.line']
        for time_sheet in self:
            line_id = time_line.create({
                'name': time_sheet.name,
                'date': time_sheet.date,
                'task_id': time_sheet.task_id.id,
                'user_id': time_sheet.user_id.id or self.env.user.id,
                'project_id': time_sheet.project_id.id,
                'unit_amount': time_sheet.unit_amount,
                'employee_id': time_sheet.employee_id.id,
                'encoding_uom_id': time_sheet.encoding_uom_id.id,
                'timesheet_entry_id': time_sheet.id
            })
            time_sheet.account_analytic_line_id = line_id.id

    # Button Methods
    def action_submit(self):
        """
        1. Submit timesheet
        :return: True
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('You cannot submit time sheet other than "Draft" state'))

            rec.validate_access_rights_submit()

            rec.state = 'submitted'
        return True

    def action_approve(self):
        """
        1. Approve the timesheet and validate it
        :return:
        """
        for rec in self:
            if rec.state != 'submitted':
                raise ValidationError(_('Time sheet must be in "Submitted" state to approve'))

            rec.validate_access_rights_approval()

            # Create timesheet entry
            if rec.account_analytic_line_id:
                raise ValidationError(_("Timesheet entry already validated against this record %s")%(rec.name))

            rec.create_timesheet_entry()

            rec.state = 'approved'

        return True

    def action_draft(self):
        """
        1. Move the record to draft stage
        :return:
        """
        for rec in self:
            if rec.account_analytic_line_id:
                rec.account_analytic_line_id.unlink()

            rec.validate_access_rights_approval()

            rec.state = "draft"

        return True

    def action_open_task(self):
        """
        This is to open the task form view
        :return:
        """
        view_id = self.env.ref('project.view_task_form2').id

        if not self.task_id:
            raise ValidationError(_("There is no tasks lined with this record or the task has been deleted"))

        context = self._context.copy()

        return {
            'name': 'Task',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id, 'form')],
            'res_model': 'project.task',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': self.task_id.id,
            'target': 'new',
            'context': context,
        }


    # ORM Methods

    def write(self, values):
        # If it's a basic user then check if the timesheet is his own.
        if not self.user_has_groups('hr_timesheet.group_hr_timesheet_user') and not self.user_has_groups('employee_inherits.employee_project_admin'):
            if not (self.user_has_groups('hr_timesheet.group_hr_timesheet_approver') or self.env.su) and\
                    any(self.env.user.id != analytic_line.user_id.id for analytic_line in self):
                raise AccessError(_("You cannot access time sheets that are not yours."))

        if 'name' in values and not values.get('name'):
            values['name'] = '/'
        result = super(HrTimesheetEntry, self).write(values)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(HrTimesheetEntry, self).create(vals_list)
        return lines

    def unlink(self):
        for line in self:
            if self.env.context.get('admin_timesheet_unlink'):
                continue
            print("----------------------_>>", self.env.context.get('admin_timesheet_unlink'))
            if line.state not in ["draft", "submitted"]:
                raise AccessError(_("You cannot delete this record as it is approved. "
                                    "Cancel the record and try again"))
        return super(HrTimesheetEntry, self).unlink()


class AccountAnalyticLine(models.Model):

    _inherit = 'account.analytic.line'

    timesheet_entry_id = fields.Many2one("hr.timesheet.entry", string="Timesheet Entry")

    def unlink(self):
        for line in self:
            if self.user_has_groups('hr_timesheet.group_timesheet_manager') or \
                self.user_has_groups('hr_timesheet.group_hr_timesheet_approver'):
                if line.timesheet_entry_id:
                    line.timesheet_entry_id.with_context({'admin_timesheet_unlink': True}).unlink()
            elif line.timesheet_entry_id:
                raise AccessError(_("You cannot delete this record as it is linked with timesheet log. "
                                    "You can delete this from that record"))
            else:
                continue
        return super(AccountAnalyticLine, self).unlink()


class ProjectTask(models.Model):

    _inherit = 'project.task'

    @api.depends('timesheet_entry_ids.unit_amount')
    def _compute_unapproved_hours(self):
        for task in self:
            task.unapproved_hours = round(sum(task.timesheet_entry_ids.filtered(
                lambda a: a.state == 'submitted'
            ).mapped('unit_amount')), 2)

    @api.model
    def _default_planned_start(self):
        return fields.Datetime.now()

    @api.model
    def _default_planned_stop(self):
        return fields.Datetime.now() + timedelta(hours=1)

    @api.onchange('date_deadline')
    def onchange_deadline(self):
        for rec in self:
            my_time = datetime.min.time()
            if rec.date_deadline:
                rec.planned_stop = datetime.combine(rec.date_deadline, my_time)

    def do_log_timesheet(self):
        view_id = self.env.ref('hr_timesheet_approval.hr_timesheet_entry_lite_form').id

        context = {}
        context.update(
            {
                'default_task_id': self.id,
                'default_project_id': self.project_id and self.project_id.id,
            }
        )
        return {
            'name': 'Timesheet',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id, 'form')],
            'res_model': 'hr.timesheet.entry',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'flags': {'form': {'action_buttons': False}}
        }

    timesheet_entry_ids = fields.One2many("hr.timesheet.entry", "task_id", string="Timesheet Entry",
                                          domain=[('state','in',['submitted','draft'])])
    unapproved_hours = fields.Float(string="Unapproved Hours", compute="_compute_unapproved_hours", store=True)

    planned_start = fields.Datetime(string="Planned Start Time", default=_default_planned_start)
    planned_stop = fields.Datetime(string="Planned Stop Time", default=_default_planned_stop)


class ProjectProject(models.Model):

    _inherit = 'project.project'

    avoid_manual_timesheet = fields.Boolean(string="Avoid Manual Timesheet",
                                            help="This is to avoid listing from timesheet entry")