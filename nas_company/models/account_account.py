from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.onchange('account_type')
    def _onchange_account_type_update_code(self):
        if self.env.company.nas_company:
            if self.account_type:
                last_account = self.search([
                    ('account_type', '=', self.account_type),
                    ('company_ids', 'in', self.company_ids.ids)
                ], order='code desc', limit=1)

                if last_account and last_account.code:
                    try:
                        last_code = last_account.code
                        if last_code.isdigit():
                            new_code = str(int(last_code) + 1).zfill(len(last_code))
                            self.code = new_code
                    except (ValueError, TypeError):
                        pass