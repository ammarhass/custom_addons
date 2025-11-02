from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def asset_create(self):
        """Create function for the asset and its associated properties"""
        for record in self:
            if record.asset_category_id:
                vals = {
                    'name': record.name,
                    'code': record.move_id.name or False,
                    'category_id': record.asset_category_id.id,
                    'value': record.price_subtotal,
                    'partner_id': record.partner_id.id,
                    'company_id': record.move_id.company_id.id,
                    'currency_id': record.move_id.company_currency_id.id,
                    'date': record.move_id.invoice_date,
                    'invoice_id': record.move_id.id,
                    'asset_state': 'stock',

                }
                changed_vals = record.env[
                    'account.asset.asset'].onchange_category_id_values(
                    vals['category_id'])
                vals.update(changed_vals['value'])
                asset = record.env['account.asset.asset'].create(vals)
                if record.asset_category_id.open_asset:
                    asset.validate()
        return True
