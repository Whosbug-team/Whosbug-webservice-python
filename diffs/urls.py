# -*- coding: utf-8 -*-
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from diffs import views
from rest_framework import routers  # 路由配置模块

# router = routers.DefaultRouter()
# router.register(r'users', views.UserViewSet, base_name='user')
# router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    
    # public api
    url(r"^releases/last/", views.get_last_release),
    url(r"^commits/diffs/", views.commit_diffs),
    url(r'^liveness/', views.liveness_probe),
    url(r"^create-project-release/", views.create_project_and_release),  # 创建project_release信息
    url(r"^commits/commits-info/", views.upload_commits_info),  # 上传commits_info
    url(r"^commits/upload-done/", views.upload_done),  # 上传结束标志
    url(r"^commits/train_method/", views.train_method),  # 上传结束标志2
    url(r"^delete_all_related", views.delete_all_related_data),  # debug:删除所有内容
    url(r"^commits/delete_uncalculate/", views.delete_uncalculate),
    url(r"^liveness/", views.liveness_probe),
    url(r"^owner/", views.get_confidence_and_infos),
    # url(r"^base64test/", views.get_decrypted_text),
]

urlpatterns = format_suffix_patterns(urlpatterns)
