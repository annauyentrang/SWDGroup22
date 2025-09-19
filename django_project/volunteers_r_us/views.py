from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'volunteers_r_us/home.html')

def login(request):
    return HttpResponse('<h1>Home</h1>')