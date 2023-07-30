{
    "name": "Custom Module",
    "version": "16.0.1.0.0",
    "category": "Hidden",
    "description": """
Publish your customers as business references on your website to attract new potential prospects.
""",
    "summary": "Publish your customer references",
    "website": "https://github.com/royaurelien",
    "author": "Aurelien ROY",
    "mainteners": ["Aurelien ROY"],
    "depends": [
        "base",
        "contacts",
    ],
    # 'external_dependencies': {
    #     'python': ['cryptography']
    # },
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        # 'report/report.xml',
        "views/new_model.xml",
        "views/res_partner.xml",
        "wizard/wizard.xml",
        "views/menu.xml",
    ],
    "demo": [
        "demo/res_partner.xml",
        "demo/new_model.xml",
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'custom_module/static/src/scss/custom.scss',
    #     ],
    #     'web.assets_frontend': [
    #         'custom_module/static/src/js/custom.js',
    #     ],
    #     'web.assets_qweb': [
    #         'custom_module/static/src/xml/**/*',
    #     ],
    # },
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}
