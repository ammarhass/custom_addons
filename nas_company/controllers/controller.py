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
        # allowed_users_ids = task.stage_id.get_allow_users()
        # if not allowed_users_ids:
        #     allowed_users_ids = []
        # if (not task.stage_id and request.env.user.has_group('project.group_project_manager')) \
        #         or (request.env.user.id in allowed_users_ids
        #             and request.env.user.has_group('project.group_project_manager')) \
        #         or (request.env.user.id in allowed_users_ids and task.stage_id.allow_stage_ids and
        #             request.env.user in task.user_ids):
            return True

    @staticmethod
    def _return_portal_available_stages(task):
        if not task.stage_id:
            return request.env['project.task.type'].sudo().search([

            ])


    @http.route(['/my/task/edit/<int:task_id>'], type='http', auth="public", website=True)
    def portal_edit_my_task(self, task_id, access_token=None, **kw):
        if not request.env.user.partner_id:
            raise request.NotFound()
        try:
            task_sudo = self._document_check_access('project.task', task_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if request.httprequest.method == 'GET':
            # ensure attachment are accessible with access token inside template
            for attachment in task_sudo.attachment_ids:
                attachment.generate_access_token()
            values = self._task_get_page_view_values(task_sudo, access_token, **kw)
            values["available_stages"] = self._return_portal_available_stages(task_sudo)
            return request.render("tindex_equipment_installation.edit_task_portal", values)
        elif request.httprequest.method == 'POST':
            new_stage = kw.get("new_stage_id") and int(kw.get("new_stage_id"))
            new_stage_sudo = task_sudo.stage_id.search([
                ("id", "=", new_stage)
            ])
            if new_stage_sudo:
                try:
                    admin_user = request.env.ref('base.user_admin')
                    task_sudo.with_user(admin_user).with_context(skip_check_users=True).write(
                        {"stage_id": new_stage_sudo.id})
                except Exception as e:
                    _logger.error("Error while changing stage on portal: {}".format(str(e)))
                    task_sudo.sudo().with_context(skip_check_users=True).write({"stage_id": new_stage_sudo.id})
            url = f'/my/task/{task_sudo.id}'
            return request.redirect(url)
