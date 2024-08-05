"""
This file is part of POPOPANEL.

@package     POPOPANEL is part of WHAT PANEL – Web Hosting Application Terminal Panel.
@copyright   2023-2024 Version Next Technologies and MadPopo. All rights reserved.
@license     BSL; see LICENSE.txt
@link        https://www.version-next.com
"""
from django.db import models



# class MyTable(models.Model):
#     # username = models.CharField(max_length=100)
#     # email = models.EmailField(max_length=100)
#     password = models.CharField(max_length=100, null=True)
#     domain_name = models.CharField(max_length=100, default='example.com')
#     php_version = models.CharField(max_length=10, default= '7.4')
    
    
#     def __str__(self):
#         return self.username
class test(models.Model):
    full_name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class Customer(models.Model):
    full_name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    email = models.EmailField()
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name

class Website(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    website_name = models.CharField(max_length=100)
    ftp_username = models.CharField(max_length=100)
    ftp_password = models.CharField(max_length=100)
    php_version = models.CharField(max_length=10)
    database_allowed = models.IntegerField()

    def __str__(self):
        return self.website_name


# dj/models.py

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, username, emailid, password=None):
        if not username:
            raise ValueError('The Username field is required')
        if not emailid:
            raise ValueError('The Email field is required')

        user = self.model(username=username, emailid=emailid)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, emailid, password=None):
        user = self.create_user(username, emailid, password)
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    username = models.CharField(max_length=100, unique=True)
    emailid = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # AbstractBaseUser includes password hashing
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['emailid']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin



# class User(models.Model):
#     username = models.CharField(max_length=100)
#     emailid = models.EmailField()
#     password = models.CharField(max_length=64)

#     def __str__(self):
#         return self.username