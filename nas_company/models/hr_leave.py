from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, time
import pytz
from odoo.exceptions import UserError,AccessError



class HrLeave(models.Model):
    _inherit = 'hr.leave'

    is_permission = fields.Boolean(string="Is Permission", related="holiday_status_id.is_permission" )
    permission_slot = fields.Selection(
        [
            ('start', 'First 2 hours (start of day)'),
            ('end', 'Last 2 hours (end of day)'),
        ],
        string="Permission Slot",
        help="For Permission leaves: choose which 2-hour block to apply.",
    )

    def _get_responsible_for_approval(self):
        self.ensure_one()

        responsible = self.env['res.users']
        if self.validation_type == 'manager' or (
                self.validation_type in ['both', 'both_with_group'] and self.state == 'confirm'):
            if self.employee_id.leave_manager_id:
                responsible = self.employee_id.leave_manager_id
            elif self.employee_id.parent_id.user_id:
                responsible = self.employee_id.parent_id.user_id
        elif self.validation_type == 'hr' or (
                self.validation_type in ['both', 'both_with_group'] and self.state == 'validate1'):
            if self.holiday_status_id.responsible_ids:
                responsible = self.holiday_status_id.responsible_ids
        return responsible

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return

        current_employee = self.env.user.employee_id
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        is_group_approver = self.env.user.has_group('nas_company.group_hr_holidays_group_approval')

        for holiday in self:
            val_type = holiday.validation_type

            if not is_manager:
                if holiday.state == 'cancel' and state != 'confirm':
                    raise UserError(_('A cancelled leave cannot be modified.'))
                if state == 'confirm':
                    if holiday.state == 'refuse':
                        raise UserError(_('Only a Time Off Manager can reset a refused leave.'))
                    if holiday.date_from and holiday.date_from.date() <= fields.Date.today():
                        raise UserError(_('Only a Time Off Manager can reset a started leave.'))
                    if holiday.employee_id != current_employee:
                        raise UserError(_('Only a Time Off Manager can reset other people leaves.'))
                else:
                    if val_type == 'no_validation' and current_employee == holiday.employee_id and (
                            is_officer or is_manager or is_group_approver):
                        continue
                    # use ir.rule based first access check: department, members, ... (see security.xml)
                    holiday.check_access('write')

                    # This handles states validate1 validate and refuse
                    if holiday.employee_id == current_employee \
                            and self.env.user != holiday.employee_id.leave_manager_id \
                            and not is_officer \
                            and not is_group_approver:
                        raise UserError(
                            _('Only a Time Off Officer, Group Approver or Manager can approve/refuse its own requests.'))

                    if (state == 'validate1' and val_type in ['both', 'both_with_group']):
                        if not is_officer and not is_group_approver and self.env.user != holiday.employee_id.leave_manager_id:
                            raise UserError(
                                _('You must be either %s\'s manager, Time off Manager or Group Approver to approve this leave') % (
                                    holiday.employee_id.name))

                    if (state == 'validate' and val_type in ['manager', 'both_with_group']) \
                            and self.env.user != holiday.employee_id.leave_manager_id \
                            and not is_officer \
                            and not is_group_approver:
                        raise UserError(
                            _("You must be %s's Manager, Time Off Officer or Group Approver to approve this leave",
                              holiday.employee_id.name))

                    if not is_officer and not is_group_approver and (state == 'validate' and val_type == 'hr'):
                        raise UserError(
                            _('You must either be a Time off Officer, Group Approver or Time off Manager to approve this leave'))

    def _check_double_validation_rules(self, employees, state):
        if self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
            return

        is_leave_user = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_group_approver = self.env.user.has_group('nas_company.group_hr_holidays_group_approval')

        if state == 'validate1':
            employees = employees.filtered(lambda employee: employee.leave_manager_id != self.env.user)
            if employees and not is_leave_user and not is_group_approver:
                raise AccessError(
                    _('You cannot first approve a time off for %s, because you are not his time off manager, group approver or time off officer',
                      employees[0].name))
        elif state == 'validate' and not is_leave_user and not is_group_approver:
            # Is probably handled via ir.rule
            raise AccessError(_('You don\'t have the rights to apply second approval on a time off request'))

    def action_validate(self, check_state=True):
        current_employee = self.env.user.employee_id
        leaves = self._get_leaves_on_public_holiday()
        if leaves:
            raise ValidationError(
                _('The following employees are not supposed to work during that period:\n %s') % ','.join(
                    leaves.mapped('employee_id.name')))
        if check_state and any(
                holiday.state not in ['confirm', 'validate1'] and holiday.validation_type != 'no_validation' for holiday
                in self):
            raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})

        leaves_second_approver = self.env['hr.leave']
        leaves_first_approver = self.env['hr.leave']

        for leave in self:
            if leave.validation_type in ['both', 'both_with_group']:
                leaves_second_approver += leave
            else:
                leaves_first_approver += leave

        leaves_second_approver.write({'second_approver_id': current_employee.id})
        leaves_first_approver.write({'first_approver_id': current_employee.id})

        self._validate_leave_request()
        if not self.env.context.get('leave_fast_create'):
            self.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
        return True
    def _get_workday_bounds_for_date(self, employee, day_date):
        """Return (first_interval_start, last_interval_end) as **naive UTC** datetimes
        for the employee's calendar on given date. Internally uses tz-aware UTC.
        """
        self.ensure_one()
        calendar = employee.resource_calendar_id or employee.company_id.resource_calendar_id
        if not calendar or not employee.resource_id:
            return (False, False)

        # Build aware UTC bounds for the calendar API
        start_aware = datetime.combine(day_date, time.min).replace(tzinfo=pytz.UTC)
        end_aware = datetime.combine(day_date, time.max).replace(tzinfo=pytz.UTC)

        intervals_map = calendar._work_intervals_batch(
            start_aware, end_aware, resources=employee.resource_id
        )
        intervals = intervals_map.get(employee.resource_id.id)
        if not intervals:
            return (False, False)

        # Robustly extract first start and last end from WorkIntervals:
        def _iter_intervals(itvls):
            # Prefer the public iterator
            for item in itvls:
                # item can be (start, stop, data) or an object with attributes
                start = getattr(item, 'start', None)
                stop = getattr(item, 'stop', None)
                if start is None or stop is None:
                    # assume tuple-like
                    start, stop = item[0], item[1]
                yield start, stop

        first_start = None
        last_end = None
        for s, e in _iter_intervals(intervals):
            if first_start is None:
                first_start = s
            last_end = e

        if not first_start or not last_end:
            return (False, False)

        # Convert aware→naive UTC for writing on fields / comparisons
        def _naive_utc(dt):
            return dt.astimezone(pytz.UTC).replace(tzinfo=None)

        return _naive_utc(first_start), _naive_utc(last_end)

    @api.onchange('is_permission', 'permission_slot', 'employee_id', 'request_date_from')
    def _onchange_permission_times(self):
        for leave in self:
            if not leave.is_permission or not leave.employee_id or not leave.request_date_from:
                continue

            leave.request_unit_half = False
            leave.request_unit_hours = True

            start_dt, end_dt = leave._get_workday_bounds_for_date(
                leave.employee_id, leave.request_date_from  # request_date_from is already a date
            )
            if not start_dt or not end_dt:
                leave.date_from = False
                leave.date_to = False
                continue

            two_hours = timedelta(hours=2)
            if (end_dt - start_dt) < two_hours:
                leave.date_from = False
                leave.date_to = False
                continue

            slot = leave.permission_slot or 'start'
            if slot == 'start':
                leave.date_from = start_dt  # naive UTC
                leave.date_to = start_dt + two_hours
            else:
                leave.date_to = end_dt  # naive UTC
                leave.date_from = end_dt - two_hours

    @api.constrains('is_permission', 'date_from', 'date_to', 'permission_slot', 'employee_id')
    def _check_permission_two_hours_edges(self):
        two_hours = timedelta(hours=2)

        for leave in self:
            if not leave.is_permission:
                continue
            if not leave.employee_id or not leave.date_from or not leave.date_to:
                raise ValidationError(_("Permission leave requires employee and time interval."))

            # Calculate the duration
            duration = leave.date_to - leave.date_from

            # Check if duration is GREATER than 2 hours (not allowed)
            if duration > two_hours:
                raise ValidationError(_("Permission leave cannot exceed 2 hours."))

            # Both edges we compute are **naive UTC**, matching leave.date_from/to
            start_edge, end_edge = leave._get_workday_bounds_for_date(
                leave.employee_id, leave.date_from.date()
            )
            if not start_edge or not end_edge:
                raise ValidationError(_("Employee has no working hours on this date."))

            if leave.permission_slot == 'start' or not leave.permission_slot:
                # For start slot: must start at work start and end within first 2 hours
                if not (leave.date_from == start_edge and leave.date_to <= start_edge + two_hours):
                    raise ValidationError(
                        _("Start-slot Permission must be within the first 2 hours of the working day."))
            else:  # 'end'
                # For end slot: must end at work end and start within last 2 hours
                if not (leave.date_to == end_edge and leave.date_from >= end_edge - two_hours):
                    raise ValidationError(_("End-slot Permission must be within the last 2 hours of the working day."))

    @api.model_create_multi
    def create(self, vals_list):
        # Normalize on create as well (in case created by RPC/import and not using the form onchange)
        records = super().create(vals_list)
        for rec in records:
            if rec.is_permission:
                # Use context to avoid recursion
                if not self.env.context.get('skip_permission_processing'):
                    # Call onchange without triggering write again
                    rec_with_context = rec.with_context(skip_permission_processing=True)
                    rec_with_context._onchange_permission_times()
        return records

    def write(self, vals):
        # Check if we're already processing permission logic to avoid recursion
        if self.env.context.get('skip_permission_processing'):
            return super().write(vals)

        # Process permission logic only once
        permission_leaves = self.filtered(lambda l: l.is_permission)
        if permission_leaves and any(field in vals for field in
                                     ['is_permission', 'permission_slot', 'employee_id', 'request_date_from',
                                      'date_from', 'date_to']):
            # First write without processing
            result = super().write(vals)

            # Then process permission logic without triggering write again
            for leave in permission_leaves:
                leave.with_context(skip_permission_processing=True)._onchange_permission_times()

            return result
        else:
            return super().write(vals)

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
                # if self.env.company.prevent_day:
                #     if not self.env.user.has_group('nas_company.nas_access_leave_group'):
                #         start_date = fields.Date.from_string(leave.request_date_from)
                #         start_weekday = str(start_date.weekday())
                #         if start_weekday == self.env.company.prevent_day:
                #             raise ValidationError(
                #                 f"You cannot create a leave that starts on {self.env.company.prevent_day}. "
                #                 f"Selected start date {start_date} falls on a prevented day."
                #             )
