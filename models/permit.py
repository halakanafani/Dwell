# -*- coding: utf-8 -*-
"""DTCM holiday home permits for the Dwell module.

This file implements the Permit component of the Dwell design:

* ``dwell.permit``- the Permit class and its two subclasses
(IndividualOwnerPermit, OperatorPermit).
* ``dwell.permit.notification`` - the PermitExpiryNotification class.

Design notes
------------
* Dubai Tourism (DTCM) is the authority that approves, suspends and closes
  permits. The system never decides on its own: it only RECORDS DTCM
  decisions (see ``record_dtcm_update``) and enforces the rules that apply
  before an application is submitted.
* The life cycle follows the Permit statechart. Each ``state`` value below
  matches one state in that diagram.
* Once an application is submitted, its official details (type, unit, manager,
  dates, operator documents) are locked and can only change through the
  official actions: DTCM approval and renewal.

Author: Supernova Team (Permits component)
"""
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class DwellPermit(models.Model):
    """DTCM holiday home permit.

    A single model covers both subclasses from the class diagram
    (IndividualOwnerPermit and OperatorPermit). The ``permit_type`` field
    decides which fields are shown and which eligibility checks run:

    * Individual Owner - limited to MAX_INDIVIDUAL_PERMITS active permits per
      property manager, and the unit must not already hold an active permit.
    * Operator - requires the owner's authorisation letter and a contract
      period that covers the permit's expiry date.
    """
    _name = 'dwell.permit'
    _description = 'DTCM Holiday Home Permit'
    _order = 'expiry_date, id'

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------
    # maxPermits attribute of IndividualOwnerPermit in the class diagram.
    MAX_INDIVIDUAL_PERMITS = 8

    # States in which a permit counts as "in use" for the eligibility checks.
    ACTIVE_STATES = ['under_inspection', 'valid', 'expiring_soon', 'suspended']

    # Decision reported by DTCM -> (states it may be recorded from, state it leads to).
    # This table is the single place that defines the allowed DTCM transitions.
    DTCM_TRANSITIONS = {
        'Valid': (['under_inspection', 'suspended', 'reopening_inspection'], 'valid'),
        'Rejected': (['under_inspection'], 'rejected'),
        'Suspended': (['valid', 'expiring_soon'], 'suspended'),
        'Closed': (['suspended', 'reopening_inspection'], 'closed'),
        'ReopenRequested': (['closed'], 'reopen_requested'),
        'ReopeningInspection': (['reopen_requested'], 'reopening_inspection'),
    }

    # Fields that are frozen as soon as the application leaves the draft state.
    LOCKED_AFTER_SUBMIT = [
        'permit_type', 'unit_id', 'manager_id', 'issue_date', 'expiry_date',
        'operator_license_no', 'owner_authorisation_letter',
        'owner_authorisation_filename', 'contract_start_date', 'contract_end_date',
    ]

    # ------------------------------------------------------------------
    # Fields - Permit (base class)
    # ------------------------------------------------------------------
    name = fields.Char(string='Permit Number', required=True, copy=False, default='New')
    permit_type = fields.Selection(
        [('individual', 'Individual Owner'), ('operator', 'Operator')],
        string='Permit Type', required=True, default='individual')
    # TODO: switch to 'dwell.unit' once unit.py exists
    unit_id = fields.Many2one('dwell.property', string='Unit', required=True, ondelete='restrict')
    manager_id = fields.Many2one(
        'res.users', string='Property Manager', required=True,
        default=lambda self: self.env.user)
    license_info = fields.Char(string='License Info')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    # Filled in by the manager when renewing; copied into expiry_date by renew_permit().
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
    notification_ids = fields.One2many(
        'dwell.permit.notification', 'permit_id', string='Notifications')

    # ------------------------------------------------------------------
    # Fields - OperatorPermit only
    # ------------------------------------------------------------------
    operator_license_no = fields.Char(string='Operator License No')
    owner_authorisation_letter = fields.Binary(string='Owner Authorisation Letter')
    owner_authorisation_filename = fields.Char()
    contract_start_date = fields.Date(string='Contract Start')
    contract_end_date = fields.Date(string='Contract End')

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('issue_date', 'expiry_date', 'contract_start_date', 'contract_end_date')
    def _check_dates(self):
        """Keep the permit and contract dates in a logical order."""
        for p in self:
            if p.issue_date and p.expiry_date and p.expiry_date < p.issue_date:
                raise ValidationError("Expiry date cannot be before the issue date.")
            if (p.contract_start_date and p.contract_end_date
                    and p.contract_end_date < p.contract_start_date):
                raise ValidationError("Contract end cannot be before contract start.")

    # ------------------------------------------------------------------
    # Individual owner checks (CheckingUnit / CheckingLimit states)
    # ------------------------------------------------------------------
    def get_active_permit_count(self):
        """Return how many active individual permits this permit's manager holds.

        The permit itself is not counted, so the result can be compared
        directly with MAX_INDIVIDUAL_PERMITS.
        """
        self.ensure_one()
        return self.search_count([
            ('manager_id', '=', self.manager_id.id),
            ('permit_type', '=', 'individual'),
            ('state', 'in', self.ACTIVE_STATES),
            ('id', '!=', self.id),
        ])

    def check_unit_eligibility(self):
        """Raise an error if the unit already has an active permit."""
        self.ensure_one()
        clash = self.search_count([
            ('unit_id', '=', self.unit_id.id),
            ('state', 'in', self.ACTIVE_STATES),
            ('id', '!=', self.id),
        ])
        if clash:
            raise UserError("This unit already has an active permit (not eligible).")

    def check_permit_limit(self):
        """Raise an error if the manager has reached the individual permit limit."""
        self.ensure_one()
        if self.get_active_permit_count() >= self.MAX_INDIVIDUAL_PERMITS:
            raise UserError(
                "This manager already holds %d active permits (limit reached)."
                % self.MAX_INDIVIDUAL_PERMITS)

    # ------------------------------------------------------------------
    # Operator checks (CheckingAuthorisation / CheckingContract states)
    # ------------------------------------------------------------------
    def verify_owner_authorisation(self):
        """Raise an error if the owner's authorisation letter is missing."""
        self.ensure_one()
        if not self.owner_authorisation_letter:
            raise UserError("Upload the owner authorisation letter first (not eligible).")

    def validate_contract_period(self):
        """Raise an error unless the contract covers the permit's expiry date."""
        self.ensure_one()
        if not (self.contract_start_date and self.contract_end_date and self.expiry_date):
            raise UserError("Fill in the contract start, contract end and expiry dates.")
        if self.expiry_date > self.contract_end_date:
            raise UserError("The permit expiry date cannot be after the contract end date.")

    # ------------------------------------------------------------------
    # Locking: an official record must not be edited freely
    # ------------------------------------------------------------------
    def write(self, vals):
        """Block edits to the official fields once the application is submitted.

        The system's own actions (DTCM approval, renewal) pass the context key
        ``permit_system_write`` to bypass the lock, so only the official
        workflow can change the dates of a submitted permit.
        """
        if not self.env.context.get('permit_system_write'):
            if any(f in vals for f in self.LOCKED_AFTER_SUBMIT) and any(p.state != 'draft' for p in self):
                raise UserError(
                    "This permit has been submitted, so its details are locked. "
                    "Use the DTCM actions or Renew Permit to change the dates.")
        return super().write(vals)

    # ------------------------------------------------------------------
    # Statechart operations
    # ------------------------------------------------------------------
    def action_submit_application(self):
        """StartingApplication -> verification -> UnderInspection.

        Requires a future expiry date, then runs the checks that belong to
        the permit type. If any check fails, an error is shown and the
        application stays in the draft so it can be corrected.
        """
        for p in self:
            if p.state != 'draft':
                raise UserError("Only a new application can be submitted.")
            if not p.expiry_date or p.expiry_date <= fields.Date.today():
                raise UserError("Enter an expiry date in the future before submitting.")
            if p.permit_type == 'individual':
                p.check_unit_eligibility()
                p.check_permit_limit()
            else:
                p.verify_owner_authorisation()
                p.validate_contract_period()
            p.state = 'under_inspection'
        return True

    def record_dtcm_update(self, status, decision_date=None, remarks=None):
        """Record a decision made by DTCM and move the permit to the matching state.

        :param status: one of the keys of DTCM_TRANSITIONS (e.g. 'Valid', 'Suspended')
        :param decision_date: date of the DTCM decision (defaults to today)
        :param remarks: optional DTCM remarks to store with the permit

        When a permit becomes Valid and has no issue date yet, the decision
        date is used as the issue date.
        """
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
            # System write: bypasses the lock on submitted permits.
            p.with_context(permit_system_write=True).write(vals)
        return True

    def send_reminder(self, days_before_expiry=30):
        """Valid -> ExpiringSoon, and notify the property manager.

        A reminder is only allowed within ``days_before_expiry`` days of the
        expiry date. A valid permit that is already past its expiry date is
        moved straight to Expired instead.
        """
        Notification = self.env['dwell.permit.notification']
        today = fields.Date.today()
        for p in self.filtered(lambda r: r.state == 'valid'):
            if not p.expiry_date:
                raise UserError("Set an expiry date before sending a reminder.")
            days_left = (p.expiry_date - today).days
            if days_left < 0:
                p.state = 'expired'
                continue
            if days_left > days_before_expiry:
                raise UserError(
                    "This permit expires in %d days. Reminders are only sent within %d days of expiry."
                    % (days_left, days_before_expiry))
            p.state = 'expiring_soon'
            Notification.create_notification(p, days_before_expiry)
        return True

    def renew_permit(self, new_expiry_date):
        """ExpiringSoon / Expired -> Valid once the renewal is approved.

        The new expiry date must be later than the current one.
        """
        for p in self:
            if p.state not in ('expiring_soon', 'expired'):
                raise UserError("Only permits that are expiring soon or expired can be renewed.")
            if p.expiry_date and new_expiry_date <= p.expiry_date:
                raise UserError("The new expiry date must be after the current one.")
            # System write: renewal is an official way to change the expiry date.
            p.with_context(permit_system_write=True).write(
                {'expiry_date': new_expiry_date, 'new_expiry_date': False, 'state': 'valid'})
        return True

    # ------------------------------------------------------------------
    # Button methods (called from the form view)
    # ------------------------------------------------------------------
    def action_dtcm_valid(self):
        """Button: DTCM approved the application, rectified a suspension or passed an inspection."""
        return self.record_dtcm_update('Valid')

    def action_dtcm_rejected(self):
        """Button: DTCM rejected the application after inspection."""
        return self.record_dtcm_update('Rejected')

    def action_dtcm_suspended(self):
        """Button: DTCM issued a suspension notice."""
        return self.record_dtcm_update('Suspended')

    def action_dtcm_closed(self):
        """Button: DTCM closed the permit (not rectified, or reopening inspection failed)."""
        return self.record_dtcm_update('Closed')

    def action_dtcm_reopen_requested(self):
        """Button: the issue was resolved and a reopening was requested."""
        return self.record_dtcm_update('ReopenRequested')

    def action_dtcm_reopening_inspection(self):
        """Button: the reopening fee was paid and DTCM started a new inspection."""
        return self.record_dtcm_update('ReopeningInspection')

    def action_send_reminder(self):
        """Button: send an expiry reminder for the selected permit."""
        return self.send_reminder()

    def action_renew(self):
        """Button: renew the permit using the New Expiry Date entered on the form."""
        for p in self:
            if not p.new_expiry_date:
                raise UserError("Enter the new expiry date first.")
            p.renew_permit(p.new_expiry_date)
        return True

    # ------------------------------------------------------------------
    # Scheduled job (runs daily through the cron record in permit_views.xml)
    # ------------------------------------------------------------------
    @api.model
    def _cron_check_expiry(self, days_before_expiry=30):
        """Mark permits past their expiry date as Expired, and remind the rest.

        Expired permits are handled first so a permit is never both reminded
        and expired in the same run.
        """
        today = fields.Date.today()
        expired = self.search([('state', 'in', ['valid', 'expiring_soon']),
                               ('expiry_date', '<', today)])
        expired.write({'state': 'expired'})
        soon = self.search([('state', '=', 'valid'),
                            ('expiry_date', '<=', today + timedelta(days=days_before_expiry))])
        soon.send_reminder(days_before_expiry)


