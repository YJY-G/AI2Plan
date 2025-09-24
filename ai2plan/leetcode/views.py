from rest_framework.viewsets import ModelViewSet
from .models import Leetcode
from .serializers import LeetcodeSerializer
from rest_framework import permissions


# Create your views here.
class LeetcodeViewSet(ModelViewSet):
    queryset = Leetcode.objects.all()
    serializer_class = LeetcodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Leetcode.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)