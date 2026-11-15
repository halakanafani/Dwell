# dwell_management/__manifest__.py
{
    'name': 'Dwell - Holiday Home Management',
    'version': '19.0.1.0',
    'category': 'Real Estate',
    'summary': 'Short-Term Rental & DTCM Compliance System',
    'author': 'Supernova Team',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/property_views.xml',
        'views/booking.xml',
        'data/cron_data.xml',
    ],
    'installable': True,
    'application': True,
}