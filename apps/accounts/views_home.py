from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    """Homepage view"""
    return render(request, 'home.html')
