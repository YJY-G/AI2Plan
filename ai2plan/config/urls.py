"""
URL configuration for ai2plan project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
from users.views import LoginView, RefreshTokenView, RegisterView
from todo.views import TodoViewSet
from chat.views import HistoryViewSet
from leetcode.views import LeetcodeViewSet
from accounting.views import AccountViewSet, CategoryViewSet, TransactionViewSet
from chat.views import ChatView, AddDocView, ChatStreamView
from django.urls import include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'todos', TodoViewSet, basename='todo')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'histories', HistoryViewSet, basename='history')
router.register(r'leetcode', LeetcodeViewSet, basename='leetcode')

urlpatterns = [
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/chat/', ChatView.as_view(), name='chat'),
    path('api/add-doc/', AddDocView.as_view(), name='add-doc'),
    path('api/', include(router.urls)),
]
