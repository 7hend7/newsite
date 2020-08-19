from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.template import Context, Template
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
import django.urls as urls
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt

from django.views.generic.base import TemplateView, ContextMixin
from django.views.generic.edit import ProcessFormView, BaseCreateView, FormMixin
from django.conf import settings
from newapp.models import AppPage

"""
# -ajax
def dolikes(request):
    if request.is_ajax():
        id_page = request.GET['id_page']
    data = {
        'res': "success",
        }
    return JsonResponse(data)   
"""