from odoo import models, fields, api


class FieldServiceStaff(models.Model):
    # Technical model name used in ORM queries, relations, and XML views
    _name = 'field.service.staff'
    # Human-readable description for Odoo metadata
    _description = 'Field Service Staff'
    # Field used as the display label when another record links to a staff member
    _rec_name = 'name'

    # Basic staff details
    name = fields.Char(string='Staff Name', required=True)
    role = fields.Selection([
        ('technician', 'Maintenance Technician'),
        ('cleaner', 'Housekeeping / Cleaner'),
        ('inspector', 'Property Inspector'),
        ('supervisor', 'Field Supervisor'),
    ], string='Role', required=True, default='technician')
    phone = fields.Char(string='Phone Number')
    email = fields.Char(string='Email')

    # Tracks whether the staff member can currently take a task
    availability_status = fields.Selection([
        ('available', 'Available'),
        ('busy', 'On Task'),
        ('off_duty', 'Off Duty'),
    ], string='Availability', default='available', required=True)

    # Standard Odoo field: false hides the record instead of deleting it
    active = fields.Boolean(default=True)

    # Reverse link: fetches all service.tasks rows where assigned_staff_id points to this staff member
    task_ids = fields.One2many('service.tasks', 'assigned_staff_id', string='Assigned Tasks')

    # Computed field (not stored in DB by default unless store=True is added)
    task_count = fields.Integer(string='Task Count', compute='_compute_task_count')

    @api.depends('task_ids')
    def _compute_task_count(self):
        # Loop over recordset safely (Odoo methods can receive multiple records at once)
        for record in self:
            record.task_count = len(record.task_ids)


class ServiceTasks(models.Model):
    _name = 'service.tasks'
    _description = 'Dwell Service & Maintenance Tasks'
    # Adds chatter message history (mail.thread) and scheduled activities (mail.activity.mixin)
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # Default sort order in list views: earliest scheduled_date first, highest priority first
    _order = 'scheduled_date asc, priority desc'

    # tracking=True logs field changes automatically in the record's chatter
    name = fields.Char(string='Task Title', required=True, tracking=True)
    task_type = fields.Selection([
        ('cleaning', 'Turnover Cleaning'),
        ('maintenance', 'Preventive Maintenance'),
        ('repair', 'Urgent Repair'),
        ('inspection', 'Check-in / Check-out Inspection'),
    ], string='Service Type', required=True, default='cleaning', tracking=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1', tracking=True)

    # Workflow stage of the task
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Many2one links this task to one property record (check exact model name with your teammate)
    property_id = fields.Many2one('dwell.property', string='Property', required=True, tracking=True)
    # Many2one links this task to one staff member
    assigned_staff_id = fields.Many2one('field.service.staff', string='Assigned Staff', tracking=True)

    scheduled_date = fields.Datetime(string='Scheduled Date', required=True, tracking=True)
    # readonly=True prevents manual editing; set automatically when marked done
    completion_date = fields.Datetime(string='Completion Date', readonly=True)
    estimated_hours = fields.Float(string='Estimated Duration (Hours)', default=1.0)
    description = fields.Text(string='Task Instructions / Issue Details')
    completion_notes = fields.Text(string='Completion Notes')

    # Button action: moves task to 'assigned' and marks staff 'busy'
    def action_assign(self):
        for record in self:
            record.state = 'assigned'
            if record.assigned_staff_id:
                record.assigned_staff_id.availability_status = 'busy'

    # Button action: moves task to 'in_progress'
    def action_start(self):
        for record in self:
            record.state = 'in_progress'

    # Button action: marks task 'done', stamps completion time, and frees up staff
    def action_done(self):
        for record in self:
            record.state = 'done'
            record.completion_date = fields.Datetime.now()
            if record.assigned_staff_id:
                record.assigned_staff_id.availability_status = 'available'

    # Button action: cancels task and frees up staff if they were assigned
    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
            if record.assigned_staff_id:
                record.assigned_staff_id.availability_status = 'available'