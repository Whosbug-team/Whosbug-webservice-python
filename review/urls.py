# -*- coding: utf-8 -*-
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from review import views

urlpatterns = [
    # API for commit reviewers and rules
    url(r'^commits/reviewers/', views.commit_reviewers),
    url(r'^commits/rules/', views.commit_rules),
]

urlpatterns = format_suffix_patterns(urlpatterns)
