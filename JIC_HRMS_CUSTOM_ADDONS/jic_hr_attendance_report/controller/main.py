import base64

from odoo import http
from odoo.http import content_disposition, request


class BankRecoReport(http.Controller):
    @http.route(
        "/web/binary/jic_attendance_report",
        type="http",
        auth="user",
        sitemap=False,
    )
    def download_jic_attendance_report(self, wizard_id, **kw):
        model = request.env["hr.attendance.report.wizard"]
        case = model.browse(int(wizard_id))
        filename = "jic_report_attendance.xlsx"
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
