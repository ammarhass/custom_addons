from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class InvoiceReminderTracker(models.Model):
    _name = 'invoice.reminder.tracker'
    _description = 'Invoice Reminder Tracking'

    invoice_id = fields.Many2one('account.move', string='Invoice', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='invoice_id.partner_id', string='Customer')
    invoice_date = fields.Date(related='invoice_id.invoice_date')
    due_date = fields.Date(related='invoice_id.invoice_date_due')
    amount_total = fields.Monetary(related='invoice_id.amount_total')
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id')
    residual = fields.Monetary(related='invoice_id.amount_residual')
    state = fields.Selection(related='invoice_id.state')

    # Tracking fields
    pre_due_sent = fields.Boolean(default=False)
    invoice_issued_sent = fields.Boolean(default=False)
    week1_reminder_sent = fields.Boolean(default=False)
    week2_reminders_count = fields.Integer(default=0)
    last_week2_reminder = fields.Date()
    escalation_reminders_count = fields.Integer(default=0)
    last_escalation_reminder = fields.Date()
    payment_confirmation_sent = fields.Boolean(default=False)

    # Recipient groups
    initial_recipient_ids = fields.Many2many('res.users', string='Initial Recipients (3)')
    escalation_recipient_ids = fields.Many2many('res.users', string='Escalation Recipients (6)', relation='Users')

    # Status
    is_active = fields.Boolean(default=True)