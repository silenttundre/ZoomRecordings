# Constant variables - Zoom OAuth credentials (replace with your actual credentials)
ZOOM_2_CLIENT_ID = "nfvZFnITqOha4nR0YDuow"
ZOOM_2_CLIENT_SECRET = "0FShl58rOB9szuHCyEQLsVjVYL1OYU6V"
ZOOM_2_ACCOUNT_ID = "CZvNsUtbTkCjQaHuOqRTxg"
ZOOM_2_TOKEN_URL = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ZOOM_2_ACCOUNT_ID}"
API_URL = "https://api.zoom.us/v2"
REDIRECT_URI = "https://cstu.edu"


# Add this to the imports or near the top of the script
COURSE_MAPPING_ZOOM2 = {
    'MB_CSE 590 Data Analytics': {
        'schedule': {
            'Wesdnesday': ['7:15PM-9:49PM'],
            'Saturday': ['12:45PM-2:39PM']
        },
        'folder_name': 'MB CSE 590 Data Analytics'
    },
    'MB 590 Business Law': {
        'schedule': {
            'Thursday': ['3:55PM-6:19PM'],
            'Saturday': ['8:55AM-10:39AM']
        },
        'folder_name': 'MB 590 Business Law'
    },
    'MB 590 Innovation in Fintech': {
        'schedule': {
            'Wesdnesday': ['3:55PM-6:19PM'],
            'Saturday': ['4:15PM-5:59PM']
        },
        'folder_name': 'MB 590 Fintech Innovation'
    },
    'MB 590 Sales Operations and Management': {
        'schedule': {
            'Tuesday': ['3:55PM-6:19PM'],
            'Saturday': ['2:35PM-4:20PM']
        },
        'folder_name': 'MB 590 Sales Operations'
    },
    'MB 590 AI and project management': {
        'schedule': {
            'Tuesday': ['7:25PM-9:49PM'],
            'Saturday': ['10:35AM-12:25PM']
        },
        'folder_name': 'MB 590 AI Project Management'
    }
}

# Add this to the imports or near the top of the script
COURSE_MAPPING_ZOOM1 = {
    'CSE_MB 600 Python for AI': {
        'schedule': {
            'Monday': ['3:55PM-6:30PM'],
            'Saturday': ['4:15PM-6:00PM']
        },
        'folder_name': 'CSE_MB 600 Python for AI'
    },
    'MB_CSE 590 Multi-Agent Systems (MAS) for Digital Marketing': {
        'schedule': {
            'Tuesday': ['7:20PM-9:40PM'],
            'Saturday': ['2:35AM-4:15AM']
        },
        'folder_name': 'MB_CSE 590 Multi-Agent Systems (MAS) for Digital Marketing'
    },
    'CSE_MB 642 GenAI': {
        'schedule': {
            'Thursday': ['3:55PM-6:19PM'],
            'Saturday': ['10:35AM-12:20PM']
        },
        'folder_name': 'CSE_MB 642 GenAI'
    },
    'CSE_MB 636 DevOps': {
        'schedule': {
            'Wedsnesday': ['7:25PM-9:40PM'],
            'Saturday': ['12:55PM-2:35PM']
        },
        'folder_name': 'CSE_MB 636 DevOps'
    },
    'CSE_MB 628  Machine Learning for NLP': {
        'schedule': {
            'Monday': ['7:25PM-9:49PM'],
            'Saturday': ['8:55AM-10:35AM']
        },
        'folder_name': 'CSE_MB 628  Machine Learning for NLP'
    }
}

DAY_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']