class DwellPermitNotification(models.Model):
    """PermitExpiryNotification from the class diagram.

    A message addressed to a property manager about one permit that is
    approaching its expiry date. Created by ``DwellPermit.send_reminder``.
    """
    _name = 'dwell.permit.notification'
    _description = 'Permit Expiry Notification'
    _order = 'sent_date desc, id desc'

    permit_id = fields.Many2one('dwell.permit', string='Permit', required=True, ondelete='cascade')
    recipient_id = fields.Many2one('res.users', string='Recipient')
    message = fields.Char(string='Message', required=True)
    sent_date = fields.Datetime(string='Sent', default=fields.Datetime.now)
    is_read = fields.Boolean(string='Read', default=False)
    days_left = fields.Integer(string='Days Left', compute='_compute_days_left')

    @api.depends('permit_id.expiry_date')
    def _compute_days_left(self):
        """calculateDaysLeft(): days between today and the permit's expiry date."""
        today = fields.Date.today()
        for n in self:
            expiry = n.permit_id.expiry_date
            n.days_left = (expiry - today).days if expiry else 0

    @api.model
    def create_notification(self, permit, days_before_expiry=30):
        """createNotification(): create one reminder addressed to the permit's manager."""
        if permit.expiry_date:
            days = (permit.expiry_date - fields.Date.today()).days
            text = "Permit %s expires in %d day(s), on %s." % (permit.name, days, permit.expiry_date)
        else:
            text = "Permit %s is approaching its expiry date." % permit.name
        return self.create({
            'permit_id': permit.id,
            'recipient_id': permit.manager_id.id,
            'message': text,
        })

    def mark_as_read(self):
        """markAsRead(): flag the notification as read."""
        self.write({'is_read': True})
        return True