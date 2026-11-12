from odoo import models, fields

class DwellProperty(models.Model):
    _name = 'dwell.property'
    _description = 'Holiday Home Property'

    name = fields.Char(string='Property Name', required=True)
    address = fields.Char(string='Address')
    property_type = fields.Selection([
        ('apartment', 'Apartment Building'),
        ('villa', 'Villa'),
    ], string='Property Type', default='apartment')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active')