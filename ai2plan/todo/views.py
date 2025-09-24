from rest_framework import viewsets
from .models import Todo
from .serializers import TodoSerializer
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

class TodoFilter(django_filters.FilterSet):
    class Meta:
        model = Todo
        fields = '__all__'

    

class TodoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TodoFilter
    serializer_class = TodoSerializer

    def get_queryset(self):
        # 仅返回当前用户的待办
        return Todo.objects.filter(user=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        # 创建时强制绑定为当前用户
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # 禁止修改他人的待办
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("无权修改此待办")
        serializer.save()


        