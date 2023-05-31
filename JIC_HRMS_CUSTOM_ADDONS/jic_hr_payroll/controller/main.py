import base64

from odoo import http
from odoo.http import content_disposition, request


class PayrollDiagnosis(http.Controller):

    @http.route(
        "/web/binary/jic_payroll_diagnosis",
        type="http",
        auth="user",
        sitemap=False,
    )
    def download_jic_diagnosis_report(self, wizard_id, **kw):
        print("---------------------------------->>")
        model = request.env["hr.payroll.diagnosis"]
        case = model.browse(int(wizard_id))
        print("Case-------------------------------", case)
        filename = "jic_report_payroll_diagnosis.xlsx"
        if case and case.report_file:
            file_data = base64.b64decode(case.report_file)
            return request.make_response(
                file_data,
                headers=[
                    ("Content-Disposition", content_disposition(filename)),
                    ("Content-Type", "application/vnd.ms-excel"),
                    ("Content-Length", len(filename)),
                ],
                cookies={"fileToken": ""},
            )