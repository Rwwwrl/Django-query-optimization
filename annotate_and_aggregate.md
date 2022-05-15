# Aggregate, Annotate

## Aggregate

```python
# models.py
class Author(models.Model):

  name = models.CharField(max_length=100)

  def __repr__(self):
    return f'<Author: {self.name}>'


class Book(models.Model):

  title = models.CharField(max_length=100)
  price = models.IntegerField()
  author = models.ForeignKey(Author, related_name='books', on_delete=models.CASCADE)

  def __repr__(self):
    return f'<Book: {self.title}>'
```

**_aggregate_** - по кварисету мы хотим получить какое-то конечное значение, какой-нибудь величины (количество записей, максимальное значение в кварисете по какому нибудь полю, среднее значению по полю)
**Задача:** вывести количество авторов в бд, среднюю цену книг, а также их сумму цен
_Количество авторов_

```python
# количество 1 первым способом
Author.objects.count()
# результат
2
```

```sql
SELECT COUNT(*) AS "__count"
  FROM "app_author"
```

```python
# количество при помощи aggregate
Author.objects.aggregate(author_count=Count('name'))
# результат
{'author_count': 2}
```

```python
SELECT COUNT("app_author"."name") AS "author_count"
  FROM "app_author"
```

_Средняя цена книг_

```python
Book.objects.aggregate(avg_price=Avg('price'))
# результат
{'avg_price': 150.0}
```

```sql
SELECT AVG("app_book"."price") AS "avg_price"
  FROM "app_book"
```

_Сумма цен книг_

```python
Book.objects.aggregate(total_price=Sum('price'))
# результат
{'total_price': 900}
```

```sql
SELECT SUM("app_book"."price") AS "total_price"
  FROM "app_book"
```

Мы также могли это сделать **одним** запросом

```python
Book.objects.aggregate(
  books_count=Count('id'),
  avg_price=Avg('price'),
  total_price=Sum('price'),
)
# результат
{'books_count': 6, 'avg_price': 150.0, 'total_price': 900}
```

```sql
SELECT COUNT("app_book"."id") AS "books_count",
       AVG("app_book"."price") AS "avg_price",
       SUM("app_book"."price") AS "total_price"
  FROM "app_book"
```

> **_aggregate - нужен для получения конечного результата из Queryset_**

## Annotate

_aggregate_ возвращает единое значение для всей (очевидно мы можем использовать _filter_) таблицы, но что если мы хотим получить единое значение для каждого объекта в _queryset_? На чистом _sql_ это делается при помощи _GROUP BY_, в джанго орм при помощи _annotate_
**Задача:** получить для каждого автора количество книг, которые он написал.

```python
authors = Author.objects.all().annotate(author_books_count=Count('books'))
authors[0].author_books_count
# результат
3
```

```sql
SELECT "app_author"."id",
       "app_author"."name",
       COUNT("app_book"."id") AS "author_books_count"
  FROM "app_author"
  LEFT OUTER JOIN "app_book"
    ON ("app_author"."id" = "app_book"."author_id")
 GROUP BY "app_author"."id"
 LIMIT 21
```

> **_annotate нужен для получения агрегированного значения для каждого объекта queryset`a_**

#### Group by

Реализации _group by_ происходит при помощи _annotate_
**Задача:** Вывести количество книг по каждой ценовой категории.

```python
Book.objects.values('price').annotate(count_by_price=Count('id')).all()
```

```sql
SELECT "app_book"."price",
       COUNT("app_book"."id") AS "count_by_price"
  FROM "app_book"
 GROUP BY "app_book"."price"
```

Результат:

```python
[{'price': 4, 'count_by_price': 1},
 {'price': 1, 'count_by_price': 1},
 {'price': 5, 'count_by_price': 2},
 {'price': 3, 'count_by_price': 1},
 {'price': 0, 'count_by_price': 1},
 {'price': 2, 'count_by_price': 1}]
```

###### Порядок _values_ и _annotate_ имеет значение:

```python
Book.objects.annotate(count_by_price=Count('id')).values('price').all()
```

```sql
SELECT "app_book"."price",
       COUNT("app_book"."id") AS "count_by_price"
  FROM "app_book"
 GROUP BY "app_book"."id"  # групировка тут идут по дефолтному полю
```

Результат:

```python
[{'price': 5, 'count_by_price': 1},
 {'price': 1, 'count_by_price': 1},
 {'price': 3, 'count_by_price': 1},
 {'price': 0, 'count_by_price': 1},
 {'price': 4, 'count_by_price': 1},
 {'price': 2, 'count_by_price': 1},
 {'price': 5, 'count_by_price': 1}]
```

---

На самом деле логику _аннотации_ мы могли бы проделать и на питоне. Зачем тогда это нужно на уровне _sql_?
**Задача:** На главную страницу вывести все книги, но при этом умножив значение _price_ на некоторую величину _discount_

```python
# models.py
class Book(models.Model):

  title = models.CharField(max_length=100)
  price = models.PositiveIntegerField()
```

```python
# some_service.py

@time_it
def get_all_books_by_python():
  '''
  by python  (0.58 sec)
  '''
  queryset = models.Book.objects.all()
  for book in queryset:
    book.price *= 0.5
  return queryset


@time_it
def get_all_books_by_sql():
  '''
  by sql  (0.05 sec)
  '''
  queryset = models.Book.objects.all().annotate(price_with_discount=F('price') * discount)
  str(queryset)  # нужно чтобы инициализовать queryset
  return queryset

```

Замерив время выполения функции на _10 \*\* 5_ записей мы видим, что прописывание логики в _sql_ работает сильно быстрее
