from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    service_type_id = fields.Many2one('project.service.type')
    account_director_ids = fields.Many2many('res.users')
    account_executive_ids = fields.Many2many('res.users', relation='Executive')
    commercial_register_id = fields.Many2one('commercial.register')
    commercial_register = fields.Char(related='commercial_register_id.commercial_register')
    vat_no = fields.Char(related='commercial_register_id.vat_no')
    project_code = fields.Char()

    @api.constrains('project_code')
    def _check_unique_project_code(self):
        for record in self:
            if record.project_code:
                existing_record = self.search([
                    ('project_code', '=', record.project_code),
                    ('id', '!=', record.id)
                ])
                if existing_record:
                    raise ValidationError(
                        f"Project code '{record.project_code}' already exists. "
                        f"Please use a unique project code."
                    )

    @api.constrains('name', 'partner_id')
    def _check_unique_project_name_per_customer(self):
        for record in self:
            if record.name and record.partner_id:
                existing_project = self.search([
                    ('name', '=', record.name),
                    ('partner_id', '!=', record.partner_id.id),
                    ('id', '!=', record.id)
                ], limit=1)

                if existing_project:
                    raise ValidationError(
                        f"Project name '{record.name}' already exists for customer "
                        f"'{existing_project.partner_id.name}'. Please use a unique project name "
                        f"for different customers."
                    )



class ProjectServiceType(models.Model):
    _name = 'project.service.type'

    name = fields.Char()