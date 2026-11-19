from odoo import models, fields, api

class FieldServiceStaff(models.Model):
    _name = 'field.service.staff'
    _description = 'Field Service Staff'

    name = fields.Char(string='Staff Name', required=True)
    status = fields.Char(string='Status', default='Available')
    task_ids = fields.One2many('service.tasks', 'staff_id', string='Assigned Tasks')


class ServiceTasks(models.Model):
    _name = 'service.tasks'
    _description = 'Service Tasks'

    name = fields.Char(string='Task Name', required=True)
    task_id_code = fields.Char(string='Task ID', required=True)
    estimated_duration = fields.Integer(string='Estimated Duration (min)')
    task_cost = fields.Float(string='Task Cost')
    description = fields.Text(string='Description')
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Priority', default='medium')
    scheduled_date = fields.Date(string='Scheduled Date')
    task_type = fields.Selection([
        ('cleaning', 'Cleaning Task'),
        ('maintenance', 'Maintenance Task')
    ], string='Task Type', default='cleaning')
    
    staff_id = fields.Many2one('field.service.staff', string='Assigned Staff')

    # Cleaning Task Fields
    checklist_details = fields.Text(string='Checklist Details')
    linen_change_required = fields.Boolean(string='Linen Change Required')
    inspection_passed = fields.Boolean(string='Inspection Passed')

    # Maintenance Task Fields
    equipment_needed = fields.Char(string='Equipment Needed')
    urgency_level = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency')
    ], string='Urgency Level', default='normal')
    technician_notes = fields.Text(string='Technician Notes')