
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from doctors.models import City
from .models import ServiceCategory, Service, HomeCareRequest
from .forms import HomeCareRequestForm
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import HomeCareRequest



def select_service_view(request):
    categories = ServiceCategory.objects.all()
    cities = City.objects.all()

    selected_city_name = request.GET.get('city')
    selected_category_name = request.GET.get('category')

    selected_city = City.objects.filter(name=selected_city_name).first() if selected_city_name else None
    selected_category = ServiceCategory.objects.filter(name=selected_category_name).first() if selected_category_name else None

    services = Service.objects.all()

    if selected_city:
        services = services.filter(available_in_cities=selected_city)

    if selected_category:
        services = services.filter(category=selected_category)

    context = {
        'categories': categories,
        'cities': cities,
        'services': services,
        'selected_city': selected_city,
        'selected_category': selected_category,
    }
    return render(request, 'homecare/select_service.html', context)


@login_required
def request_service(request, service_slug):
    service = get_object_or_404(Service, slug=service_slug)

    if request.method == 'POST':
        form = HomeCareRequestForm(request.POST, request.FILES, user=request.user, service=service)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.patient = request.user.patient
            instance.service = service

            # مطمئن شو که فیلدهای تاریخ و زمان مقدار داشته باشند (حتی اگر null باشن)
            # اینجا لازم نیست مقدار پیش‌فرض بدی چون مدل nullable هست
            instance.save()

            messages.success(request, "درخواست شما با موفقیت ثبت شد.")
            return redirect('homecare:success')
        else:
            # خطاهای فرم رو چاپ کن برای دیباگ
            print("Form errors:", form.errors)
    else:
        form = HomeCareRequestForm(user=request.user, service=service)

    return render(request, 'homecare/request_service.html', {
        'service': service,
        'form': form,
        'requires_prescription': service.requires_prescription
    })

def request_success(request):
    return render(request, 'homecare/success.html')



@login_required
def cancel_homecare_request(request, request_id):
    homecare_request = get_object_or_404(HomeCareRequest, id=request_id, patient__user=request.user)

    if homecare_request.status in ['pending', 'contacted']:
        homecare_request.status = 'cancelled_by_patient'
        homecare_request.save()
        messages.success(request, "درخواست با موفقیت لغو شد.")
    else:
        messages.warning(request, "این درخواست قابل لغو نیست.")

    return redirect('patients:homecare_request_list')





def is_staff_user(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_staff_user)
def admin_homecare_requests(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')

    requests = HomeCareRequest.objects.select_related('patient__user', 'service', 'city').all().order_by('-created_at')

    # فیلتر وضعیت
    if status_filter:
        requests = requests.filter(status=status_filter)

    # جستجو روی نام بیمار و نام خدمت
    if search_query:
        requests = requests.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(service__name__icontains=search_query)
        )

    paginator = Paginator(requests, 10)  # هر صفحه 10 درخواست
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': HomeCareRequest.STATUS_CHOICES,
    }
    return render(request, 'homecare/admin_requests_list.html', context)


@user_passes_test(is_staff_user)
def admin_request_detail(request, request_id):
    req = get_object_or_404(HomeCareRequest, id=request_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes')

        if new_status in dict(HomeCareRequest.STATUS_CHOICES).keys():
            req.status = new_status

        req.extra_notes = notes
        req.save()

        messages.success(request, 'وضعیت و توضیحات درخواست با موفقیت بروزرسانی شد.')
        return redirect('homecare:admin_request_detail', request_id=request_id)

    context = {'req': req}
    return render(request, 'homecare/admin_request_detail.html', context)