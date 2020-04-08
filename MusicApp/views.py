from django.http import HttpResponse
from django.shortcuts import render


def homePage(request):
    return render(request, 'music/homePage.html')