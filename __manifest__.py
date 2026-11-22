<<<<<<< HEAD
# dwell_management/__manifest__.py
=======

>>>>>>> 2ff131b06a072364bd885b0b395120c821922a1a
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
        'views/booking.xml',
<<<<<<< HEAD
        'data/cron_data.xml',
=======
        'views/rental_agreement_views.xml',
        'views/permit_views.xml',
        'report/rental_agreement_report.xml',
>>>>>>> 2ff131b06a072364bd885b0b395120c821922a1a
    ],

    'installable': True,
    'application': True,
}                       