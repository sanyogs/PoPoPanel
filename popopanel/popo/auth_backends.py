"""
This file is part of POPOPANEL.

@package     POPOPANEL is part of WHAT PANEL – Web Hosting Application Terminal Panel.
@copyright   2023-2024 Version Next Technologies and MadPopo. All rights reserved.
@license     BSL; see LICENSE.txt
@link        https://www.version-next.com
"""
# dj/auth_backends.py

import hashlib
from django.contrib.auth.backends import BaseBackend
from popo.models import User

class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if user.password == hashed_password:
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
