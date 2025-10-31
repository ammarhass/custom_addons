from odoo import models, fields, api
from datetime import datetime, date, timedelta


class MailMessageInherit(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(MailMessageInherit, self).create(vals_list)

        for record in records:
            if not self.env.context.get('create_ticket'):
                self._check_subject_and_create_ticket(record)

        return records

    def _check_subject_and_create_ticket(self, message):

        mail_config = self.env['incoming.mail.config'].search([('create_ticket', '=', True)])
        ticket_keywords = mail_config.subject_ids.mapped('name')

        if message.subject:
            subject_lower = message.subject.lower()

            subject_words = subject_lower.split()

            if any(keyword.lower() in subject_words for keyword in ticket_keywords):
                self._create_helpdesk_ticket(message)

    def _create_helpdesk_ticket(self, message):
        try:
            if not self.env['ir.model'].search([('model', '=', 'helpdesk.ticket')]):
                print("Helpdesk module not installed")
                return

            partner_id = False
            if message.author_id:
                partner_id = message.author_id.id
            elif message.email_from:
                partner = self.env['res.partner'].search([
                    ('email', '=ilike', message.email_from)
                ], limit=1)
                if partner:
                    partner_id = partner.id

            ticket_vals = {
                'name': message.subject or 'Support Request',
                'description': message.body or 'No description provided',
                'partner_id': partner_id,
                'email_cc': message.email_from,
            }

            ticket = self.env['helpdesk.ticket'].create(ticket_vals)
            activity_type = self.env.ref('nas_company.incoming_mail_activity_type')
            model = self.env['ir.model']._get('helpdesk.ticket')
            activity_obj = self.env['mail.activity']

            users = self.env.ref("nas_company.nas_incoming_mail_group").users
            for user in users:
                if user:
                    activity_vals = {
                        'activity_type_id': activity_type.id,
                        'note': "for reviewing Hr Request",
                        'user_id': user.id,
                        'res_id': ticket.id,
                        'res_model_id': model.id,
                        'date_deadline': datetime.today().date(),
                    }
                    activity_obj.sudo().with_context(create_ticket=True).create(activity_vals)

            message.author_id.unlink()
            self.env['partner_id'].browse(message.res_id).unlink()


            print(f"Helpdesk ticket created: {ticket.name} (ID: {ticket.id})")

        except Exception as e:
            print(f"Error creating helpdesk ticket: {e}")