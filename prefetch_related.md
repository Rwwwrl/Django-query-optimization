# Prefetch_related

```python
# models.py
class Topping(models.Model):
  name = models.CharField(max_length=100)

class Pizza(models.Model):
  name = models.CharField(max_length=100)
  toppings = models.ManyToManyField(Topping)

  def get_toppings(self):
    return [topping.name for topping in self.toppings.all()]
```

**Задача:** для каждой _pizza_ получить имена _topping-ов_:
Как мы бы делали раньше:

```python
for pizza in Pizza.objects.all():
  print(pizza.get_toppings())
```

И получили

```sql
SELECT "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"

Execution time: 0.000000s [Database: default]
SELECT "app_topping"."id",
       "app_topping"."name"
  FROM "app_topping"
 INNER JOIN "app_pizza_toppings"
    ON ("app_topping"."id" = "app_pizza_toppings"."topping_id")
 WHERE "app_pizza_toppings"."pizza_id" = 1

Execution time: 0.000000s [Database: default]
['topping_name1', 'topping_name2', 'topping_name3']
SELECT "app_topping"."id",
       "app_topping"."name"
  FROM "app_topping"
 INNER JOIN "app_pizza_toppings"
    ON ("app_topping"."id" = "app_pizza_toppings"."topping_id")
 WHERE "app_pizza_toppings"."pizza_id" = 2

Execution time: 0.015621s [Database: default]
['topping_name1', 'topping_name2', 'topping_name3']
SELECT "app_topping"."id",
       "app_topping"."name"
  FROM "app_topping"
 INNER JOIN "app_pizza_toppings"
    ON ("app_topping"."id" = "app_pizza_toppings"."topping_id")
 WHERE "app_pizza_toppings"."pizza_id" = 3
```

**Сколько мы тут получили запросов?**
**N + 1** - 1 для получения всех _pizza_ и по одному для выборки всех _toppings_ для каждой _pizza_.
**Правильное решение:**

```python
for pizza in Pizza.objects.prefetch_related('toppings').all():
  print(pizza.get_toppings())
```

```sql
SELECT "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"

Execution time: 0.000000s [Database: default]
SELECT ("app_pizza_toppings"."pizza_id") AS "_prefetch_related_val_pizza_id",
       "app_topping"."id",
       "app_topping"."name"
  FROM "app_topping"
 INNER JOIN "app_pizza_toppings"
    ON ("app_topping"."id" = "app_pizza_toppings"."topping_id")
 WHERE "app_pizza_toppings"."pizza_id" IN (1, 2, 3)
```

Все что изменилось, это мы сразу, одним запросом, получили все записи из таблицы _toppings_. Информация для каждой _pizza_ берется именно из этого закешированного результата

<!-- **Но тут есть проблема**. Кеширование таблиц в _prefetch_related_ работает после выполнения основого кварисета. Если к получившимуся результату мы применяем любые чейн методы, то **никакого** смысла от _prefetch_related_ смысла нет.

```python
pizzas = Pizza.objects.prefetch_related('toppings').all()
[pizza.toppings.filter(name='topping_name1') for pizza in pizzas]
``` -->

### Добавляем ресторан

```python
# manage.py
class Topping(models.Model):
  name = models.CharField(max_length=100)

class Pizza(models.Model):
  name = models.CharField(max_length=100)
  toppings = models.ManyToManyField(Topping)

  def get_toppings(self):
    return [topping.name for topping in self.toppings.all()]

class Restaurant(models.Model):
  pizzas = models.ManyToManyField(Pizza, related_name='restaurants')
  best_pizza = models.ForeignKey(Pizza, related_name='championed_by', on_delete=models.CASCADE)
```

**Задача:** мы хотим получить для _best_pizza_ имена всех _toppings_.
**Решение:**

1. Первым запросом мы _join-им_ таблицы _Restaurant_ и _Pizza_ при помощи _select_related_ и получаем данные для инстанса _restaurant_
2. Вторым запросом мы кешируем всю таблицу _Topping_

```python
restaurant = Restaurant.objects.select_related('best_pizza').prefetch_related('best_pizza__toppings').first()
restaurant.best_pizza.get_toppings()
```

