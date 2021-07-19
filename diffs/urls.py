# -*- coding: utf-8 -*-
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from diffs import views

urlpatterns = [
    # public api
    url(r'^releases/last/', views.get_last_release),
    url(r'^commits/diffs/', views.commit_diffs),
    url(r'^results/', views.get_bug_owners),
    url(r'^liveness/', views.liveness_probe),
]

urlpatterns = format_suffix_patterns(urlpatterns)
