# Select_related

```python
# models.py
class ProductType(models.Model):

  type_name = models.CharField(max_length=100)


class Product(models.Model):

  name = models.CharField(max_length=100)
  product_type = models.ForeignKey(ProductType, related_name='products', on_delete=models.CASCADE)
```

**select_related** - джанго не знает заранее понадобится ли нам связи с другой таблицей или нет

```python
Product.objects.all()
```

```sql
SELECT "app_product"."id",
       "app_product"."name",
       "app_product"."product_type_id"
  FROM "app_product"
 LIMIT 21
```

Мы видим, что в этом запросе нет _join_, у нас нет информации для **_product_type_**, если мы все же захотим получить эту информацию и мы обратимся _product.product_type_, произойдет еще один запрос.

**Вопрос:** мы хотим получить для каждого _product_ его _product.type_name_

Если бы мы делали как обычно:

```python
for product in Product.objects.all():
  print(product.product_type.type_name)
```

То пришло бы огромное количество запросов

```sql
SELECT "app_product"."id",
       "app_product"."name",
       "app_product"."product_type_id"
  FROM "app_product"

Execution time: 0.000000s [Database: default]
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 1
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name1
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 1
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name1
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 1
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name1
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 2
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name2
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 2
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name2
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 2
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name2
```

**Сколько тут запросов?**
Количество _product_ + 1, это знаменитая проблема **N+1**.
Как бы мы написали такой запрос на sql?

```sql
SELECT  "app_product_type"."type_name",
        "app_product"."id",
        "app_product"."name",
        "app_product"."product_type_id"
  FROM "app_product" INNER JOIN "app_product_type"
  ON "app_product"."product_type_id" = "app_product_type"."id"
```

То есть заранее одним запросом, при помощи _join`a_, получили все данные для модели product, и тогда наша задача сводится к **1 запросу!**
Именно эту проблему и решает **_select_related_**
**Правильный запрос** будет выглядеть так:

```python
for product in Product.objects.select_related('product_type').all():
  print(product.product_type.type_name)
```

```sql
SELECT "app_product"."id",
       "app_product"."name",
       "app_product"."product_type_id",
       "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_product"
 INNER JOIN "app_producttype"
    ON ("app_product"."product_type_id" = "app_producttype"."id")
```

**Все**, у нас не будет никаких дополнительных запросов.

> Очевидно, это нужно использовать, когда мы заранее знаем, что нам нужны данные из связанной таблицы

### Задача

Для каждого _product_ выбрать только _type_name_ из связанной таблицы.

**Ответ:**

```python
for product in Product.objects.select_related('product_type').only('product_type__type_name'):
    print(product.product_type.type_name)
```

```sql
SELECT "app_product"."id",
       "app_product"."product_type_id",
       "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_product"
 INNER JOIN "app_producttype"
    ON ("app_product"."product_type_id" = "app_producttype"."id")
```

> **_Only сам по себе не содержит в себе select_related_**

```python
for product in Product.objects.only('product_type__type_name'):
  print(product.product_type.type_name)
```

```sql
SELECT "app_product"."id",
       "app_product"."product_type_id"
  FROM "app_product"

Execution time: 0.000000s [Database: default]
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 1
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name1
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 1
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name1
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 1
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name1
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 2
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name2
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 2
 LIMIT 21

Execution time: 0.000000s [Database: default]
type_name2
SELECT "app_producttype"."id",
       "app_producttype"."type_name"
  FROM "app_producttype"
 WHERE "app_producttype"."id" = 2
 LIMIT 21
```

> **_Но, values сам по содержит в себе select_related_**

```python
for product in Product.objects.values('product_type__type_name'):
  print(product['product_type__type_name'])
```

```sql
SELECT "app_producttype"."type_name"
  FROM "app_product"
 INNER JOIN "app_producttype"
    ON ("app_product"."product_type_id" = "app_producttype"."id")
```

> select_related также поддерживает обращение к полям другой табилицы через **\_\_**

Если бы у _ProductType_ было еще одно поле _fk_to_another_model_, которое являлось бы внешним ключом к третьей таблице, которая в свою очередь содержила бы поле _another_model_name_. Если бы для каждого _product_ нам нужно было бы получить это поле _another_model_name_, мы бы сделали так:

```python
for product in Product.objects.select_related('product_type__fk_to_another_model'):
  print(product.product_type.fk_to_another_model.another_model_name)
```

Тут был бы **1** запрос с двумя _join`ами_.
