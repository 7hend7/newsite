
from django.urls import re_path, path
from . import *
from . import views

# patterns
urlpatterns = [
# adding likes at the apppage through  AJAX
re_path(r'addlike/$', views.dolikes, name="addlike"),
]