```sql
SELECT "app_restaurant"."id",
       "app_restaurant"."best_pizza_id",
       "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_restaurant"
 INNER JOIN "app_pizza"
    ON ("app_restaurant"."best_pizza_id" = "app_pizza"."id")
 ORDER BY "app_restaurant"."id" ASC
 LIMIT 1

Execution time: 0.000000s [Database: default]
SELECT ("app_pizza_toppings"."pizza_id") AS "_prefetch_related_val_pizza_id",
       "app_topping"."id",
       "app_topping"."name"
  FROM "app_topping"
 INNER JOIN "app_pizza_toppings"
    ON ("app_topping"."id" = "app_pizza_toppings"."topping_id")
 WHERE "app_pizza_toppings"."pizza_id" IN (1)
```

**Задача:** мы хотим получить для каждой _pizza_ в _pizzas_ имена всех _toppings_
**Решение:**

1. Первым запросом мы получим данные для инстанса _restaurant_
2. Вторым запросом мы закешируем всю таблицу _Pizza_
3. Третьим запросом мы закешируем всю таблицы _Topping_

```python
restaurant = Restaurant.objects.prefetch_related('pizzas', 'pizzas__toppings').first()
for pizza in restaurant.pizzas.all():
  print(pizza.get_toppings())
```

```sql
SELECT "app_restaurant"."id",
       "app_restaurant"."best_pizza_id"
  FROM "app_restaurant"
 ORDER BY "app_restaurant"."id" ASC
 LIMIT 1

Execution time: 0.000000s [Database: default]
SELECT ("app_restaurant_pizzas"."restaurant_id") AS "_prefetch_related_val_restaurant_id",
       "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"
 INNER JOIN "app_restaurant_pizzas"
    ON ("app_pizza"."id" = "app_restaurant_pizzas"."pizza_id")
 WHERE "app_restaurant_pizzas"."restaurant_id" IN (1)

Execution time: 0.000000s [Database: default]
SELECT ("app_pizza_toppings"."pizza_id") AS "_prefetch_related_val_pizza_id",
       "app_topping"."id",
       "app_topping"."name"
  FROM "app_topping"
 INNER JOIN "app_pizza_toppings"
    ON ("app_topping"."id" = "app_pizza_toppings"."topping_id")
 WHERE "app_pizza_toppings"."pizza_id" IN (1, 2)

Execution time: 0.000000s [Database: default]
```

### Prefetch

**Задача:** для _pizza_ получить для каждого _restaurant_ получить _best_pizza_
**Решение, 1 вариант, без prefetch:**

1. Первым запросом мы получаем данные по инстансу _pizza_
2. Вторым запросом мы получаем данные по всей таблице _Restaurants_
3. Третьим запросом мы получаем данные по всей таблицу для _Pizza_

```python
pizza = Pizza.objects.prefetch_related('restaurants', 'restaurants__best_pizza').first()
for restaurant in pizza.restaurants.all():
  print(restaurant.best_pizza)
```

```sql
SELECT "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"
 ORDER BY "app_pizza"."id" ASC
 LIMIT 1

Execution time: 0.000000s [Database: default]
SELECT ("app_restaurant_pizzas"."pizza_id") AS "_prefetch_related_val_pizza_id",
       "app_restaurant"."id",
       "app_restaurant"."best_pizza_id"
  FROM "app_restaurant"
 INNER JOIN "app_restaurant_pizzas"
    ON ("app_restaurant"."id" = "app_restaurant_pizzas"."restaurant_id")
 WHERE "app_restaurant_pizzas"."pizza_id" IN (1)

Execution time: 0.000000s [Database: default]
SELECT "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"
 WHERE "app_pizza"."id" IN (1)
```

> **_А можно ли соединить 2 и 3 шаг в один, зачем кешировать 2 таблицы, если мы может сразу join-ить, и кешировать именно этот результат?_**

**Решение, 2 вариант, с prefetch:**

1. Первым запросом получили данные самого инстанса _pizza_
2. Вторым запросом закешировали сджоененную таблицу _Restaurants_ и _Pizza_

```python
pizza = Pizza.objects.prefetch_related(Prefetch('restaurants', queryset=Restaurant.objects.select_related('best_pizza'))).first()
for restaurant in pizza.restaurants.all():
      print(restaurant.best_pizza)
```

