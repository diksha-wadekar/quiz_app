from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Subject, Question


class Styled(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'


class SubjectForm(Styled):
    class Meta:
        model = Subject
        fields = ['name']


class QuestionForm(Styled):
    class Meta:
        model = Question
        fields = ['subject', 'text', 'option_a', 'option_b',
                  'option_c', 'option_d', 'correct']
        widgets = {'text': forms.Textarea(attrs={'rows': 3})}

    def clean(self):
        data = super().clean()
        opts = [data.get(k) for k in ('option_a', 'option_b', 'option_c', 'option_d')]
        if None not in opts and len(set(o.strip().lower() for o in opts)) < 4:
            raise forms.ValidationError('All 4 options must be different')
        return data


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'