from django.db import models


class SomeModel(models.Model):

  field1 = models.CharField(max_length=100)
  field2 = models.CharField(max_length=100)
  field3 = models.CharField(max_length=100)

