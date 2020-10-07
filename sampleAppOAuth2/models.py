from django.db import models
from django_mysql.models import ListTextField
from django.utils import timezone
from django.contrib.auth import (
    get_user_model
)
User = get_user_model()

class Bearer:
    def __init__(self, refreshExpiry, accessToken, tokenType, refreshToken, accessTokenExpiry, idToken=None):
        self.refreshExpiry = refreshExpiry
        self.accessToken = accessToken
        self.tokenType = tokenType
        self.refreshToken = refreshToken
        self.accessTokenExpiry = accessTokenExpiry
        self.idToken = idToken

class QBToken(models.Model):
    user = models.ForeignKey(User, db_column="user", on_delete=models.CASCADE, null=True)
    access_token = models.TextField(max_length=1000)
    refresh_token = models.TextField(max_length=1000)
    realmId = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.user

    # companyName
    # startDate
    # endDate
    # lastMonth
    # departmentsOfPL
    # sameDepartmentsOfPL
    # departmentsOfHC
    # staffLocation
class Status(models.TextChoices):
    QUEUED = 'Queued'
    RUNNING = 'Running'
    INCOMPLETED = 'Incompleted'
    COMPLETED = 'Completed'

class QBReport(models.Model):
    user = models.ForeignKey(User, db_column="user", on_delete=models.CASCADE, null=True)
    companyName = models.CharField(max_length=100, blank=True)
    accountingBasis = models.CharField(max_length=100, null=True, blank=True)
    fileName = models.CharField(max_length=100, null=True, blank=True)
    rollFileName = models.CharField(max_length=100, null=True, blank=True)
    startDate = models.CharField(max_length=100, null=True, blank=True)
    endDate = models.CharField(max_length=100, null=True, blank=True)
    lastMonth = models.CharField(max_length=100, null=True, blank=True)
    rollLastMonth = models.CharField(max_length=100, null=True, blank=True)

    departmentsOfPL = ListTextField(
        base_field=models.CharField(max_length=25),
        size=10,
        max_length=(25 * 10),
        null = True,
        blank = True
    )
    departmentsOfHC = ListTextField(
        base_field=models.CharField(max_length=25),
        size=10,
        max_length=(25 * 10),
        null = True,
        blank = True
    )
    staffLocation = ListTextField(
        base_field=models.CharField(max_length=25),
        size=10,
        max_length=(25 * 10),
        null = True,
        blank = True
    )
    sameDepartmentsOfPL = models.BooleanField(default=False)


    status = models.CharField(max_length=100, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    def __str__(self):
        return self.user.username + '->' + self.companyName
