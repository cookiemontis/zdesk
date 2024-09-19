ZDC = {
    'prod': {
        'ZDC': {
            'zdesk_url': 'https://Prod_Zendesk',
            'zdesk_email': '',
            'zdesk_password': '',
            'zdesk_token': True
        },
    },
    'sandbox': {
        'ZDC': {
            'zdesk_url': 'https://Dev_Zendesk',
            'zdesk_email': '',
            'zdesk_password': '',
            'zdesk_token': True
        },
    },
}


WHMCSC = {
    'prod': {
        'WHMCSC': {
            'username' : '',
            'password' : '',
            'accesskey' : '',
            'action' : 'OpenTicket',
            'deptid' : '1',
            'apiurl' : 'https://Prod_WHMCS/members/includes/api.php?',
        },
        'groups' : {
        'ZenDeskGroupID' : 'WHMCS_GroupID', #Ex.Technical Support
        'ZenDeskGroupID' : 'WHMCS_GroupID', #Ex.Sales
        },
    },
    'sandbox': {
        'WHMCSC': {
            'username' : '',
            'password' : '',
            'accesskey' : '',
            'action' : 'OpenTicket',
            'deptid' : '1',
            'apiurl' : 'https://Dev_WHMCS/members/includes/api.php?',
        },
        'groups' : {
         'ZenDeskGroupID' : 'WHMCS_GroupID', #Ex.Technical Support
         'ZenDeskGroupID' : 'WHMCS_GroupID', #Ex.Sales
        },
    },
}
