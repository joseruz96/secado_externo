# -*- coding: utf-8 -*-
{
    'name': "Secado Externo",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    'data': [
        'data/secado_sequence.xml',
    ],
        # always loaded
    'assets': {
        'web.report_assets_common': [
            'package_move/static/src/js/secado_recepcion.js',
        ],
        'web.assets_backend': [
            'package_move/static/src/js/secado_recepcion.js',
        ],
    'qweb': ['static/src/xml/secado_recepcion.xml'],
        # 'web.assets_qweb': [
        #     'package_move/static/src/css/style.css',
        # ],
        # 'web.report_assets_common': [
        #     'package_move/static/src/css/style.css',
        # ]
    },
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/secado_formulario.xml',
        'views/secado_recepcion.xml',
        'views/secado_paquetes.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
