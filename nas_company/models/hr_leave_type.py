from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_permission = fields.Boolean(string="Is Permission",  )
    leave_validation_type = fields.Selection(
        selection_add=[  ('both_with_group', "By Employee's Approver and Time Off Officer and Group Time Off Approval")])