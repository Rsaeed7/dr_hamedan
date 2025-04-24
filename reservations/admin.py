from django.contrib import admin
from .models import ReservationDay, Reservation

@admin.register(ReservationDay)
class ReservationDayAdmin(admin.ModelAdmin):
    list_display = ('date', 'published', 'created_at')
    list_filter = ('published', 'date')
    search_fields = ('date',)
    date_hierarchy = 'date'

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('get_patient_name', 'doctor', 'day', 'time', 'status', 'payment_status', 'amount')
    list_filter = ('status', 'payment_status', 'day__date', 'doctor')
    search_fields = ('patient__name', 'doctor__user__first_name', 'doctor__user__last_name', 'phone')
    date_hierarchy = 'day__date'
    
    def get_patient_name(self, obj):
        return obj.patient.name if obj.patient else "Guest"
    get_patient_name.short_description = 'Patient'
    
    actions = ['mark_as_confirmed', 'mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_confirmed(self, request, queryset):
        for reservation in queryset:
            if reservation.status == 'pending' and reservation.payment_status == 'paid':
                reservation.confirm_appointment()
        self.message_user(request, "Selected appointments have been confirmed.")
    mark_as_confirmed.short_description = "Mark selected appointments as confirmed"
    
    def mark_as_completed(self, request, queryset):
        for reservation in queryset:
            if reservation.status == 'confirmed' and reservation.payment_status == 'paid':
                reservation.complete_appointment()
        self.message_user(request, "Selected appointments have been marked as completed.")
    mark_as_completed.short_description = "Mark selected appointments as completed"
    
    def mark_as_cancelled(self, request, queryset):
        for reservation in queryset:
            if reservation.status in ['pending', 'confirmed']:
                reservation.cancel_appointment(refund=False)
        self.message_user(request, "Selected appointments have been cancelled (without refund).")
    mark_as_cancelled.short_description = "Cancel selected appointments (no refund)"
