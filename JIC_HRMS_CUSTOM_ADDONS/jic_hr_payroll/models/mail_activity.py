from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def validation_mark_as_discard(self, activity, context):
        if context and context.get("activity_log_status", False) == "discard":
            child_user_ids = self.env.user.child_ids.ids
            if (
                activity.user_id.id != self.env.uid
                and activity.user_id.id not in child_user_ids
            ):
                raise ValidationError(_("You are not allowed to Mark this as Discarded"))

        # if activity.res_model == 'hr.employee.input.requests':
        #     input_request_id = self.env[activity.res_model].browse(activity.res_id)
        #     input_request_id.action_reject()

    def validation_mark_as_done(self, activity, context):
        child_user_ids = self.env.user.child_ids.ids
        if (
                activity.user_id.id != self.env.uid
                and activity.user_id.id not in child_user_ids
        ):
            raise ValidationError(_("You are not allowed to Mark this as Discarded"))

        # if activity.res_model == 'hr.employee.input.requests':
        #     input_request_id = self.env[activity.res_model].browse(activity.res_id)
        #     input_request_id.action_approve()

    def _action_done(self, feedback=False, attachment_ids=None):
        for activity in self:
            context_vals = self.env.context or {}
            # Validation on mark as discard
            #self.validation_mark_as_discard(activity, context_vals)

            # Validation on mark as done
            #self.validation_mark_as_done(activity, context_vals)

        return super(MailActivity, self)._action_done(feedback=False, attachment_ids=None)

