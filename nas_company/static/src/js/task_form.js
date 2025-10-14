odoo.define('nas_company.task_form', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var viewRegistry = require('web.viewRegistry');

    FormController.include({
        /**
         * Override to handle stage_id changes and open wizard
         */
        _onFieldChanged: function (event) {
            this._super.apply(this, arguments);

            var self = this;
            var record = this.model.get(this.handle);

            // Check if stage_id field was changed
            if (event.data.changes && event.data.changes.stage_id) {
                var newStageId = event.data.changes.stage_id;

                // Revert the stage change temporarily
                record.update({stage_id: event.data.changes.stage_id.oldValue});

                // Open the wizard
                this._openStageNoteWizard(newStageId);
            }
        },

        /**
         * Open the stage note wizard
         */
        _openStageNoteWizard: function (newStageId) {
            var self = this;
            var context = {
                default_task_id: this.handle.context.active_id,
                default_new_stage_id: newStageId
            };

            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Stage Change Note Required',
                res_model: 'task.note.wizard',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: context,
            }, {
                on_close: function () {
                    // Optional: refresh the view after wizard closes
                    self.reload();
                }
            });
        }
    });
});