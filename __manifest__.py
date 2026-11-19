{
    'name': 'Dwell - Holiday Home Management',
    'version': '1.0',
    'category': 'Real Estate',
    'summary': 'Short-Term Rental & DTCM Compliance System',
    'author': 'Supernova Team',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/rental_agreement_sequence.xml',  # Generates automatic agreement numbers
        'views/property_views.xml',
        'views/booking.xml',
        'views/rental_agreement_views.xml',  # Rental Agreements and Agreement Templates
        'views/permit_views.xml',
        'report/rental_agreement_report.xml',  # Printable rental agreement PDF
    ],
    'installable': True,
    'application': True,
}