from odoo import models, fields, api


class HrEmployeeQualification(models.Model):
    _name = "hr.employee.qualification"

    def _get_year_of_passing(self):
        year_list = []
        for i in range(1920, int(fields.Date.today().year) + 1):
            year_list.append((i,i))
        return year_list

    name = fields.Char(string="Qualification", required=True)
    subject_id = fields.Many2one("hr.employee.qualification.subject", string="Subject", required=True)
    institution_id = fields.Many2one("hr.employee.qualification.institution", string="Institution", required=True)
    university_id = fields.Many2one("hr.employee.qualification.university", string="University", required=True)
    year_of_passing = fields.Selection(selection=_get_year_of_passing, string="Year of Passing")
    doc_attachment_ids = fields.Many2many('ir.attachment', 'employee_qualification_attach_rel', 'emp_qualification_id', 'attach_id', string="Attachment",
                                         help='You can attach the copy of your document', copy=False)
    employee_id = fields.Many2one("hr.employee", string="Employee", ondelete="cascade")


class HrEmployeeQualificationSubject(models.Model):
    _name = "hr.employee.qualification.subject"

    name = fields.Char(string="Subject", required=True)


class HrEmployeeQualificationInstitution(models.Model):
    _name = "hr.employee.qualification.institution"

    name = fields.Char(string="Institution", required=True)


class HrEmployeeQualificationUniversity(models.Model):
    _name = "hr.employee.qualification.university"

    name = fields.Char(string="University", required=True)