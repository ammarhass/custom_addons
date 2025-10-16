from itertools import product

from odoo import models, fields, api, _

class InheritEquipmentRequest(models.Model):
    _inherit = 'equipment.request'

    def action_internal_transfer(self):
        super().action_internal_transfer()
        emp_product = self.env['employee.products'].search([])
        if self.equipment_request_ids:
            product_lines = []
            for request in self.equipment_request_ids:
                product_lines.append((0, 0, {
                    'product_id': request.product_id.id,
                    'assign_date': self.stock_date,
                    'employee_id': self.employee_name_id.id,
                    'quantity': request.quantity,
                    'product_uom_id': request.product_uom_id.id,
                    'description': request.description
                }))
            self.employee_name_id.assigned_product_ids = product_lines
