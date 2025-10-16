from odoo import models, fields, api, _


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    joining_date = fields.Date()
    assigned_product_ids = fields.One2many('employee.products', 'employee_id')
    section_id = fields.Many2one('employee.section')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        if not name:
            return super().name_search(name=name, args=args, operator=operator,
                                       limit=limit)
        domain = ['|', '|', '|',
                  ('name', operator, name),
                  ('work_email', operator, name),
                  ('employee_code', operator, name),
                  ('mobile_phone', operator, name)]
        if args:
            domain = ['&'] + args + domain
        employees = self.search_fetch(domain, ['display_name'], limit=limit)
        return [(employee.id, employee.display_name) for employee in employees]


