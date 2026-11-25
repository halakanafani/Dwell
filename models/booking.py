# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DwellBooking(models.Model):
    _name = 'dwell.booking'
    _description = 'Holiday Home Reservation'
    _order = 'check_in_date desc'

    # Core Attributes
    name = fields.Char(string='Booking Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    property_id = fields.Many2one('dwell.property', string='Property', required=True, ondelete='cascade')
    
    # Guest & Source details
    customer_name = fields.Char(string='Guest Name', required=True)
    customer_email = fields.Char(string='Guest Email')
    customer_phone = fields.Char(string='Guest Phone')
    
    booking_source = fields.Selection([
        ('direct', 'Direct Booking'),
        ('airbnb', 'Airbnb'),
        ('booking_com', 'Booking.com'),
        ('other', 'Other Channel')
    ], string='Booking Source', default='direct', required=True)

    booking_type = fields.Selection([
        ('standard', 'Standard Booking'),
        ('special', 'Special Booking (VIP / Long-Term)')
    ], string='Booking Type', default='standard', required=True)

    # Dates
    check_in_date = fields.Date(string='Check-In Date', required=True)
    check_out_date = fields.Date(string='Check-Out Date', required=True)
    
    # Lifecycle Status
    booking_status = fields.Selection([
        ('pending', 'Pending Approval'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked-In'),
        ('checked_out', 'Checked-Out'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='confirmed', tracking=True, required=True)

    # Special Booking Features
    special_requests = fields.Text(string='Special Requests')
    vip_perks = fields.Char(string='VIP Perks')
    cancellation_reason = fields.Text(string='Cancellation / Rejection Reason')

    # Sequence Generator for Booking Reference
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dwell.booking') or _('New')
        return super(DwellBooking, self).create(vals_list)

    # Validation: Check-Out must be after Check-In
    @api.constrains('check_in_date', 'check_out_date')
    def _check_dates(self):
        for record in self:
            if record.check_in_date and record.check_out_date and record.check_out_date <= record.check_in_date:
                raise ValidationError(_("Check-Out Date must be after Check-In Date!"))

    # Action Methods
    def action_confirm_booking(self):
        for record in self:
            record.booking_status = 'confirmed'

    def action_check_in(self):
        for record in self:
            if record.booking_status != 'confirmed':
                raise ValidationError(_("Only confirmed bookings can check in!"))
            record.booking_status = 'checked_in'

    def action_check_out(self):
        for record in self:
            if record.booking_status != 'checked_in':
                raise ValidationError(_("Only checked-in guests can check out!"))
            record.booking_status = 'checked_out'

    def action_cancel_booking(self):
        for record in self:
            record.booking_status = 'cancelled'