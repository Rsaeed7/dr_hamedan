from rest_framework import serializers
from .models import ChatRoom, Message, ChatRequest
from doctors.models import Doctor
from patients.models import PatientsFile as Patient


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_type = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'sender_name',
            'sender_type',
            'content',
            'created_at',
            'is_read'
        ]
        read_only_fields = ['created_at', 'is_read']

    def get_sender_name(self, obj):
        if obj.sender:
            if hasattr(obj.sender, 'doctor'):
                return f"Dr. {obj.sender.get_full_name()}"
            return obj.sender.get_full_name()
        return "Unknown"

    def get_sender_type(self, obj):
        if obj.sender:
            if hasattr(obj.sender, 'doctor'):
                return 'doctor'
            elif hasattr(obj.sender, 'patient'):
                return 'patient'
        return 'system'


class ChatRequestSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ChatRequest
        fields = [
            'id',
            'patient',
            'patient_name',
            'doctor',
            'doctor_name',
            'status',
            'status_display',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ChatRoomSerializer(serializers.ModelSerializer):
    doctor_info = serializers.SerializerMethodField()
    patient_info = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'request',
            'doctor_info',
            'patient_info',
            'is_active',
            'last_activity',
            'last_message',
            'unread_count',
            'created_at'
        ]
        read_only_fields = ['last_activity', 'created_at']

    def get_doctor_info(self, obj):
        doctor = obj.request.doctor
        return {
            'id': doctor.id,
            'name': f"Dr. {doctor.user.get_full_name()}",
            'specialty': doctor.specialty
        }

    def get_patient_info(self, obj):
        patient = obj.request.patient
        return {
            'id': patient.id,
            'name': patient.user.get_full_name(),
            'medical_history': patient.medical_history
        }

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None

    def get_unread_count(self, obj):
        if hasattr(self.context['request'].user, 'doctor'):
            return obj.messages.filter(is_read=False).exclude(
                sender=self.context['request'].user
            ).count()
        return 0