```sql
SELECT "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"
 ORDER BY "app_pizza"."id" ASC
 LIMIT 1

Execution time: 0.000000s [Database: default]
SELECT ("app_restaurant_pizzas"."pizza_id") AS "_prefetch_related_val_pizza_id",
       "app_restaurant"."id",
       "app_restaurant"."best_pizza_id",
       T4."id",
       T4."name"
  FROM "app_restaurant"
 INNER JOIN "app_restaurant_pizzas"
    ON ("app_restaurant"."id" = "app_restaurant_pizzas"."restaurant_id")
 INNER JOIN "app_pizza" T4
    ON ("app_restaurant"."best_pizza_id" = T4."id")
 WHERE "app_restaurant_pizzas"."pizza_id" IN (1)
```

### Аргумент _queryset_ у Prefetch

**Задача:** есть ресторан, получить для него закешированные данные для поля _pizzas_ для пицц, у которых _name='topping_name1_
**Решение 1, неправильное**

```python
Restaurant.objects.prefetch_related(Prefetch('pizzas')).first()
```

```sql
SELECT ("app_restaurant_pizzas"."restaurant_id") AS "_prefetch_related_val_restaurant_id",
       "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"
 INNER JOIN "app_restaurant_pizzas"
    ON ("app_pizza"."id" = "app_restaurant_pizzas"."pizza_id")
 WHERE "app_restaurant_pizzas"."restaurant_id" IN (1)
```

**Почему это неправильно**
В данном случае мы нигде не указываем условие для имени `(name='topping_name1')`, т.е. мы кешируем всю таблицу _Pizza_.

**Решение 2, правильное**

```python
Restaurant.objects.prefetch_related(Prefetch('pizzas', queryset=Pizza.objects.filter(name='topping_name1'))).first()
```

```sql
SELECT "app_restaurant"."id",
       "app_restaurant"."best_pizza_id"
  FROM "app_restaurant"
 ORDER BY "app_restaurant"."id" ASC
 LIMIT 1

Execution time: 0.000000s [Database: default]
SELECT ("app_restaurant_pizzas"."restaurant_id") AS "_prefetch_related_val_restaurant_id",
       "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"
 INNER JOIN "app_restaurant_pizzas"
    ON ("app_pizza"."id" = "app_restaurant_pizzas"."pizza_id")
 WHERE ("app_pizza"."name" = 'topping_name1' AND "app_restaurant_pizzas"."restaurant_id" IN (1))
```

Единственная разница между первым запросам это то, что в данном случае у нас добавляется еще одно условие `"app_pizza"."name" = 'topping_name1'` во втором запросе

> **аргумент _queryset_ отвечает за итоговую таблицу, которую мы кешируем**

### Аргумент _to_attr_ у Prefetch

Мы можем положить закешированную таблицу в конкретный атрибут инстанса. Если у нас только один _prefetch_, то это по сути не нужно, но мы можем кешировать сразу несколько таблиц в одном _prefetch_related_

```python
restaurant = Restaurant.objects.prefetch_related(
  Prefetch('pizzas', to_attr='all_pizzas'),
  Prefetch('pizzas', queryset=Pizza.objects.filter(name='topping_name1'), to_attr='filtered_pizzas'),
).first()
```

```sql
SELECT "app_restaurant"."id",
       "app_restaurant"."best_pizza_id"
  FROM "app_restaurant"
 ORDER BY "app_restaurant"."id" ASC
 LIMIT 1

Execution time: 0.000000s [Database: default]
SELECT ("app_restaurant_pizzas"."restaurant_id") AS "_prefetch_related_val_restaurant_id",
       "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"
 INNER JOIN "app_restaurant_pizzas"
    ON ("app_pizza"."id" = "app_restaurant_pizzas"."pizza_id")
 WHERE "app_restaurant_pizzas"."restaurant_id" IN (1)

Execution time: 0.000000s [Database: default]
SELECT ("app_restaurant_pizzas"."restaurant_id") AS "_prefetch_related_val_restaurant_id",
       "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"
 INNER JOIN "app_restaurant_pizzas"
    ON ("app_pizza"."id" = "app_restaurant_pizzas"."pizza_id")
 WHERE ("app_pizza"."name" = 'topping_name1' AND "app_restaurant_pizzas"."restaurant_id" IN (1))

Execution time: 0.000000s [Database: default]
```

