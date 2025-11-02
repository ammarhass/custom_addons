from odoo import models, fields, api, _

class InheritEquipmentRequest(models.Model):
    _inherit = 'equipment.request'

    def action_internal_transfer(self):
        super().action_internal_transfer()
        emp_product = self.env['employee.products'].search([])

        if self.equipment_request_ids:
            product_lines = []
            all_assets = self.env['account.asset.asset']

            for request in self.equipment_request_ids:
                invoice_lines = self.env['account.move.line'].search([
                    ('product_id', '=', request.product_id.id),
                    ('move_id', '!=', False)
                ])

                invoice_ids = invoice_lines.mapped('move_id').ids

                assets = self.env['account.asset.asset'].search([
                    ('invoice_id', 'in', invoice_ids)
                ])

                all_assets |= assets

                product_lines.append((0, 0, {
                    'product_id': request.product_id.id,
                    'assign_date': self.stock_date,
                    'employee_id': self.employee_name_id.id,
                    'quantity': request.quantity,
                    'product_uom_id': request.product_uom_id.id,
                    'description': request.description
                }))

            if all_assets:
                all_assets.write({'asset_state': 'employee'})

            self.employee_name_id.assigned_product_ids = product_lines
            return all_assets