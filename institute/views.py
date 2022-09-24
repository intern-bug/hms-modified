from django.shortcuts import render
from institute.models import Block

# Create your views here.
def index(request):
    return render(request, 'institute/index.html')

def gallery(request):
    return render(request, 'institute/grid-gallery.html')

def hostels(request):
    blocks = Block.objects.all()
    return render (request,'institute/hostels.html',{'blocks': blocks})

def contact(request):
    boys_blocks = Block.objects.filter(gender='Male')
    girls_blocks = Block.objects.filter(gender='Female') 
    return render (request,'institute/contact.html', {'boys_blocks':boys_blocks, 'girls_blocks':girls_blocks})

def developers(request):
    return render(request,'institute/developers.html')