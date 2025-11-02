# -*- coding: utf-8 -*-
{
    'name': "Nas Update",

    'summary': """
        To add customization to Nas Compnay""",

    'description': """
        Long description of module's purpose
    """,
    'author': "Kam",
    'website': "http://www.yourcompany.com",
    'category': 'Hidden',
    'version': '18.0.0.1',
    'depends': ['hr', 'account', 'hr_holidays', 'base_accounting_kit', 'project', 'helpdesk'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'report/project_task_report.xml',
        'views/res_company.xml',
        'views/res_config_setting.xml',
        'views/asset_asset_form_view.xml',
        'views/asset_management_views.xml',
        'views/inherit_hr_employee_views.xml',
        'views/project_project_view.xml',
        'views/service_type_views.xml',
        'views/res_partner_views.xml',
        'views/project_task_views.xml',
        'views/unit_type_views.xml',
        'views/employee_team_views.xml',
        'views/task_type_views.xml',
        'views/project_task_portal.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_ticket_type_views.xml',
        'views/incoming_mail_configuration.xml',
        'views/hr_leave_type.xml',
        'views/hr_leave.xml',
        'wizard/task_notes_wizard_views.xml',
        'data/ir_sequence.xml',
        'data/email_template.xml',
        'data/email_activity.xml',

    ],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install"': False,
    'application': True,
}