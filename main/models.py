from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct = models.CharField(max_length=1, choices=CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.text[:50]
    
class Attempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    total = models.PositiveIntegerField()
    correct = models.PositiveIntegerField()
    taken_at = models.DateTimeField(auto_now_add=True)

    @property
    def wrong(self):
        return self.total - self.correct

    @property
    def percent(self):
        return round(self.correct * 100 / self.total) if self.total else 0