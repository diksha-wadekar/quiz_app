from django.contrib import admin
from .models import Subject, Question, Attempt
admin.site.register(Subject)
admin.site.register(Question)
admin.site.register(Attempt)