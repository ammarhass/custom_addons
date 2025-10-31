from odoo import models, fields, api, _

class IncomingMailConfig(models.Model):

    _name = 'incoming.mail.config'
    _rec_name = 'name'

    name = fields.Char()
    create_ticket = fields.Boolean()
    subject_ids = fields.Many2many('incoming.mail.subject')

class IncomingMailSubject(models.Model):

    _name = 'incoming.mail.subject'
    _rec_name = 'name'

    name = fields.Char()