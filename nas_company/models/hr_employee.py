from odoo import models, fields, api, _


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    employee_code = fields.Char()
