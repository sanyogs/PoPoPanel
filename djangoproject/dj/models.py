from django.db import models



class MyTable(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100, null=True)
    domain_name = models.CharField(max_length=100, default='example.com')
    php_version = models.CharField(max_length=10, default= '7.4')
    
    
    def __str__(self):
        return self.username



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
        return self.full_name