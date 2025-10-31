# -*- coding: utf-8 -*-
{
    'name': "Invoice Mail Reminder",

    'summary': """
        To add customization to Invoice Reminder""",

    'description': """
        Long description of module's purpose
    """,
    'author': "Kam",
    'website': "http://www.yourcompany.com",
    'category': 'Hidden',
    'version': '18.0.0.1',
    'depends': ['account','mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/invoice_reminder_tracker_views.xml',
        'views/account_move_views.xml',
        'data/ir_cron.xml',
        'data/mail_template.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install"': False,
    'application': True,
}