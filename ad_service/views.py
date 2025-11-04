from django.shortcuts import render

учше
def home(request):
    """Простое представление для главной страницы"""
    return render(request, 'home.html')