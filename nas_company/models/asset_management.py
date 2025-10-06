from odoo import models, fields, api, _


class AssetBrand(models.Model):
    _name = 'brand.asset.asset'

    name = fields.Char()


class ModelBrand(models.Model):
    _name = 'model.asset.asset'

    name = fields.Char()


class LocationBrand(models.Model):
    _name = 'location.asset.asset'

    name = fields.Char()
