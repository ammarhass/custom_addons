from odoo import models, fields, api


class HelpdeskTicket(models.Model):

    _inherit = 'helpdesk.ticket'

    team_id = fields.Many2one(
        'helpdesk.team',
        string='Helpdesk Team',
        index=True,
        tracking=True
    )


    available_teams_ids = fields.Many2many('helpdesk.team',related='ticket_type_id.team_ids'  ,string='Available Teams')
    ticket_type_id = fields.Many2one('helpdesk.ticket.type')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            employee = self.env['hr.employee'].search([('user_partner_id', '=', self.partner_id.id)])
            if employee:
                self.email_cc = employee.work_email
                self.partner_phone = employee.work_phone

class HelpdeskType(models.Model):
    _name = 'helpdesk.ticket.type'

    name = fields.Char()
    team_ids = fields.Many2many('helpdesk.team')