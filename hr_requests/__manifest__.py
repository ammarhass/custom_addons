# -*- coding: utf-8 -*-
{
    'name': "Hr Requests",

    'summary': """
        To manage the hr requests""",

    'description': """
        Long description of module's purpose
    """,
    'author': "Kam",
    'website': "http://www.yourcompany.com",
    'category': 'Hidden',
    'version': '18.0.0.1',
    'depends': ['hr', 'mail', 'equipment_request_it_operations'],
    'data': [
        'security/ir.model.access.csv',
        'security/user_groups.xml',
        'views/hr_requests_views.xml',
        'views/software_license_view.xml',
        'views/hr_employee_views.xml',
        'views/employee_section_views.xml',
        'views/menus.xml',
        'data/mail_activity.xml',
        'data/email_template.xml',
        'report/hr_letter_report.xml',
        'report/excperience_certificate_report.xml',
        'report/hr_letter_report_visa.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install"': False,
    'application': True,
}