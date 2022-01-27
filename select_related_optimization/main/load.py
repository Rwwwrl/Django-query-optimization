from app import models


def create():

  pt1 = models.ProductType.objects.create(type_name='type_name1')
  pt2 = models.ProductType.objects.create(type_name='type_name2')

  product1 = models.Product.objects.create(name='name1', product_type=pt1)
  product2 = models.Product.objects.create(name='name2', product_type=pt1)
  product3 = models.Product.objects.create(name='name3', product_type=pt1)
  product4 = models.Product.objects.create(name='name4', product_type=pt2)
  product5 = models.Product.objects.create(name='name5', product_type=pt2)
  product6 = models.Product.objects.create(name='name6', product_type=pt2)





