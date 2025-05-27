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
                
                # دریافت اسلات‌های آزاد
                available_slots = doctor.get_available_slots(date)
                
                if available_slots:
                    available_days.append({
                        'date': date,
                        'jalali_date': jdatetime.date.fromgregorian(date=date),
                        'slots': available_slots,
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
            tuple: (is_valid, error_message)
        """
        # بررسی دسترسی پزشک
        if not doctor.is_available:
            return False, "پزشک در حال حاضر پذیرش بیمار ندارد"
        
        # بررسی وجود روز رزرو
        try:
            reservation_day = ReservationDay.objects.get(date=date, published=True)
        except ReservationDay.DoesNotExist:
            return False, "این تاریخ برای رزرو فعال نیست"
        
        # بررسی آزاد بودن زمان
        available_slots = doctor.get_available_slots(date)
        if time not in available_slots:
            return False, "این زمان دیگر آزاد نیست"
        
        # اعتبارسنجی اطلاعات بیمار
        required_fields = ['name', 'phone']
        for field in required_fields:
            if not patient_data.get(field):
                return False, f"فیلد {field} الزامی است"
        
        return True, None
    
    @staticmethod
    @transaction.atomic
    def create_reservation(doctor, date, time, patient_data, user=None):
        """
        ایجاد رزرو جدید
        
        Args:
            doctor: نمونه پزشک
            date: تاریخ رزرو
            time: زمان رزرو
            patient_data: اطلاعات بیمار
            user: کاربر (اختیاری)
        
        Returns:
            tuple: (reservation, created) یا (None, error_message)
        """
        # اعتبارسنجی
        is_valid, error_message = BookingService.validate_booking_request(
            doctor, date, time, patient_data
        )
        
        if not is_valid:
            return None, error_message
        
        try:
            # دریافت یا ایجاد روز رزرو
            reservation_day = ReservationDay.objects.get(date=date)
            
            # ایجاد یا پیدا کردن فایل بیمار
            patient = None
            if user and user.is_authenticated:
                patient, created = PatientsFile.objects.get_or_create(
                    user=user,
                    defaults={
                        'name': f"{user.first_name} {user.last_name}".strip(),
                        'phone': patient_data.get('phone', ''),
                        'email': user.email,
                        'national_id': patient_data.get('national_id', '')
                    }
                )
                # بروزرسانی اطلاعات در صورت نیاز
                if not patient.phone:
                    patient.phone = patient_data.get('phone', '')
                    patient.save()
            else:
                # مهمان - ایجاد فایل بیمار جدید
                patient = PatientsFile.objects.create(
                    name=patient_data['name'],
                    phone=patient_data['phone'],
                    national_id=patient_data.get('national_id', ''),
                    email=patient_data.get('email', '')
                )
            
            # ایجاد رزرو
            reservation = Reservation.objects.create(
                day=reservation_day,
                patient=patient,
                doctor=doctor,
                time=time,
                phone=patient_data['phone'],
                amount=doctor.consultation_fee,
                status='pending',
                payment_status='pending',
                notes=patient_data.get('notes', '')
            )
            
            return reservation, None
            
        except Exception as e:
            return None, f"خطا در ایجاد رزرو: {str(e)}"
    
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
        appointments = Reservation.objects.filter(patient=patient)
        
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
        appointments = Reservation.objects.filter(doctor=doctor)
        
        if date_from:
            appointments = appointments.filter(day__date__gte=date_from)
        
        if date_to:
            appointments = appointments.filter(day__date__lte=date_to)
        
        if status_filter and status_filter != 'all':
            appointments = appointments.filter(status=status_filter)
        
        return appointments.select_related('patient', 'day').order_by('day__date', 'time')


class AppointmentService:
    """سرویس مدیریت نوبت‌ها"""
    
    @staticmethod
    @transaction.atomic
    def confirm_appointment(reservation, confirmed_by=None):
        """تایید نوبت"""
        if reservation.status != 'pending':
            return False, "فقط نوبت‌های در انتظار قابل تایید هستند"
        
        if reservation.payment_status != 'paid':
            return False, "ابتدا پرداخت باید انجام شود"
        
        reservation.status = 'confirmed'
        reservation.save()
        
        # TODO: ارسال اعلان به بیمار
        
        return True, "نوبت با موفقیت تایید شد"
    
    @staticmethod
    @transaction.atomic
    def cancel_appointment(reservation, cancelled_by=None, refund=True):
        """لغو نوبت"""
        if reservation.status == 'completed':
            return False, "نوبت تکمیل شده قابل لغو نیست"
        
        old_status = reservation.status
        reservation.status = 'cancelled'
        
        # مدیریت بازپرداخت
        if refund and reservation.payment_status == 'paid':
            try:
                refund_result = AppointmentService._process_refund(reservation)
                if refund_result:
                    reservation.payment_status = 'refunded'
            except Exception as e:
                # در صورت خطا در بازپرداخت، نوبت را لغو نکن
                return False, f"خطا در بازپرداخت: {str(e)}"
        
        reservation.save()
        
        # TODO: ارسال اعلان به بیمار و پزشک
        
        return True, "نوبت با موفقیت لغو شد"
    
    @staticmethod
    @transaction.atomic
    def complete_appointment(reservation, completed_by=None):
        """تکمیل نوبت"""
        if reservation.status != 'confirmed':
            return False, "فقط نوبت‌های تایید شده قابل تکمیل هستند"
        
        reservation.status = 'completed'
        reservation.save()
        
        # TODO: ارسال اعلان تکمیل
        
        return True, "نوبت به عنوان تکمیل شده علامت‌گذاری شد"
    
    @staticmethod
    def _process_refund(reservation):
        """پردازش بازپرداخت"""
        if not reservation.transaction:
            return False
        
        # ایجاد تراکنش بازپرداخت
        refund_transaction = Transaction.objects.create(
            user=reservation.transaction.user,
            amount=reservation.amount,
            transaction_type='refund',
            related_transaction=reservation.transaction,
            status='completed',
            description=f"بازپرداخت نوبت لغو شده - {reservation}"
        )
        
        return True 