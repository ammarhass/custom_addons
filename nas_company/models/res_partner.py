from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    commercial_register_ids = fields.One2many('commercial.register', 'partner_id')



class CommercialRegister(models.Model):
    _name = 'commercial.register'

    name = fields.Char()
    commercial_register = fields.Char()
    vat_no = fields.Char()
    partner_id = fields.Many2one('res.partner')