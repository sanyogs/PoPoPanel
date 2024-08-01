#!/usr/bin/env python
"""
This file is part of POPOPANEL.

@package     POPOPANEL is part of WHAT PANEL – Web Hosting Application Terminal Panel.
@copyright   2023-2024 Version Next Technologies and MadPopo. All rights reserved.
@license     BSL; see LICENSE.txt
@link        https://www.version-next.com
"""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'popopanel.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
