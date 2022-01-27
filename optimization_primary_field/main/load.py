from app import models


def create():
  for i in range(10):
    models.SomeModel.objects.create(
      field1=f'field1{i}',
      field2=f'field2{i}',
      field3=f'field3{i}',
    )






