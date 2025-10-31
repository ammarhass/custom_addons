from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError
from datetime import date


class CommissionDetails(models.Model):
    _name = 'commission.details'
    _description = 'Commission Details'
    _order = 'calculation_date desc'

    name = fields.Char(string="Reference", compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', required=True)
    user_id = fields.Many2one('res.users', related='employee_id.user_id', store=True)
    plan_id = fields.Many2one('salesperson.commission.plan', string="Commission Plan")

    date_from = fields.Date(string="Period From", related='plan_id.date_from', store=True)
    date_to = fields.Date(string="Period To", related='plan_id.date_to', store=True)

    target_from = fields.Monetary(currency_field='currency_id')
    target_to = fields.Monetary(currency_field='currency_id')
    actual_sales_amount = fields.Monetary(currency_field='currency_id', string="Actual Sales")
    commission_amount = fields.Monetary(currency_field='currency_id')
    commission_rate = fields.Float(string="Commission Rate")
    commission_type = fields.Selection([
        ('fixed', "Fixed"),
        ('percentage', "Percentage")
    ], string="Type")

    invoice_count = fields.Integer(compute='_compute_invoice_data', string="Number of Invoices")

    calculation_date = fields.Date(default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], default='draft', string="Status")

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    @api.depends('employee_id', 'calculation_date')
    def _compute_name(self):
        for record in self:
            if record.employee_id and record.calculation_date:
                record.name = f"COMM/{record.employee_id.name}/{record.calculation_date.strftime('%Y%m')}"
            else:
                record.name = "New Commission"

    def _compute_invoice_data(self):
        for record in self:
            if record.employee_id and record.employee_id.user_id and record.date_from and record.date_to:
                invoices = self.env['account.move'].search([
                    ('invoice_user_id', '=', record.employee_id.user_id.id),
                    ('state', '=', 'posted'),
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('date', '>=', record.date_from),
                    ('date', '<=', record.date_to),
                    ('company_id', '=', record.company_id.id)
                ])
                record.invoice_count = len(invoices)
            else:
                record.invoice_count = 0

    def action_view_invoices(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([
            ('invoice_user_id', '=', self.employee_id.user_id.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id)
        ])

        return {
            'type': 'ir.actions.act_window',
            'name': f'Invoices - {self.employee_id.name}',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {'create': False},
        }