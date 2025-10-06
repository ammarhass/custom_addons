from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    nas_company = fields.Boolean()
    allowed_days = fields.Integer()
    prevent_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ])