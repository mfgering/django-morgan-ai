"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import routers
from morgan import views as morgan_views

router = routers.DefaultRouter()

urlpatterns = [
    path('', morgan_views.chat, name='chat'),
    path("admin/", admin.site.urls),
    path('api/', include(router.urls)),
    path('test/', morgan_views.test_view, name='test_view'),
    path('chat/', morgan_views.chat, name='chat'),
    re_path(r'^chat-show/$', morgan_views.chat_show, name='chat_show'),
    re_path(r'^chat-show/(?P<chat_id>[0-9]+)/$', morgan_views.chat_show, name='chat_show'),
    path('chat-check-status/', morgan_views.chat_check_status, name='chat_check_status'),
    path('chat-flag-submit/', morgan_views.chat_flag_submit, name='chat_flag_submit'),
    path('chat-show-action/', morgan_views.chat_show_action, name='chat_show_action'),
    path('chat-favs/', morgan_views.chat_favs, name='chat_favs'),
    path('chat-faqs/', morgan_views.chat_faqs, name='chat_faqs'),
    path('about/', morgan_views.about_morgan, name='about_morgan'),
    path("__debug__/", include("debug_toolbar.urls")),
]
