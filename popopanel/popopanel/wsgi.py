"""
This file is part of POPOPANEL.

@package     POPOPANEL is part of WHAT PANEL – Web Hosting Application Terminal Panel.
@copyright   2023-2024 Version Next Technologies and MadPopo. All rights reserved.
@license     BSL; see LICENSE.txt
@link        https://www.version-next.com
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'popopanel.settings')

application = get_wsgi_application()
