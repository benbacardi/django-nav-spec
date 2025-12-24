
from django.http import HttpResponse

def home(request):
    return HttpResponse("Home")

def page_a(request):
    return HttpResponse("Page A")

def page_b(request):
    return HttpResponse("Page B")
