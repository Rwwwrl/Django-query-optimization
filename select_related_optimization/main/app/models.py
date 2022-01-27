from django.db import models

class ProductType(models.Model):

  type_name = models.CharField(max_length=100)


class Product(models.Model):

  name = models.CharField(max_length=100)
  product_type = models.ForeignKey(ProductType, related_name='products', on_delete=models.CASCADE)
