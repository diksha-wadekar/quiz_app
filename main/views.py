import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from .forms import RegisterForm
from .forms import SubjectForm, QuestionForm
from .models import Subject, Question, Attempt
from django.db.models import Sum, Count

staff_required = user_passes_test(lambda u: u.is_staff)

def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect('home')
    return render(request, 'registration/register.html', {'form': form})

@login_required
def home(request):
    ctx = {
        'total_q': Question.objects.count(),
        'my_q': Question.objects.filter(created_by=request.user).count(),
        'attempts': Attempt.objects.filter(user=request.user).order_by('-taken_at')[:5],
    }
    return render(request, 'quiz/home.html', ctx)

@staff_required
def subject_list(request):
    form = SubjectForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Subject added')
        return redirect('subject_list')
    return render(request, 'quiz/subjects.html', {'form': form, 'subjects': Subject.objects.all()})

@staff_required
def subject_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(Subject, pk=pk).delete()
        messages.success(request, 'Subject removed')
    return redirect('subject_list')

@login_required
def question_list(request):
    qs = Question.objects.select_related('subject', 'created_by').order_by('-created_at')
    q = request.GET.get('q', '')
    sub = request.GET.get('subject', '')
    if q:
        qs = qs.filter(text__icontains=q)
    if sub:
        qs = qs.filter(subject_id=sub)
    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    return render(request, 'quiz/questions.html', {'page': page, 'q': q, 'sub': sub, 'subjects': Subject.objects.all()})

@login_required
def question_create(request):
    form = QuestionForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        messages.success(request, 'Question added')
        return redirect('question_list')
    return render(request, 'quiz/question_form.html', {'form': form, 'title': 'Add question'})

@login_required
def question_update(request, pk):
    obj = get_object_or_404(Question, pk=pk)
    if obj.created_by != request.user and not request.user.is_staff:
        return redirect('question_list') # only the owner or admin can edit
    form = QuestionForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Question updated')
        return redirect('question_list')
    return render(request, 'quiz/question_form.html', {'form': form, 'title': 'Edit question'})

@login_required
def question_delete(request, pk):
    obj = get_object_or_404(Question, pk=pk)
    if request.method == 'POST' and (obj.created_by == request.user or request.user.is_staff):
        obj.delete()
        messages.success(request, 'Question deleted')
    return redirect('question_list')

@login_required
def quiz_start(request):
    if request.method == 'POST':
        subject = get_object_or_404(Subject, pk=request.POST.get('subject'))
        n = int(request.POST.get('count') or 5)
        ids = list(Question.objects.filter(subject=subject).values_list('id', flat=True))
        if not ids:
            messages.error(request, 'No questions in this subject yet')
            return redirect('quiz_start')
        picked = random.sample(ids, min(n, len(ids))) # random from the shared pool
        request.session['quiz'] = {'subject': subject.id, 'ids': picked}
        return redirect('quiz_take')
    return render(request, 'quiz/start.html', {'subjects': Subject.objects.all()})

@login_required
def quiz_take(request):
    data = request.session.get('quiz')
    if not data:
        return redirect('quiz_start')
    questions = list(Question.objects.filter(id__in=data['ids']))
    if request.method == 'POST':
        correct = 0
        for q in questions:
            if request.POST.get('q%d' % q.id) == q.correct:
                correct += 1
        attempt = Attempt.objects.create(user=request.user, subject_id=data['subject'], total=len(questions), correct=correct)
        del request.session['quiz']
        return redirect('quiz_result', pk=attempt.pk)
    return render(request, 'quiz/take.html', {'questions': questions})

@login_required
def quiz_result(request, pk):
    attempt = get_object_or_404(Attempt, pk=pk, user=request.user)
    return render(request, 'quiz/result.html', {'a': attempt})

@login_required
def leaderboard(request):
    rows = (Attempt.objects.values('user__username')
        .annotate(attempts=Count('id'), right=Sum('correct'), asked=Sum('total'))
        .order_by('-right')[:10])
    return render(request, 'quiz/leaderboard.html', {'rows': rows})