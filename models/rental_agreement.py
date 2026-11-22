
from odoo import models, fields

# Defines the Rental Agreement model for Dwell
class RentalAgreement(models.Model):
    _name = 'dwell.rental.agreement'
    _description = 'Dwell Rental Agreement'

    name = fields.Char(
        string='Agreement Reference',
        required=True
    )
# Stores the name of the guest
    guest_name = fields.Char(
        string='Guest Name',
        required=True
    )
# Automatically sets the agreement date to today
    agreement_date = fields.Date(
        string='Agreement Date',
        default=fields.Date.today
    )
# Tracks the current status of the agreement
    status = fields.Selection([
        ('draft', 'Draft'),
        ('signed', 'Signed'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft')
