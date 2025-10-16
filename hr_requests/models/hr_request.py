from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError



class HrRequest(models.Model):
    _name = "hr.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "HR Request"

    name = fields.Char(compute='_compute_name',
                       help="Auto-generated field based on record's ID")
    request_type = fields.Selection([
        ('new_hire', 'New Hire Process'),
        ('replace', 'Replacement Request'),
        ('hr_letter', 'HR Letter'),
        ('embassy_letter', 'Embassy Letter'),
        ('experience_letter', 'Experience Letter'),
        ('training_request', 'Training Request')], string='Request Type',
        copy=False, default='hr_letter', required=True,
        help="Type of HR Request")
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id,
                                       required=True,
                                       help="Employee requesting the equipment")
    department_id = fields.Many2one('hr.department', string='Department', default=lambda self: self.env.user.employee_id.department_id,
                                         help="Department of the Requester")
    job_position_id = fields.Many2one('hr.job', string='Job Position', default=lambda self: self.env.user.employee_id.job_id,
                                      help="Job position of the employee")
    user_id = fields.Many2one('res.users', string='User',
                                    default=lambda self: self.env.user,
                                    help="User who created the equipment "
                                         "request")
    created_user_id = fields.Many2one('res.users', string='Created By',
                                      default=lambda self: self.env.user,
                                      help="User who created the equipment "
                                           "request")
    create_date = fields.Date(string='Created Date',
                              help="Date when the hr "
                                   "request was created")
    hr_user_id = fields.Many2one('res.users', string='HR Manager',
                                 help="HR Manager who approves the hr "
                                      "request")
    hr_date = fields.Date(string='HR Approved Date',
                          help="Date when the HR Manager approved the hr"
                               "request")

    company_id = fields.Many2one('res.company', string='Company',
                                      default=lambda self: self.env.company,
                                      help="Company of the employee")

    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Waiting for Approval of HR'),
        ('approved', 'Approved'),
        ('second_approved', 'second Approved'),
        # ('ready', 'Ready To Collect'),
        ('reject', 'Rejected'),
        ('replaced', 'Replace')],
        string='State', copy=False, default='draft', tracking=True,
        help="Status of the hr request")

    source_location_id = fields.Many2one('stock.location',
                                         string='Source Location',
                                         help="Location from where the "
                                              "equipment"
                                              "will be sourced")
    destination_location_id = fields.Many2one('stock.location',
                                              string='Destination Location',
                                              help="Location where the "
                                                   "equipment"
                                                   "will be sent")

    # status = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('approved', 'Approved'),
    #     ('reject', 'Rejected')],
    #     string='State', copy=False, default='draft', tracking=True,
    #     help="Status of the hr request")


    directed_to = fields.Char()
    full_name = fields.Char()
    national_id = fields.Char()
    title = fields.Char()
    starting_date = fields.Date()
    salary = fields.Monetary()
    Social_insurance_number = fields.Char()
    travel_date_from = fields.Date()
    travel_date_to = fields.Date()
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id)

    emp_id = fields.Many2one('hr.employee')
    employee_code = fields.Char()
    arabic_name = fields.Char()
    mobile_num = fields.Char(compute='_compute_employee_data', store=True, readonly=False)
    employee_email = fields.Char(compute='_compute_employee_data', store=True, readonly=False)
    emp_department_id = fields.Many2one('hr.department', compute='_compute_employee_data', store=True, readonly=False)
    emp_position_id = fields.Many2one('hr.job', compute='_compute_employee_data', store=True, readonly=False)
    emp_director_manager_id = fields.Many2one('hr.employee', compute='_compute_employee_data', store=True, readonly=False)
    emp_director_id = fields.Many2one('hr.employee', compute='_compute_employee_data', store=True, readonly=False)
    joining_date = fields.Date(compute='_compute_employee_data', store=True, readonly=False)

    emp_section = fields.Char()
    section_id = fields.Many2one('employee.section')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    nationality = fields.Many2one('res.country')
    government = fields.Char()
    new_hire_status = fields.Selection([('active', 'Active')])
    email_creation = fields.Boolean()
    laptop = fields.Boolean()
    mousepad = fields.Boolean()
    headset = fields.Boolean()
    mouse = fields.Boolean()
    monitor_stand = fields.Boolean()
    mobilephone = fields.Boolean()
    keyboard = fields.Boolean()
    monitor = fields.Boolean()
    software_id = fields.Many2many('software.licenses')
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    notes = fields.Text()
    replacement_reason = fields.Text()
    replacement_note = fields.Text()
    emp_replacement_id = fields.Many2one('hr.employee')
    product_replacement_ids = fields.One2many('replacement.products', 'request_id')
    hr_request_internal_ids = fields.One2many('stock.picking',
                                             'hr_request_id',
                                             string='Internal Orders',
                                             help="The internal orders "
                                                  "related to"
                                                  "this hr request.")



    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.emp_replacement_id and record.request_type == 'replace':
            if record.emp_replacement_id.assigned_product_ids:
                product_lines = []
                for rec in record.employee_id.assigned_product_ids:
                    product_lines.append((0, 0, {
                        'product_id': rec.product_id.id,
                        'assign_date': rec.assign_date,
                        'request_id': record.id,
                        'quantity': rec.quantity,
                        'product_uom_id': rec.product_uom_id.id,
                        'description': rec.description
                    }))
                record.product_replacement_ids = product_lines
        return record

    @api.depends('emp_id')
    def _compute_employee_data(self):
        for record in self:
            if record.emp_id:
                record.mobile_num = record.emp_id.mobile_phone
                record.employee_email = record.emp_id.work_email
                record.emp_department_id = record.emp_id.department_id
                record.emp_position_id = record.emp_id.job_id
                record.emp_director_manager_id = record.emp_id.parent_id
                record.emp_director_id = record.emp_id.coach_id
                record.joining_date = record.emp_id.joining_date
                record.employee_code = record.emp_id.employee_code
                record.section_id = record.emp_id.section_id
            else:
                # Clear fields if no employee selected
                record.mobile_num = False
                record.employee_email = False
                record.emp_department_id = False
                record.emp_position_id = False
                record.emp_director_manager_id = False
                record.emp_director_id = False
                record.joining_date = False
                record.employee_code = False

    @api.onchange('employee_code')
    def _onchange_emp_id(self):
        for record in self:
            if record.employee_code:
                if record.employee_code:
                    employee = self.env['hr.employee'].search([
                        ('employee_code', '=', record.employee_code)
                    ], limit=1)
                    record.emp_id = employee.id if employee else False
                else:
                    record.emp_id = False


    @api.depends('request_type', 'employee_id')
    def _compute_name(self):
        """ _rec_name = Employee Name + Request Type + Creation Date"""
        for record in self:
            record.name = str(record.employee_id.name) + ' - ' + str(
                record.request_type) + ' - ' + str(
                fields.date.today())

    def get_recipient_partner_ids(self):
        group = self.env.ref('hr_requests.group_hr_request_officer')
        partner_ids = group.users.mapped('partner_id').ids
        return ','.join(str(pid) for pid in partner_ids)

    def get_second_approval_recipient_ids(self):
        group = self.env.ref('hr_requests.group_hr_request_second_approve')
        partner_ids = group.users.mapped('partner_id').ids
        return ','.join(str(pid) for pid in partner_ids)


    def action_confirm(self):
        """Confirm Button"""
        self = self.sudo()
        self.write({'status': 'in_progress'})
        hr_mail_template = self.env.ref('hr_requests.send_hr_request_mail_hr_approve')
        hr_mail_template.send_mail(self.id, force_send=True, email_values={'res_id': self.id})

        activity_type = self.env.ref('hr_requests.mail_act_first_approve')
        model = self.env['ir.model']._get('hr.request')
        activity_obj = self.env['mail.activity']

        users = self.env.ref("hr_requests.group_hr_request_officer").users
        for user in users:
            if user:
                activity_vals = {
                    'activity_type_id': activity_type.id,
                    'note': "for reviewing Hr Request",
                    'user_id': user.id,
                    'res_id': self.id,
                    'res_model_id': model.id,
                    'date_deadline': datetime.today().date(),
                }
                activity_obj.sudo().create(activity_vals)

    def action_reject(self):
        """Reject Button"""
        self.write({'status': 'reject'})


    def action_approval_hr(self):
        """HR Approval Button also write the user who Approved this button
        and Date he approved"""
        self.write({'status': 'approved', 'hr_user_id': self.env.user.id,
                    'hr_date': fields.Date.today()})
        second_approve_mail_template = self.env.ref('hr_requests.send_hr_request_mail_second_approve')
        second_approve_mail_template.send_mail(self.id, force_send=True, email_values={'res_id': self.id})

        activity_to_do = self.env.ref('hr_requests.mail_act_first_approve').id
        activity_users = self.env.ref("hr_requests.group_hr_request_officer").users
        activity_id = self.env['mail.activity'].search(
            [('res_id', '=', self.id), ('user_id', 'in', activity_users.ids),
             ('activity_type_id', '=', activity_to_do)])
        activity_id.action_feedback(feedback='Approved')
        activity_type = self.env.ref('hr_requests.mail_act_second_approve')
        model = self.env['ir.model']._get('hr.request')
        activity_obj = self.env['mail.activity']

        users = self.env.ref("hr_requests.group_hr_request_second_approve").users
        for user in users:
            if user:
                activity_vals = {
                    'activity_type_id': activity_type.id,
                    'note': "for reviewing Hr Request",
                    'user_id': user.id,
                    'res_id': self.id,
                    'res_model_id': model.id,
                    'date_deadline': datetime.today().date(),
                }
                activity_obj.sudo().create(activity_vals)

    def action_second_approve(self):
        """HR Approval Button also write the user who Approved this button
        and Date he approved"""
        self.write({'status': 'second_approved'})
        second_approve_mail_template = self.env.ref('hr_requests.send_hr_request_employee_approve')
        second_approve_mail_template.send_mail(self.id, force_send=True, email_values={'res_id': self.id})

        activity_to_do = self.env.ref('hr_requests.mail_act_second_approve').id
        activity_users = self.env.ref("hr_requests.group_hr_request_second_approve").users
        activity_id = self.env['mail.activity'].search(
            [('res_id', '=', self.id), ('user_id', 'in', activity_users.ids),
             ('activity_type_id', '=', activity_to_do)])
        activity_id.action_feedback(feedback='Approved')



    def action_ready(self):
        """ready Button"""
        self.write({'status': 'ready'})


    def action_internal_transfer(self):
        if not self.source_location_id:
            raise UserError(_('Source Location is not defined'))
        if not self.destination_location_id:
            raise UserError(_('Destination Location is not defined'))
        picking_type_id = self.env['stock.picking.type'].search(
            [('code', '=', 'internal')])
        if not picking_type_id:
            picking_type_id = self.env['stock.picking.type'].create({
                'name': 'Internal Transfers',
                'code': 'internal',
                'sequence_code': 'INT',
            })
        move_vals = {
            'picking_type_id': picking_type_id.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'hr_request_id': self.id,
        }
        picking = self.env['stock.picking'].create(move_vals)
        for value in self.product_replacement_ids.filtered(lambda x: x.replace == True):
            self.env['stock.move'].create({
                'picking_id': picking.id,
                'name': value.product_id.name,
                'product_id': value.product_id.id,
                'product_uom_qty': value.quantity,
                'product_uom': value.product_id.uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
            })
        picking.action_confirm()
        picking.action_assign()
        self.write({'status': 'replaced'})

    def action_view_internal_transfer(self):
        picking_id = self.env['stock.picking'].search([
            ('picking_type_id.code', '=', 'internal'),
            ('location_id', '=', self.source_location_id.id),
            ('location_dest_id', '=', self.destination_location_id.id),
            ('hr_request_id', '=', self.id)
        ], limit=1, order='create_date desc')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfer',
            'view_mode': 'form',
            'target': 'current',
            'res_model': 'stock.picking',
            'res_id': picking_id.id
        }



