from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class DwellPermit(models.Model):
    """DTCM holiday home permit.

    One model covers both subclasses from the class diagram
    (IndividualOwnerPermit and OperatorPermit). `permit_type` decides which
    fields and checks apply. The system never approves a permit itself: it
    only RECORDS DTCM decisions through record_dtcm_update().
    """
    _name = 'dwell.permit'
    _description = 'DTCM Holiday Home Permit'
    _order = 'expiry_date, id'

    MAX_INDIVIDUAL_PERMITS = 8  # maxPermits in IndividualOwnerPermit
    ACTIVE_STATES = ['under_inspection', 'valid', 'expiring_soon', 'suspended']

    # status sent by DTCM -> (states it can come from, state it leads to)
    DTCM_TRANSITIONS = {
        'Valid': (['under_inspection', 'suspended', 'reopening_inspection'], 'valid'),
        'Rejected': (['under_inspection'], 'rejected'),
        'Suspended': (['valid', 'expiring_soon'], 'suspended'),
        'Closed': (['suspended', 'reopening_inspection'], 'closed'),
        'ReopenRequested': (['closed'], 'reopen_requested'),
        'ReopeningInspection': (['reopen_requested'], 'reopening_inspection'),
    }

    # ---------- Permit (base class) ----------
    name = fields.Char(string='Permit Number', required=True, copy=False, default='New')
    permit_type = fields.Selection(
        [('individual', 'Individual Owner'), ('operator', 'Operator')],
        string='Permit Type', required=True, default='individual')
    #TO DO: switch to dwell.unit once unit.py exists 
    unit_id = fields.Many2one('dwell.property', string='Unit', required=True, ondelete='restrict')
    manager_id = fields.Many2one(
        'res.users', string='Property Manager', required=True,
        default=lambda self: self.env.user)
    license_info = fields.Char(string='License Info')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    new_expiry_date = fields.Date(string='New Expiry Date (renewal)')
    state = fields.Selection([
        ('draft', 'Starting Application'),
        ('under_inspection', 'Under Inspection'),
        ('valid', 'Valid'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
        ('reopen_requested', 'Reopen Requested'),
        ('reopening_inspection', 'Reopening Inspection'),
        ('rejected', 'Application Rejected'),
    ], string='Status', default='draft', readonly=True, copy=False)
    dtcm_remarks = fields.Text(string='DTCM Remarks')
    last_dtcm_update = fields.Date(string='Last DTCM Update', readonly=True)

    # ---------- OperatorPermit ----------
    operator_license_no = fields.Char(string='Operator License No')
    owner_authorisation_letter = fields.Binary(string='Owner Authorisation Letter')
    owner_authorisation_filename = fields.Char()
    contract_start_date = fields.Date(string='Contract Start')
    contract_end_date = fields.Date(string='Contract End')

    # ---------- Constraints ----------
    @api.constrains('issue_date', 'expiry_date', 'contract_start_date', 'contract_end_date')
    def _check_dates(self):
        for p in self:
            if p.issue_date and p.expiry_date and p.expiry_date < p.issue_date:
                raise ValidationError("Expiry date cannot be before the issue date.")
            if (p.contract_start_date and p.contract_end_date
                    and p.contract_end_date < p.contract_start_date):
                raise ValidationError("Contract end cannot be before contract start.")

    # ---------- Individual owner checks ----------
    def get_active_permit_count(self):
        """Active individual permits held by this permit's manager (not counting this one)."""
        self.ensure_one()
        return self.search_count([
            ('manager_id', '=', self.manager_id.id),
            ('permit_type', '=', 'individual'),
            ('state', 'in', self.ACTIVE_STATES),
            ('id', '!=', self.id),
        ])

    def check_unit_eligibility(self):
        """The unit must not already have an active permit."""
        self.ensure_one()
        clash = self.search_count([
            ('unit_id', '=', self.unit_id.id),
            ('state', 'in', self.ACTIVE_STATES),
            ('id', '!=', self.id),
        ])
        if clash:
            raise UserError("This unit already has an active permit (not eligible).")

    def check_permit_limit(self):
        self.ensure_one()
        if self.get_active_permit_count() >= self.MAX_INDIVIDUAL_PERMITS:
            raise UserError(
                "This manager already holds %d active permits (limit reached)."
                % self.MAX_INDIVIDUAL_PERMITS)

    # ---------- Operator checks ----------
    def verify_owner_authorisation(self):
        self.ensure_one()
        if not self.owner_authorisation_letter:
            raise UserError("Upload the owner authorisation letter first (not eligible).")

    def validate_contract_period(self):
        self.ensure_one()
        if not (self.contract_start_date and self.contract_end_date and self.expiry_date):
            raise UserError("Fill in the contract start, contract end and expiry dates.")
        if self.expiry_date > self.contract_end_date:
            raise UserError("The permit expiry date cannot be after the contract end date.")

    # ---------- Statechart operations ----------
    def action_submit_application(self):
        """StartingApplication -> verify by permit type -> UnderInspection."""
        for p in self:
            if p.state != 'draft':
                raise UserError("Only a new application can be submitted.")
            if p.permit_type == 'individual':
                p.check_unit_eligibility()
                p.check_permit_limit()
            else:
                p.verify_owner_authorisation()
                p.validate_contract_period()
            p.state = 'under_inspection'
        return True

    def record_dtcm_update(self, status, decision_date=None, remarks=None):
        """Record a decision made by DTCM (the system does not decide by itself)."""
        if status not in self.DTCM_TRANSITIONS:
            raise UserError("Unknown DTCM status: %s" % status)
        allowed_from, new_state = self.DTCM_TRANSITIONS[status]
        decision_date = decision_date or fields.Date.today()
        for p in self:
            if p.state not in allowed_from:
                raise UserError(
                    "DTCM status '%s' cannot be recorded while the permit is '%s'."
                    % (status, dict(p._fields['state'].selection).get(p.state)))
            vals = {'state': new_state, 'last_dtcm_update': decision_date}
            if remarks:
                vals['dtcm_remarks'] = remarks
            if new_state == 'valid' and not p.issue_date:
                vals['issue_date'] = decision_date
            p.write(vals)
        return True

    def send_reminder(self, days_before_expiry=30):
        """expiryApproaching / sendReminder: Valid -> ExpiringSoon."""
        for p in self.filtered(lambda r: r.state == 'valid'):
            p.state = 'expiring_soon'
        return True

    def renew_permit(self, new_expiry_date):
        """ExpiringSoon / Expired -> Valid once the renewal is approved."""
        for p in self:
            if p.state not in ('expiring_soon', 'expired'):
                raise UserError("Only permits that are expiring soon or expired can be renewed.")
            if p.expiry_date and new_expiry_date <= p.expiry_date:
                raise UserError("The new expiry date must be after the current one.")
            p.write({'expiry_date': new_expiry_date, 'new_expiry_date': False, 'state': 'valid'})
        return True

    # ---------- Button methods (called from the form view) ----------
    def action_dtcm_valid(self):
        return self.record_dtcm_update('Valid')

    def action_dtcm_rejected(self):
        return self.record_dtcm_update('Rejected')

    def action_dtcm_suspended(self):
        return self.record_dtcm_update('Suspended')

    def action_dtcm_closed(self):
        return self.record_dtcm_update('Closed')

    def action_dtcm_reopen_requested(self):
        return self.record_dtcm_update('ReopenRequested')

    def action_dtcm_reopening_inspection(self):
        return self.record_dtcm_update('ReopeningInspection')

    def action_send_reminder(self):
        return self.send_reminder()

    def action_renew(self):
        for p in self:
            if not p.new_expiry_date:
                raise UserError("Enter the new expiry date first.")
            p.renew_permit(p.new_expiry_date)
        return True

    # ---------- Scheduled job (hook up in data/cron_data.xml later) ----------
    @api.model
    def _cron_check_expiry(self, days_before_expiry=30):
        today = fields.Date.today()
        expired = self.search([('state', 'in', ['valid', 'expiring_soon']),
                               ('expiry_date', '<', today)])
        expired.write({'state': 'expired'})
        soon = self.search([('state', '=', 'valid'),
                            ('expiry_date', '<=', today + timedelta(days=days_before_expiry))])
        soon.send_reminder(days_before_expiry)