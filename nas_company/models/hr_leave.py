from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('request_date_from')
    def _check_leave_date_not_in_past(self):
        for leave in self:
            if self.env.company.nas_company:
                if self.env.company.allowed_days:
                    if leave.request_date_from:
                        if not self.env.user.has_group('nas_company.nas_access_leave_group'):
                            leave_date = fields.Date.from_string(leave.request_date_from)
                            today = fields.Date.context_today(self)
                            two_days_ago = today - timedelta(days=self.env.company.allowed_days)

                            if leave_date < two_days_ago:
                                raise ValidationError(
                                    "You cannot create a leave that starts more than 2 days in the past. "
                                    "The earliest allowed start date is %s." % two_days_ago
                                )
                if self.env.company.prevent_day:
                    if not self.env.user.has_group('nas_company.nas_access_leave_group'):
                        start_date = fields.Date.from_string(leave.request_date_from)
                        start_weekday = str(start_date.weekday())
                        if start_weekday == self.env.company.prevent_day:
                            raise ValidationError(
                                f"You cannot create a leave that starts on {self.env.company.prevent_day}. "
                                f"Selected start date {start_date} falls on a prevented day."
                            )
