{
    "name": "Edit Sequence No.",

    'version': "17.1",

    'category': "other",

    "summary": "User can easily edit number field.",

    'author': "INKERP",
    'website': 'https://www.inkerp.com/',
    "depends": ["sale", "purchase", "stock", "account"],

    "data": ["security/security.xml",
             'views/sale_order_view.xml',
             'views/purchase_order_view.xml',
             'views/account_move_view.xml',
             'views/stock_picking_view.xml'],

    'images': ['static/description/banner.gif'],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}
