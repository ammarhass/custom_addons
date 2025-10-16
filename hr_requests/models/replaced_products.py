from odoo import models, fields, api, _


class ReplacementProducts(models.Model):
    _name = 'replacement.products'

    product_id = fields.Many2one('product.product')
    assign_date = fields.Date()
    description = fields.Char(string='Description',
                              help='A brief description of the item.')
    quantity = fields.Float(string='Quantity', default=1,
                            help='The number of units of the associated product'
                                 'that were requested or used.')
    product_uom_id = fields.Many2one('uom.uom',
                                     string='Product Unit of Measure',
                                     help='The unit of measure for the '
                                          'associated'
                                          'product.')
    replace = fields.Boolean()

    request_id = fields.Many2one('hr.request')
