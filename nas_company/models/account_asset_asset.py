from odoo import models, fields, api, _


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    brand_id = fields.Many2one('brand.asset.asset')
    model_id = fields.Many2one('model.asset.asset')
    location_id = fields.Many2one('location.asset.asset')
    serial_number = fields.Char()
    asset_state = fields.Selection([
        ('maintenance', 'Maintenance'),
        ('stock', 'Stock'),
        ('employee', 'Employee'),
    ], tracking=True)
    condition = fields.Char()
    assigned_employee = fields.Many2one('hr.employee', tracking=True)
    employee_code = fields.Char(related="assigned_employee.employee_code",tracking=True)