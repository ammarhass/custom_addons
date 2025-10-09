from odoo import models, fields, api

class SoftwareLicenses(models.Model):

    _name = 'software.licenses'
    _rec_name = 'name'

    name = fields.Char()
