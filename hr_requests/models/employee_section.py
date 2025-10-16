from odoo import models, fields, api, _

class EmployeeSection(models.Model):
    _name = 'employee.section'

    name = fields.Char()