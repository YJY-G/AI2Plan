from rest_framework import serializers
from .models import History 
import uuid

class ChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length = 255,write_only=True)
    session_id = serializers.CharField(max_length = 255,write_only=True)
    response = serializers.CharField(max_length = 255,read_only=True)


    def validate_session_id(self, value):
        if not History.objects.filter(session_id=value).exists():
            raise serializers.ValidationError("Session ID does not exist")
        return value

    def create(self, validated_data):
        return validated_data

class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = '__all__'
        read_only_fields = ('user',)
        extra_kwargs = {
            'session_id': {'read_only': True}
        }

    def create(self, validated_data):
        user = self.context['request'].user
        instance = History.objects.create(
            user=user,
            session_id=str(uuid.uuid4())
        )
        return instance