import json
import logging
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.project.controllers.portal import ProjectCustomerPortal

_logger = logging.getLogger(__name__)


class TindexPortalProject(ProjectCustomerPortal):

    def _task_get_page_view_values(self, task, access_token, **kwargs):
        values = super(TindexPortalProject, self)._task_get_page_view_values(task, access_token, **kwargs)
        values["available_stages"] = self._return_portal_available_stages(task)
        values["user_can_see_edit"] = self._is_allowed_user_can_edit(task)
        # location_data = task.action_view_location()
        task_location_url = ""
        # if isinstance(location_data, dict):
        #     task_location_url = location_data.get("url", "")
        # values["task_location_url"] = task_location_url
        return values

    def _is_allowed_user_can_edit(self, task):
        if not task:
            return False

        return task.task_type_id.user_can_edit

    @staticmethod
    def _return_portal_available_stages(task):
        if not task.stage_id:
            return request.env['project.task.type'].sudo().search([
                ('is_equipment_stage', '=', True)
            ]).filtered(lambda s: task.parent_id.project_id.id in s.project_ids.ids)
        return task.stage_id.allow_stage_ids


    @http.route(['/my/task/edit/<int:task_id>'], type='http', auth="public", website=True)
    def portal_edit_my_task(self, task_id, access_token=None, **kw):
        if not request.env.user.partner_id:
            raise request.NotFound()
        try:
            task_sudo = self._document_check_access('project.task', task_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if request.httprequest.method == 'GET':
            values = self._task_get_page_view_values(task_sudo, access_token, **kw)
            values["available_stages"] = self._return_portal_available_stages(task_sudo)
            return request.render("nas_company.edit_task_portal", values)
        elif request.httprequest.method == 'POST':
            error_list = []
            new_stage = kw.get("new_stage_id") and int(kw.get("new_stage_id"))
            new_stage_sudo = task_sudo.stage_id.search([
                ("id", "=", new_stage)
            ])
            if new_stage_sudo.mandatory_message and not kw.get("message"):
                error_list.append("Please add a message")
            if not error_list:

                if new_stage_sudo:
                    try:
                        admin_user = request.env.ref('base.user_admin')
                        portal_user = request.env.user
                        task_sudo.with_user(portal_user).with_context(skip_check_users=True).write(
                            {"stage_id": new_stage_sudo.id})
                        if kw.get("message"):
                            task_sudo.message_post(body=kw.get("message"),
                                                     author_id=task_sudo.partner_id.id,
                                                     message_type='comment', subtype_id=1)

                    except Exception as e:
                        _logger.error("Error while changing stage on portal: {}".format(str(e)))
                        task_sudo.sudo().write({"stage_id": new_stage_sudo.id})
                url = f'/my/task/{task_sudo.id}'
                return request.redirect(url)
            else:
                values = self._task_get_page_view_values(task_sudo, access_token, **kw)
                values['task'] = request.env['project.task'].sudo().browse(task_id)
                values['error_list'] = error_list
                return request.render("nas_company.edit_task_portal", values)

