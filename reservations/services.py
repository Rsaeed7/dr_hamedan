"""
خدمات رزرو نوبت
"""
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Reservation, ReservationDay
from doctors.models import Doctor
from patients.models import PatientsFile
from wallet.models import Transaction
import jdatetime


class BookingService:
    """سرویس مدیریت رزرو نوبت"""
    
    @staticmethod
    def get_available_days_for_doctor(doctor, days_ahead=7):
        """
        دریافت روزهای آزاد یک پزشک برای تعداد روزهای آینده
        
        Args:
            doctor: نمونه پزشک
            days_ahead: تعداد روزهای آینده (پیش‌فرض ۷ روز)
        
        Returns:
            لیست روزهایی با اسلات‌های آزاد
        """
        available_days = []
        today = datetime.now().date()
        
        for i in range(days_ahead):
            date = today + timedelta(days=i)
            
            try:
                # بررسی اینکه روز منتشر شده باشد
                reservation_day = ReservationDay.objects.get(date=date, published=True)
                
                # دریافت نوبت‌های آزاد
                available_slots = Reservation.objects.filter(
                    day=reservation_day,
                    doctor=doctor,
                    status='available'
                ).order_by('time').values_list('time', flat=True)
                
                if available_slots:
                    available_days.append({
                        'date': date,
                        'jalali_date': jdatetime.date.fromgregorian(date=date),
                        'slots': list(available_slots),
                        'reservation_day': reservation_day
                    })
                    
            except ReservationDay.DoesNotExist:
                # اگر روز منتشر نشده، رد کن
                continue
                
        return available_days
    
    @staticmethod
    def validate_booking_request(doctor, date, time, patient_data):
        """
        اعتبارسنجی درخواست رزرو
        
        Args:
            doctor: نمونه پزشک
            date: تاریخ رزرو
            time: زمان رزرو  
            patient_data: اطلاعات بیمار
        
        Returns:
            tuple: (is_valid, error_message, reservation_slot)
        """
        # بررسی دسترسی پزشک
        if not doctor.is_available:
            return False, "پزشک در حال حاضر پذیرش بیمار ندارد", None
        
        # بررسی وجود روز رزرو
        try:
            reservation_day = ReservationDay.objects.get(date=date, published=True)
        except ReservationDay.DoesNotExist:
            return False, "این تاریخ برای رزرو فعال نیست", None
        
        # پیدا کردن نوبت آزاد
        try:
            reservation_slot = Reservation.objects.get(
                day=reservation_day,
                doctor=doctor,
                time=time,
                status='available'
            )
        except Reservation.DoesNotExist:
            return False, "این زمان دیگر آزاد نیست", None
        
        # اعتبارسنجی اطلاعات بیمار
        required_fields = ['name', 'phone']
        for field in required_fields:
            if not patient_data.get(field):
                return False, f"فیلد {field} الزامی است", None
        
        return True, None, reservation_slot
    
    @staticmethod
    @transaction.atomic
    def create_reservation(doctor, date, time, patient_data, user=None):
        """
        رزرو نوبت آزاد
        
        Args:
            doctor: نمونه پزشک
            date: تاریخ رزرو
            time: زمان رزرو
            patient_data: اطلاعات بیمار
            user: کاربر (اختیاری)
        
        Returns:
            tuple: (reservation, error_message)
        """
        # اعتبارسنجی
        is_valid, error_message, reservation_slot = BookingService.validate_booking_request(
            doctor, date, time, patient_data
        )
        
        if not is_valid:
            return None, error_message
        
        try:
            # رزرو نوبت آزاد
            success, message = reservation_slot.book_appointment(patient_data, user)
            
            if success:
                # بروزرسانی مبلغ (اگر تغییر کرده باشد)
                reservation_slot.amount = doctor.consultation_fee
                reservation_slot.save()
                
                return reservation_slot, None
            else:
                return None, message
                
        except Exception as e:
            return None, f"خطا در ایجاد رزرو: {str(e)}"
    
    @staticmethod
    def get_available_slot(doctor, date, time):
        """
        دریافت نوبت آزاد مشخص
        
        Args:
            doctor: نمونه پزشک
            date: تاریخ
            time: زمان
        
        Returns:
            Reservation object یا None
        """
        try:
            reservation_day = ReservationDay.objects.get(date=date, published=True)
            return Reservation.objects.get(
                day=reservation_day,
                doctor=doctor,
                time=time,
                status='available'
            )
        except (ReservationDay.DoesNotExist, Reservation.DoesNotExist):
            return None
    
    @staticmethod
    def get_patient_appointments(patient, status_filter=None):
        """
        دریافت نوبت‌های یک بیمار
        
        Args:
            patient: نمونه بیمار
            status_filter: فیلتر وضعیت (اختیاری)
        
        Returns:
            QuerySet رزروها
        """
        appointments = Reservation.objects.filter(patient=patient).exclude(status='available')
        
        if status_filter and status_filter != 'all':
            appointments = appointments.filter(status=status_filter)
        
        return appointments.select_related('doctor', 'day').order_by('-day__date', '-time')
    
    @staticmethod
    def get_doctor_appointments(doctor, date_from=None, date_to=None, status_filter=None):
        """
        دریافت نوبت‌های یک پزشک
        
        Args:
            doctor: نمونه پزشک
            date_from: از تاریخ (اختیاری)
            date_to: تا تاریخ (اختیاری)
            status_filter: فیلتر وضعیت (اختیاری)
        
        Returns:
            QuerySet رزروها
        """
        appointments = Reservation.objects.filter(doctor=doctor).exclude(status='available')
        
        if date_from:
            appointments = appointments.filter(day__date__gte=date_from)
        
        if date_to:
            appointments = appointments.filter(day__date__lte=date_to)
        
        if status_filter and status_filter != 'all':
            appointments = appointments.filter(status=status_filter)
        
        return appointments.select_related('patient', 'day').order_by('-day__date', '-time')
    
    @staticmethod
    def get_upcoming_appointments(doctor, days_ahead=7):
        """
        دریافت نوبت‌های آینده یک پزشک
        
        Args:
            doctor: نمونه پزشک
            days_ahead: تعداد روزهای آینده
        
        Returns:
            QuerySet رزروها
        """
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        return BookingService.get_doctor_appointments(
            doctor=doctor,
            date_from=today,
            date_to=future_date,
            status_filter='confirmed'
        )


