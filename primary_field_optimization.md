# Only, values, values_list

```python
# models.py
class SomeModel(models.Model):

  field1 = models.CharField(max_length=100)
  field2 = models.CharField(max_length=100)
  field3 = models.CharField(max_length=100)
```

1. **_Only_** - выбрать только те поля, которые нам нужны, при этом возвращается _Queryset / instance_.
   **НО!**, если дальше во вьюшке нам потребуется поле, которое мы не загрузили сразу, то выполнится **еще один** запрос. В таком случае, оптимизации никакой нет.

```python
class SomeModel(models.Model):

  field1 = models.CharField(max_length=100)
  field2 = models.CharField(max_length=100)
  field3 = models.CharField(max_length=100)
```

```python
SomeModel.objects.only('field1').first()
# На выходе:
<SomeModel: SomeModel object (1)>
```

```sql
SELECT "app_somemodel"."id",
       "app_somemodel"."field1"
  FROM "app_somemodel"
 ORDER BY "app_somemodel"."id" ASC
 LIMIT 1
```

При этом следующий **_only_** перекрывает предыдуший

```python
SomeModel.objects.only('field1').only('field2').first()
```

```sql
SELECT "app_somemodel"."id",
       "app_somemodel"."field2"
  FROM "app_somemodel"
 ORDER BY "app_somemodel"."id" ASC
 LIMIT 1
```

Но, если мы используем **_only_**, то данные загружаются в память сразу, это уже не _LazyObject_

```python
sm = SomeModel.objects.only('field1').first()
# и тут сразу же произошел запрос
```

```sql
SELECT "app_somemodel"."id",
       "app_somemodel"."field1"
  FROM "app_somemodel"
 ORDER BY "app_somemodel"."id" ASC
 LIMIT 1
```

2. **_values_** - мы получаем только те поля, что нам нужны, но возвращаемый результат теперь не _instance/Queryset_, а обычный словарь -> Следовательно, если дальше во вьюшке мы обратимся к полю, которое мы не закешировали изначально, будет ошибка. Есть вариант изначально так писать.

```python
SomeModel.objects.values('field1', 'field2').first()
# На выходе:
{'field1': 'field10', 'field2': 'field20'}
```

```sql
SELECT "app_somemodel"."field1",
       "app_somemodel"."field2"
  FROM "app_somemodel"
 ORDER BY "app_somemodel"."id" ASC
 LIMIT 1
```

3. **values_list** - тоже самое что и **_values_**, только мы получаем не словари, а кортежи. Это можем быть полезно если мы хотим получить список всех *title* в бд

```python
SomeModel.objects.values_list('field1', 'field2').first()
# На выходе:
('field10', 'field20')
```
