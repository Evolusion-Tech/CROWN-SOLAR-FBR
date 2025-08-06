{
    'name': 'c',
    'version': '17.0',
    'category': '',
    'author': '',
    'summary': '',
    'description': """""",
    'depends': ['account','base'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
       'view/move_line.xml',
        'view/partner.xml',
        'view/account_config.xml',
        'view/sale_type.xml',
        'view/fbr_data.xml',
        'view/doc_type.xml',
        'view/item_code.xml',
         'view/uom.xml',
        'view/config.xml',
        'view/menu.xml',

    ],
    'assets': {
        'web.assets_frontend': [

        ],
        'web.assets_backend': [

            '/fbr_integration_fields/static/src/js/tax_totals_patch.js',
            '/fbr_integration_fields/static/src/xml/tax_totals_custom.xml',
            '/fbr_integration_fields/static/src/xml/fbr.xml',
            '/fbr_integration_fields/static/src/js/fbr_client.js',

            '/fbr_integration_fields/static/src/css/fields_width.css',
        ],
    },
    'sequence': -100,
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
