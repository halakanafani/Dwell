from odoo import fields, models


class DwellUnit(models.Model):
    _name = 'dwell.unit'
    _description = 'Holiday Home Unit'

    name = fields.Char(string='Unit name', required=True)
    property_id = fields.Many2one(
        'dwell.property',
        string='Property',
        required=True,
        ondelete='restrict',
    )
    bedrooms = fields.Integer(string='Bedrooms', default=1, required=True)

    _unique_unit_number = models.Constraint(
        'UNIQUE(property_id, name)',
        'A unit with this name already exists in this property.',
    )

    unit_type = fields.Selection(
        [
            ('apartment', 'Apartment'),
            ('villa', 'Villa'),
        ],
        string='Unit Type',
        required=True,
    )

    _check_bedrooms = models.Constraint(
        'CHECK(bedrooms >= 0)',
        'Bedrooms must be zero or greater.',
    )

    has_private_pool = fields.Boolean(string='Private Pool')
    number_of_floors = fields.Integer(string='Number of Floors')
    building_name = fields.Char(string='Building Name')
    building_access_info = fields.Text(string='Building Access Info')

    unit_status = fields.Selection(
        [
            ('available', 'Available'),
            ('occupied', 'Occupied'),
            ('unavailable', 'Unavailable'),
        ],
        string='Unit Status',
        default='available',
        required=True,
    )
