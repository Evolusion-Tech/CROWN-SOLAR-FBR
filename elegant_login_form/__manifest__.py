# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Elegant Login Theme',
    'version': '17.0.1.0.0',
    "category": "Themes/Backend",
    'live_test_url': 'https://youtu.be/Bn4rGHAv_OI',
    'sequence': 1,
    'summary': """
        Web Login screen, New login design, Web Responsive login, Odoo Web Login Page, Web backend login, Odoo login, 
        Odoo SignUp Page, Odoo SignIn Page, Hide Powered By Odoo login screen, Login Page Background, Show Password Login Page,
        Show/Hide Password in login screen, Login Wallpaper Login Pages Wallpaper, Hide Password Login Page, Login Sign-up users,
        Odoo Login User Login Odoo, Odoo Simple Login Screen, Odoo Screen Login, Web Backend Authentication, Login / Signup Screen,
        Sign-up Odoo, Odoo Authentication Screen, SignUp Form Login, Remove Powered By Odoo, Hide Odoo, Simple login, Web SignUp,
        Background Web Login, View Password Login and Signup Page, Advance Login Advanced Pages, Elegant Login Elegant Form, 
        Customize Login Page Style, Hide Powered By Odoo, Login in Odoo, User Authentication Login Authentication, Remove Odoo,
        Sign In Odoo Sign In, SignIn Odoo SignIn, Sign-In Odoo Sign-In, Login Page Redirection, Remove Powered By Odoo Login Page,
        Login Screen Wallpaper, Social Login, Simple Authentication, Background Login Background, View Password Login Page, 
    """,
    'description': "The best design of the login form offers a welcoming and eye-catching login screen.",
    'author': 'Innoway',
    'maintainer': 'Innoway',
    'price': '20.0',
    'currency': 'EUR',
    'website': 'https://innoway-solutions.com',
    'license': 'OPL-1',
    'images': [
        'static/description/wallpaper.png'
    ],
    'depends': [
        'web'
    ],
    'data': [
        'views/login_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'elegant_login_form/static/src/scss/login.scss',
        ],
    },
    'demo': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
        
    ],
}