Теперь мы можем получить или все пиццы или пиццы, для которых выполняется условие `"app_pizza"."name" = 'topping_name1'`

```python
print(restaurant.all_pizzas)  # [<Pizza: Pizza object (1)>, <Pizza: Pizza object (2)>]
print(restaurant.filtered_pizzas)  # []
```

> **Атрибут _to_attr_ отвечает за сохранение кеширующей таблицы в атрибут инстанса**

**Задача:** Для каждого _restaurants_ получить _pizzas_, у которых среди _toppings_ есть _topping_ c _name=topping_name1_
**Решение**

1. Первым шагом получим все пиццы, для которых выполняется условие
   1.1 Нам нужно закешировать таблицу _Topping_, но не всю, а только ту часть, где `name='topping_name1'` (вспоминаем про атрибут *queryset* у _Prefetch_)
2. Вторым шагом получим данные инстанса ресторана и закешируем таблицу из первого этапа в атрибут _filtered_pizzas_

```python
# получили все пиццы, у которые topping_name='topping_name1'
filtered_pizzas = Pizza.objects.prefetch_related(
  Prefetch('toppings', queryset=Topping.objects.filter(name='topping_name1'))
).all()
# получили все пиццы у ресторана, айдишники которых лежат в filtered_pizzas
restaurant = Restaurant.objects.prefetch_related(
  Prefetch('pizzas', queryset=filtered_pizzas, to_attr='filtered_pizzas')
).first()

print(restaurant.filtered_pizzas)
```

```sql
SELECT "app_restaurant"."id",
       "app_restaurant"."best_pizza_id"
  FROM "app_restaurant"
 ORDER BY "app_restaurant"."id" ASC
 LIMIT 1

Execution time: 0.000000s [Database: default]
SELECT ("app_restaurant_pizzas"."restaurant_id") AS "_prefetch_related_val_restaurant_id",
       "app_pizza"."id",
       "app_pizza"."name"
  FROM "app_pizza"
 INNER JOIN "app_restaurant_pizzas"
    ON ("app_pizza"."id" = "app_restaurant_pizzas"."pizza_id")
 WHERE "app_restaurant_pizzas"."restaurant_id" IN (1)

Execution time: 0.000000s [Database: default]
SELECT ("app_pizza_toppings"."pizza_id") AS "_prefetch_related_val_pizza_id",
       "app_topping"."id",
       "app_topping"."name"
  FROM "app_topping"
 INNER JOIN "app_pizza_toppings"
    ON ("app_topping"."id" = "app_pizza_toppings"."topping_id")
 WHERE ("app_topping"."name" = 'topping_name1' AND "app_pizza_toppings"."pizza_id" IN (1, 2))
```

### Доп задачи

#### 1. Для всех пицц, для всех связанных с ней ресторанов, получить имя лучшей пиццы.

**Решение**

1. Первым запросом мы получим айдишники пицц (мы получаем только _id_, потому что все остальное нам не нужно из условия), закешируем сджоененную таблицу _Restaurants_ и _Pizza_

```python
pizzas = Pizza.objects.only('id').prefetch_related(
  Prefetch('restaurants', queryset=Restaurant.objects.select_related('best_pizza').only('best_pizza__name')),
).all()

for pizza in pizzas:
  for restaurant in pizza.restaurants.all():
    print(restaurant.best_pizza.name)
```

```sql
SELECT "app_pizza"."id"
  FROM "app_pizza"

Execution time: 0.000000s [Database: default]
SELECT ("app_restaurant_pizzas"."pizza_id") AS "_prefetch_related_val_pizza_id",
       "app_restaurant"."id",
       "app_restaurant"."best_pizza_id",
       T4."id",
       T4."name"
  FROM "app_restaurant"
 INNER JOIN "app_restaurant_pizzas"
    ON ("app_restaurant"."id" = "app_restaurant_pizzas"."restaurant_id")
 INNER JOIN "app_pizza" T4
    ON ("app_restaurant"."best_pizza_id" = T4."id")
 WHERE "app_restaurant_pizzas"."pizza_id" IN (1, 2, 3)

Execution time: 0.000000s [Database: default]
```
