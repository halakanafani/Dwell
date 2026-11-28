# dwell_management/__manifest__.py

{
    'name': 'Dwell - Holiday Home Management',
    'version': '19.0.1.0',
    'category': 'Real Estate',
    'summary': 'Short-Term Rental & DTCM Compliance System',
    'author': 'Supernova Team',
    'depends': ['base'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/rental_agreement_sequence.xml',
        'views/property_views.xml',
        'views/menus.xml',
        'views/booking.xml',
        'data/cron_data.xml',
        'views/rental_agreement_views.xml',
        'views/permit_views.xml',
        'report/rental_agreement_report.xml',
        'views/service_task_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dwell_management/static/src/css/dwell_theme.css',
        ],
    },
    'installable': True,
    'application': True,
}
