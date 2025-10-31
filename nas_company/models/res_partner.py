from odoo import models, fields, api, _
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    commercial_register_ids = fields.One2many('commercial.register', 'partner_id')
    sequence = fields.Char(
        string="Sequence",
        readonly=True,
        copy=False,
        default="NEW"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence') or vals.get('sequence') == "NEW":
                vals['sequence'] = self.env['ir.sequence'].next_by_code('res.partner.seq') or "NEW"
        partners = super(ResPartner, self).create(vals_list)
        return partners

    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name','sequence')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat', 'lang')
    def _compute_display_name(self):
        for partner in self:
            name = partner.with_context(lang=self.env.lang)._get_complete_name()
            if partner.sequence:
                name = f"{partner.sequence} - {name}"
            if partner._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = re.sub(r'\s+\n', '\n', name)
            if partner._context.get('partner_show_db_id'):
                name = f"{name} ({partner.id})"
            if partner._context.get('address_inline'):
                splitted_names = name.split("\n")
                name = ", ".join([n for n in splitted_names if n.strip()])
            if partner._context.get('show_email') and partner.email:
                name = f"{name} <{partner.email}>"
            if partner._context.get('show_vat') and partner.vat:
                name = f"{name} ‒ {partner.vat}"

            partner.display_name = name.strip()
    def name_get(self):
        """Returns the patient name, showing 'New -' only for specific hospital groups."""
        result = []


        for rec in self:
                result.append((rec.id, f'{rec.sequence} - {rec.name}'))
        return result



class CommercialRegister(models.Model):
    _name = 'commercial.register'

    name = fields.Char()
    commercial_register = fields.Char()
    vat_no = fields.Char()
    partner_id = fields.Many2one('res.partner')