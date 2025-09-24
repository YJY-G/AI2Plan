from rest_framework import serializers
from .models import Leetcode

class LeetcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leetcode
        fields = '__all__'
        read_only_fields = ('user',)