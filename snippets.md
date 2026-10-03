# Django Hackathon Snippets (offline cheat sheet)

Works with the starter: app `main`, model `Item`, project `core`.
After ANY model change: `python manage.py makemigrations` then `python manage.py migrate`.

---

## 1. Filter by status (add to `item_list` view)

```python
status = request.GET.get('status', '')
if status:
    items = items.filter(status=status)
# pass 'status': status to the template context
```

Template (above the table):
```html
<a href="?status=todo">To do</a> |
<a href="?status=doing">In progress</a> |
<a href="?status=done">Done</a> |
<a href="?">All</a>
```

## 2. Detail page

views.py
```python
@login_required
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk, owner=request.user)
    return render(request, 'main/item_detail.html', {'item': item})
```
urls.py
```python
path('<int:pk>/', views.item_detail, name='item_detail'),
```
item_detail.html
```html
{% extends 'base.html' %}
{% block content %}
<h3>{{ item.title }}</h3>
<p>{{ item.description }}</p>
<p>Status: {{ item.get_status_display }}</p>
<a href="{% url 'item_list' %}">Back</a>
{% endblock %}
```

## 3. Category (ForeignKey) and tags (ManyToMany)

```python
class Category(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name

class Item(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    # many to many example:
    # tags = models.ManyToManyField(Tag, blank=True)
```
Register in admin.py: `admin.site.register(Category)`
Add `'category'` to the form `fields` list.

## 4. Due date / number / boolean fields

```python
due_date = models.DateField(null=True, blank=True)
price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
quantity = models.PositiveIntegerField(default=0)
is_active = models.BooleanField(default=True)
```
Date input widget in the form:
```python
widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}
```

## 5. File / image upload

models.py
```python
image = models.ImageField(upload_to='images/', blank=True, null=True)
file = models.FileField(upload_to='files/', blank=True, null=True)
```
settings.py
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```
core/urls.py
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
views: `ItemForm(request.POST or None, request.FILES or None)`
template: `<form method="post" enctype="multipart/form-data">`
show it: `{% if item.image %}<img src="{{ item.image.url }}" width="100">{% endif %}`

## 6. Export to CSV

```python
import csv
from django.http import HttpResponse

@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="items.csv"'
    writer = csv.writer(response)
    writer.writerow(['Title', 'Status', 'Created'])
    for i in Item.objects.filter(owner=request.user):
        writer.writerow([i.title, i.get_status_display(), i.created_at.date()])
    return response
```
urls: `path('export/', views.export_csv, name='export_csv'),`

## 7. Import from CSV (upload a file)

```python
@login_required
def import_csv(request):
    if request.method == 'POST' and request.FILES.get('file'):
        text = request.FILES['file'].read().decode('utf-8').splitlines()
        for row in csv.DictReader(text):
            Item.objects.create(owner=request.user, title=row['title'],
                                description=row.get('description', ''))
        messages.success(request, 'Imported')
        return redirect('item_list')
    return render(request, 'main/import.html')
```
import.html form needs `enctype="multipart/form-data"` and `<input type="file" name="file">`.

## 8. Roles: admin only pages

```python
from django.contrib.auth.decorators import login_required, user_passes_test

@user_passes_test(lambda u: u.is_staff)
def admin_only_view(request):
    ...
```
In templates: `{% if user.is_staff %} ... {% endif %}`
Make a user staff: Django admin -> Users -> tick "Staff status".
Admin sees everything:
```python
items = Item.objects.all() if request.user.is_staff else Item.objects.filter(owner=request.user)
```

## 9. Groups / simple role field

```python
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('admin','Admin'),('user','User')], default='user')
```
Check: `request.user.profile.role == 'admin'`

## 10. Change password (built in)

core/urls.py (the `accounts/` include already has these URLs)
Create `templates/registration/password_change_form.html`:
```html
{% extends 'base.html' %}
{% block content %}
<h3>Change password</h3>
<form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Save</button></form>
{% endblock %}
```
And `password_change_done.html` with a short message. Link: `{% url 'password_change' %}`

## 11. Aggregates for dashboard cards

```python
from django.db.models import Count, Sum, Avg
Item.objects.count()
Item.objects.filter(status='done').count()
Item.objects.aggregate(total=Sum('price'))
Item.objects.values('status').annotate(n=Count('id'))
```
Per day chart:
```python
from django.db.models.functions import TruncDate
Item.objects.annotate(day=TruncDate('created_at')).values('day').annotate(n=Count('id')).order_by('day')
```
Bar chart type in Chart.js: change `type: 'doughnut'` to `'bar'` or `'line'`.

## 12. REST API (DRF)

serializers.py
```python
from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'title', 'description', 'status', 'created_at']
```
api_views (put in views.py)
```python
from rest_framework import viewsets, permissions
from .serializers import ItemSerializer

class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Item.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
```
urls.py
```python
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('api/items', views.ItemViewSet, basename='api-items')
urlpatterns += router.urls
```
Open `/api/items/` in the browser (logged in) to test.

## 13. Fetch data with JavaScript (no reload)

```html
<script>
fetch('/api/items/')
  .then(r => r.json())
  .then(data => console.log(data));
</script>
```
POST needs the CSRF token header: `'X-CSRFToken': '{{ csrf_token }}'`.

## 14. Custom validation

forms.py
```python
def clean_title(self):
    t = self.cleaned_data['title']
    if len(t) < 3:
        raise forms.ValidationError('Title must be at least 3 characters')
    return t
```

## 15. Messages / alerts (already in base.html)

`messages.success(request, 'Saved')`, `messages.error(request, 'Something went wrong')`
For errors use class `alert-danger` in base.html.

## 16. Python basics (console / logic questions)

```python
# file read / write
with open('data.txt', 'w') as f: f.write('hello')
with open('data.txt') as f: text = f.read()

# json
import json
data = json.load(open('data.json')); json.dump(data, open('out.json','w'), indent=2)

# dates
from datetime import datetime, timedelta
now = datetime.now(); tomorrow = now + timedelta(days=1)

# sorting
people.sort(key=lambda p: p['age'], reverse=True)
```

## 17. Git (offline GitLab server)

```bash
git clone <url>          # get the team repo
git add .
git commit -m "message"
git pull                 # BEFORE pushing
git push
git status
git log --oneline
```
Merge conflict: open the file, keep the right part, delete the `<<<<<<<` `=======` `>>>>>>>` lines, then `git add .` and `git commit`.
Add `venv/` and `db.sqlite3` to a `.gitignore` file so teammates don't clash.
Teammates set up with: `python -m venv venv`, activate, `pip install -r requirements.txt` (or offline: `pip install --no-index --find-links=wheels -r requirements.txt`).

## 18. Common errors

| Error | Fix |
|---|---|
| `TemplateDoesNotExist` | check the template path / DIRS in settings |
| `NoReverseMatch` | url `name` doesn't match `{% url 'name' %}` |
| `no such table` | run makemigrations then migrate |
| Static files not loading | check STATICFILES_DIRS, `{% load static %}`, Ctrl+F5 |
| `CSRF verification failed` | add `{% csrf_token %}` inside the form |
| `ModuleNotFoundError: django` | venv not activated, no `(venv)` shown |
| `Port already in use` | use `runserver 8001` or another port |
| Changes not showing | save the file, check the server is still running |
| `IntegrityError NOT NULL` | field needs `null=True, blank=True` or a default |
| Reset the database | delete `db.sqlite3` and migration files (not `__init__.py`), then makemigrations + migrate |
