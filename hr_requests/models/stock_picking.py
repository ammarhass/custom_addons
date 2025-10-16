from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    hr_request_id = fields.Many2one('hr.request',
                                            string='Request',
                                            help="link internal transfers with hr requests")
