from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from odoo.fields import Command

class ProjectTask(models.Model):
    _inherit = 'project.task'

    team_id = fields.Many2one('employee.team')
    unit_id = fields.Many2one('task.unit.type')
    task_type_id = fields.Many2one('task.type')
    quantity = fields.Integer()
    percentage = fields.Float(string="Percentage %", required=False)
    note_entered = fields.Boolean()
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True)

    cost_line_ids = fields.One2many(
        'project.task.cost.line', 'task_id',
        string="Assignee Costs", compute='_compute_cost_lines', store=True)

    reference_number = fields.Char(
        'Reference', default=lambda self: self.env['ir.sequence'].next_by_code('project.task'))

    @api.onchange('task_type_id')
    def onchange_percentage(self):
        for rec in self:
            rec.percentage = rec.task_type_id.percentage

    def _map_user_to_employee(self, user):
        """Better employee mapping that handles various cases"""
        if not user:
            return self.env['hr.employee']

        # Method 1: Direct user-employee link
        employee = self.env['hr.employee'].search([
            ('user_id', '=', user.id)
        ], limit=1)

        if employee:
            return employee

        # Method 2: Try to find by name or other criteria if direct link doesn't exist
        employee = self.env['hr.employee'].search([
            ('name', 'ilike', user.name)
        ], limit=1)

        return employee

    def _get_employee_avg_monthly_salary(self, employee):
        """Average payslip 'NET' (fallback: sum lines) across last 4 months."""
        if not employee:
            return 0.0
        today = fields.Date.context_today(self)
        start = today + relativedelta(months=-4, day=1)
        slips = self.env['hr.payslip'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'done'),
            ('date_from', '>=', start),
            ('date_to', '<=', today),
        ])
        if not slips:
            return 0.0
        totals = []
        for s in slips:
            net = sum(s.line_ids.filtered(lambda l: l.code == 'NET').mapped('total'))
            if not net:
                net = sum(s.line_ids.mapped('total'))
            totals.append(net)
        return (sum(totals) / len(totals)) if totals else 0.0

    @api.depends('user_ids', 'quantity', 'percentage', 'task_type_id')
    def _compute_cost_lines(self):
        for task in self:
            cmds = [Command.clear()]  # safely removes old lines
            for user in task.user_ids:
                employee = task._map_user_to_employee(user)
                avg_monthly = task._get_employee_avg_monthly_salary(employee)
                avg_daily = (avg_monthly / 30.0) if avg_monthly else 0.0

                # formula you confirmed
                cost = (task.quantity or 0) * avg_daily * ((task.percentage or 0.0) / 100.0)

                cmds.append(Command.create({
                    'user_id': user.id,
                    'employee_id': employee.id or False,
                    'quantity': task.quantity,
                    'percentage': task.percentage,
                    'currency_id': task.company_currency_id.id,
                    'avg_monthly_salary_4m': avg_monthly,
                    'avg_daily_cost': avg_daily,
                    'avg_task_cost': cost,
                }))
            # assign all children in one go; ORM will create them after parent is saved
            task.cost_line_ids = cmds

    def write(self, vals):
        for task in self:
            if not task.task_type_id.user_can_edit:
                if 'stage_id' in vals and vals['stage_id'] != task.stage_id.id:
                    if not task.note_entered:
                        raise ValidationError("You must add a note before changing the stage.")
                    vals['note_entered'] = False
                    mail_template = self.env.ref('nas_company.send_update_task_mail')
                    mail_template.send_mail(self.id, force_send=True, email_values={'res_id': self.id})

            else:
                if 'stage_id' in vals and vals['stage_id'] != task.stage_id.id:
                    allowed_user = self.env['res.users'].search([('partner_id', '=', task.partner_id.id)])
                    if not allowed_user or allowed_user != self.env.user:
                        raise ValidationError(
                            "You are not allowed to change the stage for this task."
                        )
                    # mail_template = self.env.ref('nas_company.send_update_task_mail')
                    # mail_template.send_mail(self.id, force_send=True, email_values={'res_id': self.id})


        return super(ProjectTask, self).write(vals)


    def open_note_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Stage',
            'res_model': 'task.note.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
            },
        }



    @api.constrains('quantity', 'task_type_id')
    def _check_quantity(self):
        for record in self:
            if record.quantity:
                if record.task_type_id and record.task_type_id.calendar:
                    allowed_values = [3, 6, 9, 12, 15, 18, 21, 24]
                    if record.quantity not in allowed_values:
                        raise ValidationError(
                            f"When calendar is enabled, quantity must be one of: {', '.join(map(str, allowed_values))}"
                        )
                else:
                    if record.quantity < 1 or record.quantity > 15:
                        raise ValidationError("Quantity must be between 1 and 15 when calendar is not enabled")


class TaskUnitType(models.Model):
    _name = 'task.unit.type'

    name = fields.Char()


class TaskType(models.Model):
    _name = 'task.type'

    name = fields.Char()
    calendar = fields.Boolean()
    user_can_edit = fields.Boolean()
    percentage = fields.Float(string="Percentage %",  required=False, )
class ProjectTaskCostLine(models.Model):
    _name = 'project.task.cost.line'
    _description = 'Task Cost per Assignee'
    _order = 'id'

    task_id = fields.Many2one('project.task', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', string="User", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)

    quantity = fields.Integer(string="Quantity", readonly=True)
    percentage = fields.Float(string="Percentage %", readonly=True)

    currency_id = fields.Many2one('res.currency', string="Currency",)
    avg_monthly_salary_4m = fields.Monetary(string="Avg monthly salary (4m)", currency_field='currency_id', readonly=True)
    avg_daily_cost = fields.Monetary(string="Avg cost / day", currency_field='currency_id', readonly=True)
    avg_task_cost = fields.Monetary(string="Avg cost of task", currency_field='currency_id', readonly=True)