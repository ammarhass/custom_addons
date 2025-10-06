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
    'depends': ['hr', 'account', 'hr_holidays', 'base_accounting_kit'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/res_config_setting.xml',
        'views/asset_asset_form_view.xml',
        'views/asset_management_views.xml',
        'views/inherit_hr_employee_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install"': False,
    'application': True,
}