from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    team_id = fields.Many2one('employee.team')
    unit_id = fields.Many2one('task.unit.type')
    task_type_id = fields.Many2one('task.type')
    quantity = fields.Integer()
    note_entered  = fields.Boolean()

    reference_number = fields.Char(
        'Reference', default=lambda self: self.env['ir.sequence'].next_by_code('project.task'))

    def write(self, vals):
        for task in self:
            if not task.task_type_id.user_can_edit:
                if 'stage_id' in vals and vals['stage_id'] != task.stage_id.id:
                    if not task.note_entered:
                        pass
                    #     raise ValidationError("You must add a note before changing the stage.")
                    # vals['note_entered'] = False
            else:
                if 'stage_id' in vals and vals['stage_id'] != task.stage_id.id:
                    allowed_user = self.env['res.users'].search([('partner_id', '=', task.partner_id.id)])
                    if allowed_user and allowed_user != self.env.user:
                        raise ValidationError(
                            "You are not allowed to change the stage for this task."
                        )


        return super(ProjectTask, self).write(vals)

    def open_note_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Stage',
            'res_model': 'task.note.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
            },
        }



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
