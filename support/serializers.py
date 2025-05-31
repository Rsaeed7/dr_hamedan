from rest_framework import serializers
from .models import SupportChatRoom, SupportMessage

class SupportMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = SupportMessage
        fields = ['id', 'sender_username', 'content', 'created_at', 'is_admin_message', 'is_read']

class SupportChatRoomSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    admin_username = serializers.CharField(source='admin.username', allow_null=True, read_only=True)
    
    class Meta:
        model = SupportChatRoom
        fields = ['id', 'title', 'customer_username', 'admin_username', 'is_active', 
                 'created_at', 'updated_at']