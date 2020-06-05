from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse
# test
from wagtail.search.backends import get_search_backend
from django.db import models
from wagtail.core.models import Page
from wagtail.search.models import Query
from newapp.models import AppPage


def search(request):
    search_query = request.GET.get('query', None)
    page = request.GET.get('page', 1)
    # raise Exception(search_query)
    # Search
    if search_query:
        # search_results = AppPage.objects.live().search(search_query)
        # Record hit        
        # raise Exception(search_query)
        s = get_search_backend()
        search_results = s.search(search_query, AppPage.objects.all())  # .filter(body__icontains=search_query)
        search_results = AppPage.objects.filter(body__icontains=search_query)
        # raise Exception(search_results)
        Query.get(search_query).add_hit()
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

    return TemplateResponse(request, 'search/search.html', {
        'search_query': search_query,
        'search_results': search_results,
    })
