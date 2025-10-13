from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    team_id = fields.Many2one('employee.team')
    unit_id = fields.Many2one('task.unit.type')
    task_type_id = fields.Many2one('task.type')
    quantity = fields.Integer()

    reference_number = fields.Char(
        'Reference', default=lambda self: self.env['ir.sequence'].next_by_code('project.task'))


    @api.constrains('quantity', 'task_type_id')
    def _check_quantity(self):
        for record in self:
            if record.quantity:
                if record.task_type_id and record.task_type_id.calendar:
                    allowed_values = [3, 6, 9, 12, 15, 18, 21, 24]
                    if record.quantity not in allowed_values:
                        raise ValidationError(
                            f"When calendar is enabled, quantity must be one of: {', '.join(map(str, allowed_values))}"
                        )
                else:
                    if record.quantity < 1 or record.quantity > 15:
                        raise ValidationError("Quantity must be between 1 and 15 when calendar is not enabled")


class TaskUnitType(models.Model):
    _name = 'task.unit.type'

    name = fields.Char()


class TaskType(models.Model):
    _name = 'task.type'

    name = fields.Char()
    calendar = fields.Boolean()
    user_can_edit = fields.Boolean()
