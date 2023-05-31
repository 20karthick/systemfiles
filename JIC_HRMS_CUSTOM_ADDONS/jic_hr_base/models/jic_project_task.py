# -*- coding: utf-8 -*-
import json

from lxml import etree
from odoo import api, fields, models, _


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Reason : This is to avoid editing project related fields
    # for all the users except project manager

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(ProjectTask, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        if view_type == 'form' and self.user_has_groups('project.group_project_user') and self.user_has_groups('employee_inherits.employee_project_admin'):
            doc = etree.XML(res['arch'], parser=None, base_url=None)

            # Fields to make readonly for project users only
            fields = ['project_id', 'user_ids', 'partner_id', 'tag_ids']

            for field in fields:
                for node in doc.xpath("//field[@name='%s']" % field):
                    node.set("readonly", "1")
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))

        else:
            if view_type == 'form' and not self.user_has_groups('project.group_project_manager'):
                doc = etree.XML(res['arch'], parser=None, base_url=None)

                # Fields to make readonly for project users only
                fields = ['project_id', 'user_ids', 'partner_id', 'tag_ids']

                for field in fields:
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set("readonly", "1")
                        modifiers = json.loads(node.get("modifiers"))
                        modifiers['readonly'] = True
                        node.set("modifiers", json.dumps(modifiers))

                res['arch'] = etree.tostring(doc)
        return res

