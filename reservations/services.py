"""
خدمات رزرو نوبت
"""
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Reservation, ReservationDay
from doctors.models import Doctor, DoctorBlockedDay
from patients.models import PatientsFile
from wallet.models import Transaction
import jdatetime

from datetime import datetime, timedelta
import jdatetime


class BookingService:
    """سرویس مدیریت رزرو نوبت"""

    @staticmethod
    def get_available_days_for_doctor(doctor_id, days_ahead=90):
        """
        دریافت روزهای آزاد یک پزشک برای تعداد روزهای آینده، شامل روزهایی که نوبت داشتند اما تمام شده‌اند

        Args:
            doctor_id: شناسه پزشک
            days_ahead: تعداد روزهای آینده (پیش‌فرض ۹۰ روز)

        Returns:
            لیست روزهایی با نوبت‌های آزاد یا پر شده
        """
        try:
            doctor = Doctor.objects.get(id=doctor_id, is_available=True)
        except Doctor.DoesNotExist:
            return []

        # Get blocked days for this doctor
        blocked_dates = set(
            DoctorBlockedDay.objects.filter(doctor=doctor)
            .values_list('date', flat=True)
        )

        available_days = []
        today = datetime.now().date()

        for i in range(days_ahead):
            date = today + timedelta(days=i)

            # Skip if this date is blocked by the doctor
            if date in blocked_dates:
                continue

            try:
                # بررسی انتشار روز
                reservation_day = ReservationDay.objects.get(date=date, published=True)

                # دریافت تمام نوبت‌های آن روز برای پزشک
                all_slots = list(Reservation.objects.filter(
                    day=reservation_day,
                    doctor=doctor
                ).order_by('time').values_list('time', 'status'))

                # تفکیک نوبت‌های آزاد
                available_slots = [slot[0].strftime('%H:%M') for slot in all_slots if slot[1] == 'available']

                # اضافه کردن روز حتی اگر نوبت‌ها پر شده باشند
                if all_slots:  # این شرط بررسی می‌کند که آیا آن روز هیچ نوبتی داشته یا خیر
                    jalali_date = jdatetime.date.fromgregorian(date=date)
                    available_days.append({
                        'date_str': date.strftime('%Y-%m-%d'),
                        'jalali_date_str': jalali_date.strftime('%Y/%m/%d'),
                        'slots': available_slots,  # لیست نوبت‌های آزاد، حتی اگر خالی باشد
                        'slots_count': len(available_slots)  # اینجا صفر هم ثبت می‌شود
                    })

            except ReservationDay.DoesNotExist:
                continue

        return available_days

    @staticmethod
    def get_available_days_for_month(doctor_id, jalali_year, jalali_month):
        """
        دریافت روزهای موجود برای یک ماه مشخص از تقویم جلالی
        
        Args:
            doctor_id: شناسه پزشک
            jalali_year: سال جلالی
            jalali_month: ماه جلالی
        
        Returns:
            دیکشنری روزهای موجود با اسلات‌هایشان
        """
        try:
            doctor = Doctor.objects.get(id=doctor_id, is_available=True)
        except Doctor.DoesNotExist:
            return {}
        
        # Get blocked days for this doctor
        blocked_dates = set(
            DoctorBlockedDay.objects.filter(doctor=doctor)
            .values_list('date', flat=True)
        )
        
        # محاسبه روزهای ماه
        if jalali_month <= 6:
            days_in_month = 31
        elif jalali_month <= 11:
            days_in_month = 30
        else:
            # بررسی سال کبیسه برای اسفند
            if jdatetime.date(jalali_year, 12, 1).isleap():
                days_in_month = 30
            else:
                days_in_month = 29
        
        available_days = {}
        
        for day in range(1, days_in_month + 1):
            try:
                jalali_date = jdatetime.date(jalali_year, jalali_month, day)
                gregorian_date = jalali_date.togregorian()
                
                # فقط روزهای آینده را بررسی کن
                if gregorian_date < datetime.now().date():
                    continue
                
                # Skip if this date is blocked by the doctor
                if gregorian_date in blocked_dates:
                    continue
                
                # بررسی وجود روز منتشر شده
                reservation_day = ReservationDay.objects.get(
                    date=gregorian_date, 
                    published=True
                )
                
                # دریافت نوبت‌های آزاد
                available_slots = Reservation.objects.filter(
                    day=reservation_day,
                    doctor=doctor,
                    status='available'
                ).order_by('time').values_list('time', flat=True)
                
                if available_slots:
                    date_key = jalali_date.strftime('%Y/%m/%d')
                    available_days[date_key] = {
                        'date_str': gregorian_date.strftime('%Y-%m-%d'),
                        'jalali_date_str': date_key,
                        'slots': [slot.strftime('%H:%M') for slot in available_slots],
                        'slots_count': len(available_slots)
                    }
                    
            except (ValueError, ReservationDay.DoesNotExist):
                continue
        
        return available_days
    
    @staticmethod
    def get_day_slots(doctor_id, jalali_date_str):
        """
        دریافت اسلات‌های موجود برای یک روز مشخص
        
        Args:
            doctor_id: شناسه پزشک
            jalali_date_str: تاریخ جلالی به فرمت 'Y/m/d'
        
        Returns:
            لیست اسلات‌های موجود
        """
        try:
            doctor = Doctor.objects.get(id=doctor_id, is_available=True)
            
            # تبدیل تاریخ جلالی به میلادی
            year, month, day = map(int, jalali_date_str.split('/'))
            jalali_date = jdatetime.date(year, month, day)
            gregorian_date = jalali_date.togregorian()
            
            # Check if this date is blocked by the doctor
            if DoctorBlockedDay.objects.filter(doctor=doctor, date=gregorian_date).exists():
                return []
            
            # بررسی روز منتشر شده
            reservation_day = ReservationDay.objects.get(
                date=gregorian_date, 
                published=True
            )
            
            # دریافت نوبت‌های آزاد
            slots = Reservation.objects.filter(
                day=reservation_day,
                doctor=doctor,
                status='available'
            ).order_by('time').values_list('time', flat=True)
            
            return [slot.strftime('%H:%M') for slot in slots]
            
        except (Doctor.DoesNotExist, ReservationDay.DoesNotExist, ValueError):
            return []
    
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