from odoo import models, fields, api

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
        ('reject', 'Rejected')],
        string='State', copy=False, default='draft', tracking=True,
        help="Status of the hr request")
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

    def action_confirm(self):
        """Confirm Button"""
        self = self.sudo()
        self.write({'status': 'in_progress'})
        users = self.env.ref("hr_requests.group_hr_request_officer").users
        for user in users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary="Please Check the HR Request",
            )

    def action_reject(self):
        """Reject Button"""
        self.write({'status': 'reject'})


    def action_approval_hr(self):
        """HR Approval Button also write the user who Approved this button
        and Date he approved"""
        self.write({'status': 'approved', 'hr_user_id': self.env.user.id,
                    'hr_date': fields.Date.today()})
        users = self.env.ref("hr_requests.group_hr_request_second_approve").users
        for user in users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary="Please Check the HR Request",
            )

    def action_second_approve(self):
        """HR Approval Button also write the user who Approved this button
        and Date he approved"""
        self.write({'status': 'second_approved'})


    def action_ready(self):
        """ready Button"""
        self.write({'status': 'ready'})


# activity_obj = self.env['mail.activity']
# activity_type = self.env.ref('elfayrouz_update.mail_activity_type_waiting_approval_elfayrouz')
# model = self.env['ir.model']._get('account.move')
# company = self.env['res.company'].search([('elfayrouz_company', '=', True)])
#
# if not upcoming_invoices:
#     return True
#
# notify_group = self.env.ref('elfayrouz_update.elfayrouz_payment_user_group')
# users_to_notify = notify_group.users
#
# if not users_to_notify:
#     raise UserError("No users in the notification group!")
#
# for invoice in upcoming_invoices:
#     for user in users_to_notify:
#         activity_vals = {
#             'activity_type_id': activity_type.id,
#             'note': "مراجعة موعد سداد الفاتورة.",
#             'user_id': user.id,
#             'res_id': invoice.id,
#             'res_model_id': model.id,
#             'date_deadline': datetime.today().date(),
#         }
#         activity_obj.sudo().create(activity_vals)


# activity_to_do = order.env.ref('solace_updates.mail_act_solace_activity').id
# activity_users = order.env.ref('solace_updates.solace_normal_purchases_group').users
# activity_id = order.env['mail.activity'].search(
#     [('res_id', '=', order.id), ('user_id', 'in', activity_users.ids),
#      ('activity_type_id', '=', activity_to_do)])
# activity_id.action_feedback(feedback='Approved')







