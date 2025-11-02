from odoo import models, fields, api, _

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    allow_stage_ids = fields.Many2many('project.task.type',
                                       "rel_allow_stage",
                                       "task_type_id",
                                       "allow_stage_id",
                                       domain="[('id', '!=', id)]",
                                       string="Allow Stages")
    mandatory_message = fields.Boolean()



