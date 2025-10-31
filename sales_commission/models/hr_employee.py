from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    commission_plan_id = fields.Many2one('salesperson.commission.plan')
