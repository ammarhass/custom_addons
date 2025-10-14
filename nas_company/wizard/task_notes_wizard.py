from odoo import models, fields, api, _

class TaskNoteWizard(models.TransientModel):

    _name = 'task.note.wizard'

    note = fields.Text()
    task_id = fields.Many2one('project.task')

    def submit_button(self):
        active_id = self.env.context.get('active_id')
        task = self.env['project.task'].browse(active_id)
        if task:
            message = self.note
            task.note_entered = True
            task.with_context(stage_change_note=self.note).message_post(body=message)
            return {'type': 'ir.actions.act_window_close'}
