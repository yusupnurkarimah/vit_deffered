# -*- coding: utf-8 -*-
{
    'name': "vit_deffered",

    'summary': """
        Revenue and Cost Deffered
        """,

    'description': """
        Revenue and Cost Deffered
    """,

    'author': "yusup[vitraining.com]",
    'website': "http://www.vitraining.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','om_account_accountant'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/category.xml',
        'views/menu.xml',
        'views/templates.xml',
        'data/squence.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}