class AppointmentService:
    """سرویس مدیریت وضعیت نوبت‌ها"""
    
    @staticmethod
    @transaction.atomic
    def confirm_appointment(reservation, confirmed_by=None):
        """
        تایید نوبت
        
        Args:
            reservation: نمونه رزرو
            confirmed_by: کاربر تایید کننده
        
        Returns:
            tuple: (success, message)
        """
        if reservation.status != 'pending':
            return False, "فقط نوبت‌های در انتظار قابل تایید هستند"
        
        if reservation.payment_status != 'paid':
            return False, "ابتدا پرداخت باید تکمیل شود"
        
        success = reservation.confirm_appointment()
        if success:
            return True, "نوبت با موفقیت تایید شد"
        else:
            return False, "خطا در تایید نوبت"
    
    @staticmethod
    @transaction.atomic
    def cancel_appointment(reservation, cancelled_by=None, refund=True):
        """
        لغو نوبت
        
        Args:
            reservation: نمونه رزرو
            cancelled_by: کاربر لغو کننده
            refund: آیا بازپرداخت انجام شود؟
        
        Returns:
            tuple: (success, message)
        """
        if reservation.status not in ['pending', 'confirmed']:
            return False, "این نوبت قابل لغو نیست"
        
        success = reservation.cancel_appointment(refund=refund)
        if success:
            if refund and reservation.payment_status == 'paid':
                AppointmentService._process_refund(reservation)
            return True, "نوبت با موفقیت لغو شد و به حالت آزاد برگشت"
        else:
            return False, "خطا در لغو نوبت"
    
    @staticmethod
    @transaction.atomic
    def complete_appointment(reservation, completed_by=None):
        """
        تکمیل نوبت
        
        Args:
            reservation: نمونه رزرو
            completed_by: کاربر تکمیل کننده
        
        Returns:
            tuple: (success, message)
        """
        if reservation.status != 'confirmed':
            return False, "فقط نوبت‌های تایید شده قابل تکمیل هستند"
        
        success = reservation.complete_appointment()
        if success:
            return True, "نوبت با موفقیت تکمیل شد"
        else:
            return False, "خطا در تکمیل نوبت"
    
    @staticmethod
    def _process_refund(reservation):
        """پردازش بازپرداخت وجه"""
        if reservation.transaction and reservation.payment_status == 'paid':
            Transaction.objects.create(
                user=reservation.transaction.user,
                amount=reservation.amount,
                transaction_type='refund',
                related_transaction=reservation.transaction,
                status='completed',
                description=f"بازپرداخت نوبت لغو شده - {reservation}"
            ) 