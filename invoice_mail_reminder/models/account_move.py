from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    reminder_tracker_id = fields.Many2one('invoice.reminder.tracker', string='Reminder Tracker', ondelete='cascade')
    days_overdue = fields.Integer(compute='_compute_days_overdue', store=True)

    @api.depends('invoice_date_due', 'state')
    def _compute_days_overdue(self):
        today = fields.Date.today()
        for invoice in self:
            if invoice.invoice_date_due and invoice.state == 'posted' and invoice.move_type == 'out_invoice':
                due_date = invoice.invoice_date_due
                invoice.days_overdue = (today - due_date).days if today > due_date else 0
            else:
                invoice.days_overdue = 0

    def create_reminder_tracker(self):
        for invoice in self:
            if invoice.move_type == 'out_invoice' and invoice.state == 'posted':
                # Define recipient groups (you can configure these)
                initial_users = self.env['res.users'].search([('groups_id', 'in', [
                    self.env.ref('account.group_account_manager').id,
                    self.env.ref('account.group_account_user').id
                ])], limit=3)

                escalation_users = self.env['res.users'].search([('groups_id', 'in', [
                    self.env.ref('account.group_account_manager').id,
                    self.env.ref('account.group_account_user').id
                ])], limit=6)

                tracker = self.env['invoice.reminder.tracker'].create({
                    'invoice_id': invoice.id,
                    'initial_recipient_ids': [(6, 0, initial_users.ids)],
                    'escalation_recipient_ids': [(6, 0, escalation_users.ids)],
                })
                invoice.reminder_tracker_id = tracker.id

    def get_first_reminder_recipient_ids(self):
        group = self.env.ref('invoice_mail_reminder.group_first_reminder')
        partner_ids = group.users.mapped('partner_id').ids
        partner_ids = partner_ids + [self.partner_id.id]
        return ','.join(str(pid) for pid in partner_ids)

    def get_second_reminder_recipient_ids(self):
        group = self.env.ref('invoice_mail_reminder.group_second_reminder')
        partner_ids = group.users.mapped('partner_id').ids
        partner_ids = partner_ids + [self.partner_id.id]
        return ','.join(str(pid) for pid in partner_ids)

    def open_invoice_tracker(self):
        return {
            'name': 'Invoice Tracker',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.reminder.tracker',
            'res_id': self.reminder_tracker_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class InvoiceReminderCron(models.Model):
    _name = 'invoice.reminder.cron'
    _description = 'Invoice Reminder Cron Job'

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help="Company of the employee")

    def process_invoice_reminders(self):
        _logger.info("Starting invoice reminder processing...")

        today = fields.Date.today()
        invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('amount_residual', '>', 0)
        ])
        # today = today + relativedelta(days=7)

        for invoice in invoices:
            self._process_single_invoice(invoice, today)

    def _process_single_invoice(self, invoice, today):
        """Process reminders for a single invoice"""
        tracker = invoice.reminder_tracker_id

        # Create tracker if doesn't exist
        if not tracker:
            invoice.create_reminder_tracker()
            tracker = invoice.reminder_tracker_id
            if not tracker:
                return

        # Check if invoice is paid (stop all reminders)
        if invoice.payment_state == 'paid':
            if not tracker.payment_confirmation_sent:
                self._send_payment_confirmation(invoice, tracker)
            tracker.is_active = False
            return

        # Don't process if not active
        if not tracker.is_active:
            return

        due_date = invoice.invoice_date_due
        if not due_date:
            return

        days_until_due = (due_date - today).days
        days_overdue = (today - due_date).days

        # 1. Pre-due reminder (1 week before)
        if days_until_due == 7 and not tracker.pre_due_sent:
            self._send_week1_reminder(invoice)
            tracker.pre_due_sent = True

        # # 2. Invoice issuance (immediate)
        # elif not tracker.invoice_issued_sent:
        #     # self._send_invoice_issued(invoice, tracker)
        #     tracker.invoice_issued_sent = True

        # Week 1: One reminder at end of week
        elif days_overdue == 7 and not tracker.week1_reminder_sent:
            self._send_week1_reminder(invoice)
            tracker.week1_reminder_sent = True

        # Week 2: Every 3 days
        elif 8 <= days_overdue <= 14:
            if not tracker.last_week2_reminder or (today - tracker.last_week2_reminder).days >= 3:
                self._send_week2_reminder(invoice)
                tracker.week2_reminders_count += 1
                tracker.last_week2_reminder = today

        # Weeks 3-4: Escalation (every 3 days)
        elif 15 <= days_overdue <= 28:
            if not tracker.last_escalation_reminder or (today - tracker.last_escalation_reminder).days >= 3:
                # self._send_escalation_reminder(invoice, tracker)
                tracker.escalation_reminders_count += 1
                tracker.last_escalation_reminder = today

    def _send_pre_due_reminder(self, invoice):
        """Send reminder 1 week before due date"""
        template = self.env.ref('your_module.template_pre_due_reminder')
        template.send_mail(invoice.id, force_send=True)
        _logger.info(f"Pre-due reminder sent for invoice {invoice.name}")

    def _send_invoice_issued(self, invoice, tracker):
        """Send invoice issuance notification"""
        template = self.env.ref('your_module.template_invoice_issued')
        # Send to initial 2 users
        for user in tracker.initial_recipient_ids[:2]:
            template.with_context(email_to=user.email).send_mail(invoice.id, force_send=True)
        _logger.info(f"Invoice issued notification sent for {invoice.name}")

    def _send_week1_reminder(self, invoice):
        """Send week 1 reminder"""
        template = self.env.ref('invoice_mail_reminder.send_first_week_reminder')
        template.send_mail(invoice.id, force_send=True, email_values={'res_id': invoice.id})

        _logger.info(f"Week 1 reminder sent for invoice {invoice.name}")

    def _send_week2_reminder(self, invoice):
        """Send week 2 reminder (every 3 days)"""
        template = self.env.ref('invoice_mail_reminder.send_second_week_reminder')
        template.send_mail(invoice.id, force_send=True, email_values={'res_id': invoice.id})
        _logger.info(f"Week 2 reminder sent for invoice {invoice.name}")

    def _send_escalation_reminder(self, invoice, tracker):
        """Send escalation reminder to 6 people"""
        template = self.env.ref('your_module.template_escalation_reminder')
        # Send to all 6 escalation recipients
        for user in tracker.escalation_recipient_ids:
            template.with_context(email_to=user.email).send_mail(invoice.id, force_send=True)
        _logger.info(f"Escalation reminder sent for invoice {invoice.name}")

    def _send_payment_confirmation(self, invoice, tracker):
        """Send payment confirmation based on timing"""
        days_overdue = (fields.Date.today() - invoice.invoice_date_due).days

        if days_overdue <= 14:
            # Send to 3 people
            template = self.env.ref('your_module.template_payment_confirmation_3')
            for user in tracker.initial_recipient_ids:
                template.with_context(email_to=user.email).send_mail(invoice.id, force_send=True)
        else:
            # Send to 6 people
            template = self.env.ref('your_module.template_payment_confirmation_6')
            for user in tracker.escalation_recipient_ids:
                template.with_context(email_to=user.email).send_mail(invoice.id, force_send=True)

        tracker.payment_confirmation_sent = True
        _logger.info(f"Payment confirmation sent for invoice {invoice.name}")


