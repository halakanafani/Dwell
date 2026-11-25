from odoo import models, fields, api

class DwellProperty(models.Model):
    _name = 'dwell.property'
    _description = 'Holiday Home Property'

    name = fields.Char(string='Property Name', required=True)
    address = fields.Char(string='Address')

    owner_id = fields.Many2one('res.partner', string='Owner')
    manager_id = fields.Many2one(
        'res.users',
        string='Property Manager',
        default=lambda self: self.env.user,
    )

    property_type = fields.Selection([
        ('apartment', 'Apartment Building'),
        ('villa', 'Villa'),
    ], string='Property Type', default='apartment')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active')


    unit_ids = fields.One2many(
        'dwell.unit',
        'property_id',
        string='Units',
        groups='dwell_management.group_dwell_manager',
    )

    unit_count = fields.Integer(
        string='Number of Units',
        compute='_compute_unit_count',
        groups='dwell_management.group_dwell_manager',
    )

    @api.depends('unit_ids')
    def _compute_unit_count(self):
        for prop in self:
            prop.unit_count = len(prop.unit_ids)