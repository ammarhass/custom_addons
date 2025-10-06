from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allowed_days = fields.Integer(
        related='company_id.allowed_days', readonly=False)

    prevent_day = fields.Selection(
        related='company_id.prevent_day', readonly=False)

