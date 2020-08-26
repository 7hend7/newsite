from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse
# test
from wagtail.search.backends import get_search_backend
from django.db import models
from wagtail.core.models import Page
from wagtail.search.models import Query
from newapp.models import AppPage
# -test
import sys
import random

def search(request):
    search_query = request.GET.get('query', None)
    page = request.GET.get('page', 1)
    # raise Exception(search_query)
    # Search
    if search_query:
        """
        s = get_search_backend()
        search_results = s.search(search_query, AppPage.objects.all())  # .filter(body__icontains=search_query)
        search_results = AppPage.objects.filter(body__icontains=search_query)                
        Query.get(search_query).add_hit()
        """
        search_results =AppPage.objects.live().search(search_query)
    else:
        search_results = AppPage.objects.none()

    # Pagination
    paginator = Paginator(search_results, 10)
    try:
        search_results = paginator.page(page)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)

    return TemplateResponse(request, 'newapp/app_index_page.html', {
        'search_query': search_query,
        'appages': search_results,
    })


"""
# search through QuerySet
def search(request):
    # Search
    search_query = request.GET.get('query', None)
    if search_query:
        search_results = AppPage.objects.live().search(search_query)

        # Log the query so Wagtail can suggest promoted results
        Query.get(search_query).add_hit()
    else:
        search_results = Page.objects.none()

    # Render template
    return render(request, 'search_results.html', {
        'search_query': search_query,
        'appages': search_results,
    })
"""