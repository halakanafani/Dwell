
{
    'name': 'Dwell - Holiday Home Management',
    'version': '1.0',
    'category': 'Real Estate',
    'summary': 'Short-Term Rental & DTCM Compliance System',
    'author': 'Supernova Team',
    'depends': ['base'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/rental_agreement_sequence.xml',
        'views/property_views.xml',
        'views/booking.xml',
        'views/rental_agreement_views.xml',
        'views/permit_views.xml',
        'report/rental_agreement_report.xml',
    ],

    'installable': True,
    'application': True,
}                       