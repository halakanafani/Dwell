
from odoo import models, fields, api
from odoo.exceptions import UserError


# Stores reusable rental agreement templates
class AgreementTemplate(models.Model):
    _name = 'dwell.agreement.template'
    _description = 'Dwell Agreement Template'

    # Name used to identify the template
    name = fields.Char(
        string='Template Name',
        required=True
    )

    # Standard rental terms for the agreement
    content = fields.Text(
        string='Terms and Conditions',
        required=True
    )

    # Rules guests must follow during their stay
    house_rules = fields.Text(
        string='House Rules'
    )

    # Allows templates to be archived instead of deleted
    active = fields.Boolean(
        string='Active',
        default=True
    )


# Stores individual rental agreements for guests
class RentalAgreement(models.Model):
    _name = 'dwell.rental.agreement'
    _description = 'Dwell Rental Agreement'
    _order = 'id desc'

    # Links the agreement to an existing booking from Hala's model
    booking_id = fields.Many2one(
        'dwell.booking',
        string='Booking',
        required=True,
        ondelete='restrict'
    )

    # Links the agreement to a reusable template
    template_id = fields.Many2one(
        'dwell.agreement.template',
        string='Agreement Template',
        required=True,
        ondelete='restrict'
    )

    # Stores the agreement's terms and conditions
    terms_content = fields.Text(
        string='Terms and Conditions'
    )

    # Stores the agreement's house rules
    house_rules = fields.Text(
        string='House Rules'
    )

    # Gets the property from the selected booking
    property_id = fields.Many2one(
        'dwell.property',
        string='Property',
        related='booking_id.property_id',  # Gets Hala's booking property
        store=True,  # Stores and synchronizes the value
        readonly=True  # Prevents manual editing
    )

    # Gets the check-in date from the booking
    check_in_date = fields.Date(
        string='Check-In Date',
        related='booking_id.check_in_date',  # Gets booking check-in date
        store=True,  # Stores and synchronizes the value
        readonly=True  # Prevents manual editing
    )

    # Gets the check-out date from the booking
    check_out_date = fields.Date(
        string='Check-Out Date',
        related='booking_id.check_out_date',  # Gets booking check-out date
        store=True,  # Stores and synchronizes the value
        readonly=True  # Prevents manual editing
    )

    # Unique reference generated for each rental agreement
    name = fields.Char(
        string='Agreement Reference',
        required=True,
        default='New',
        copy=False,
        readonly=True
    )

    # Stores the guest name from the selected booking
    guest_name = fields.Char(
        string='Guest Name',
        required=True
    )

    # Automatically sets the agreement date to today
    agreement_date = fields.Date(
        string='Agreement Date',
        default=fields.Date.context_today,
        required=True
    )

    # Stores the reason when an agreement is rejected
    rejection_reason = fields.Text(
        string='Rejection Reason'
    )

    # Tracks the different stages of a rental agreement
    status = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('signed', 'Signed'),
        ('rejected', 'Rejected')
    ], string='Status',
       default='draft',
       required=True,
       copy=False)

    # Automatically assigns an agreement number when saving
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'dwell.rental.agreement'
                    ) or 'New'
                )

        return super().create(vals_list)

    # Automatically fills the guest name when a booking is selected
    @api.onchange('booking_id')
    def _onchange_booking_id(self):
        if self.booking_id:
            self.guest_name = self.booking_id.customer_name
        else:
            self.guest_name = False

    # Copies the template details when a template is selected
    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.terms_content = self.template_id.content
            self.house_rules = self.template_id.house_rules
        else:
            self.terms_content = False
            self.house_rules = False

    # Generates an agreement using the booking and template
    def action_generate_agreement(self):
        for agreement in self:

            # Only draft agreements can be generated
            if agreement.status != 'draft':
                raise UserError(
                    'Only draft agreements can be generated.'
                )

            # A booking and template must be selected
            if not agreement.booking_id or not agreement.template_id:
                raise UserError(
                    'Please select a booking and agreement template.'
                )

            # Cancelled bookings cannot generate agreements
            if agreement.booking_id.booking_status == 'cancelled':
                raise UserError(
                    'Cannot generate an agreement for a cancelled booking.'
                )

            # Copies booking details and saves the generated agreement
            agreement.write({
                'guest_name': agreement.booking_id.customer_name,
                'terms_content': agreement.template_id.content,
                'house_rules': agreement.template_id.house_rules,
                'status': 'generated'
            })

        return True

    # Records that a generated agreement has been signed
    def action_sign_agreement(self):
        for agreement in self:

            # The agreement must be generated first
            if agreement.status != 'generated':
                raise UserError(
                    'Only generated agreements can be signed.'
                )

            # Updates the agreement's status
            agreement.status = 'signed'

        return True

    # Rejects an agreement before it has been signed
    def action_reject_agreement(self):
        for agreement in self:

            # Only draft or generated agreements can be rejected
            if agreement.status not in ('draft', 'generated'):
                raise UserError(
                    'Only draft or generated agreements can be rejected.'
                )

            # Requires a reason before rejecting the agreement
            if not agreement.rejection_reason:
                raise UserError(
                    'Please enter a rejection reason first.'
                )

            # Updates the agreement's status
            agreement.status = 'rejected'

        return True

    # Opens the rental agreement PDF report
    def action_print_pdf(self):
        self.ensure_one()

        # Draft and rejected agreements cannot be printed as final
        if self.status not in ('generated', 'signed'):
            raise UserError(
                'Generate the agreement before printing the PDF.'
            )

        # Calls the QWeb report defined in the XML file
        return self.env.ref(
            'dwell_management.action_report_rental_agreement'
        ).report_action(self)

