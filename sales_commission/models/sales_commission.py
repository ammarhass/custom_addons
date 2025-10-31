from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError
from datetime import date


class SalesCommissionPlan(models.Model):
    _name = 'salesperson.commission.plan'
    _description = 'Commission Plan'
    _order = 'id'
    _inherit = ['mail.thread']


    name = fields.Char()
    date_from = fields.Date()
    date_to = fields.Date()
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', "Draft"), ('approved', "Approved"), ('done', "Done"), ('cancel', "Cancelled")],
                             required=True, default='draft', tracking=True)
    line_ids = fields.One2many('sales.commission.line', 'plan_id')
    commission_time = fields.Boolean()
    last_calculated_date = fields.Date(string="Last Calculated On")
    commission_calculation_count = fields.Integer(string="Calculation Count", default=0)
    commission_detail_ids = fields.One2many('commission.details', 'plan_id', string="Commission Details")

    commission_details_count = fields.Integer(
        string="Commission Details Count",
        compute='_compute_commission_details_count'
    )

    def _compute_commission_details_count(self):
        for plan in self:
            plan.commission_details_count = self.env['commission.details'].search_count([
                ('plan_id', '=', plan.id)
            ])

    def action_view_commission_details(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Commission Details - {self.name}',
            'res_model': 'commission.details',
            'view_mode': 'list,form',
            'domain': [('plan_id', '=', self.id)],
            'context': {
                'default_plan_id': self.id,
                'create': False,
            },
            'target': 'current',
        }

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def action_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def create_commission(self):
        CommissionDetail = self.env['commission.details']

        for plan in self:
            if plan.state != 'approved':
                raise ValidationError(_("Commission can only be created for approved plans."))

            if not plan.date_from or not plan.date_to:
                raise ValidationError(_("Please set both start and end dates for the commission plan."))

            if plan.date_from > plan.date_to:
                raise ValidationError(_("End date cannot be before start date."))

            if not plan.line_ids:
                raise ValidationError(_("No commission lines configured for this plan."))

            existing_commissions = self.env['commission.details'].search([
                ('plan_id', '=', plan.id),
                ('date_from', '=', plan.date_from),
                ('date_to', '=', plan.date_to)
            ])

            if existing_commissions and not self._context.get('force_recalculate'):
                raise ValidationError(_(
                    "Commissions already created for this period. "
                    "Use force recalculate to regenerate."
                ))

            if self._context.get('force_recalculate') and existing_commissions:
                existing_commissions.unlink()

            employees = self.env['hr.employee'].search([
                ('commission_plan_id', '=', plan.id),
                ('active', '=', True)
            ])

            commission_created_count = 0
            skipped_employees = []

            for employee in employees:
                try:
                    if not employee.user_id:
                        skipped_employees.append(f"{employee.name} (No user account)")
                        continue

                    invoices = self.env['account.move'].search([
                        ('invoice_user_id', '=', employee.user_id.id),
                        ('state', '=', 'posted'),
                        ('move_type', 'in', ['out_invoice', 'out_refund']),
                        ('date', '>=', plan.date_from),
                        ('date', '<=', plan.date_to),
                        ('company_id', '=', plan.company_id.id)
                    ])

                    if not invoices:
                        skipped_employees.append(f"{employee.name} (No invoices in period)")
                        continue

                    total_positive = 0.0
                    total_negative = 0.0
                    for invoice in invoices:
                        if invoice.move_type == 'out_invoice':
                            total_positive += invoice.amount_untaxed
                        elif invoice.move_type == 'out_refund':
                            total_negative += invoice.amount_untaxed

                    total_amount = total_positive - total_negative

                    commission_line = None
                    for line in plan.line_ids.sorted(key=lambda l: l.target_from):
                        if line.target_from <= total_amount <= line.target_to:
                            commission_line = line
                            break

                    if not commission_line:
                        skipped_employees.append(
                            f"{employee.name} (No matching commission tier for amount {total_amount:.2f})")
                        continue

                    commission_amount = 0.0
                    if commission_line.commission_type == 'fixed':
                        commission_amount = commission_line.commission_amount
                    elif commission_line.commission_type == 'percentage':
                        commission_amount = total_amount * (commission_line.percentage_value)

                    commission_vals = {
                        'employee_id': employee.id,
                        'plan_id': plan.id,
                        'target_from': commission_line.target_from,
                        'target_to': commission_line.target_to,
                        'actual_sales_amount': total_amount,
                        'commission_amount': commission_amount,
                        'commission_rate': commission_line.commission_amount,
                        'commission_type': commission_line.commission_type,
                        'calculation_date': fields.Date.today(),
                        'state': 'calculated',
                        'company_id': plan.company_id.id,
                    }

                    CommissionDetail.create(commission_vals)
                    commission_created_count += 1

                except Exception as e:
                    skipped_employees.append(f"{employee.name} (Error: {str(e)})")
                    continue

            plan.write({
                'last_calculated_date': fields.Date.today(),
                'commission_calculation_count': plan.commission_calculation_count + 1
            })

            message = f"Successfully created {commission_created_count} commission records."
            if skipped_employees:
                message += f"\n\nSkipped {len(skipped_employees)} employees:\n• " + "\n• ".join(skipped_employees)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Commission Creation Complete'),
                    'message': message,
                    'type': 'success' if commission_created_count > 0 else 'warning',
                    'sticky': len(skipped_employees) > 0,
                    'next': {
                        'type': 'ir.actions.act_window_close'
                    }
                }
            }

    def process_commission_time(self):
        today = date.today()
        commission_plans = self.env['salesperson.commission.plan'].search([
            ('date_to', '=', today), ('state', '=', 'approved')
        ])
        if commission_plans:
            commission_plans.write({
                'commission_time': True
            })


class SalesCommissionLine(models.Model):
    _name = 'sales.commission.line'


    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    name = fields.Char()
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    target_from = fields.Monetary(currency_field='currency_id')
    target_to = fields.Monetary(currency_field='currency_id')
    commission_amount = fields.Monetary()
    commission_type = fields.Selection([
        ('fixed', "Fixed"),
        ('percentage', "Percentage")
    ])
    plan_id = fields.Many2one('salesperson.commission.plan')
    percentage_value = fields.Float()
