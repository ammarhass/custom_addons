from odoo import models, fields, api, _


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    employee_code = fields.Char()
    team_id = fields.Many2one('employee.team')


class EmployeeTeam(models.Model):
    _name = 'employee.team'
    _rec_name = 'name'

    name = fields.Char()
