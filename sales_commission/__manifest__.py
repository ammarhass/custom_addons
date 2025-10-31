{
    'name': 'Nas Sale Commission',
    'version': '1.0',
    'category': 'Sales/Commission',
    'sequence': 105,
    'summary': "Manage your salespersons' commissions",
    'description': """
    """,
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_commission_views.xml',
        'views/commission_details_views.xml',
        'views/inherit_hr_employee_views.xml',
        'data/ir_cron.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
