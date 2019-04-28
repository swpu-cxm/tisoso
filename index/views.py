from django import urls
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from multiprocessing import Process, Pool
from index.tisousou import tisousou


# Create your views here.

def index(request):
    question = request.GET.get('question')
    if question:
        return HttpResponseRedirect('/search/?question=' + question)
    return render(request, 'index.html')


def search(request):
    if request.method == "GET":
        question = request.GET.get('question')
    if request.method == "POST":
        question = request.POST.get('question')
    try:
        message_list_1, message_list_2 = tisousou(question)
    except Exception as e:
        message_list_1 = [{'question': '<h1>请求超时</h1>', 'answer': ''}]
        message_list_2 = [{'question': '<h1>请求超时</h1>', 'option': '', 'answer': ''}]
    return render(request, 'search.html', {'messages_1': message_list_1, 'messages_2': message_list_2})


def page_not_found(request):
    return render(request, '404.html')
