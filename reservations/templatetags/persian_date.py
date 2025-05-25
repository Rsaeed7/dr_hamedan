from django import template

register = template.Library()

months = {
    "01": "فروردین",
    "02": "اردیبهشت",
    "03": "خرداد",
    "04": "تیر",
    "05": "مرداد",
    "06": "شهریور",
    "07": "مهر",
    "08": "آبان",
    "09": "آذر",
    "10": "دی",
    "11": "بهمن",
    "12": "اسفند",
}

days = {
    0: 'جمعه',
    1: 'شنبه',
    2: 'یک شنبه',
    3: 'دوشنبه',
    4: 'سه شنبه',
    5: 'چهارشنبه',
    6: 'پنج شنبه'
}
@register.filter
def persian_month_name(value):
    month_number = value.strftime("%m")
    return months.get(month_number, "")


@register.filter
def persian_weekday(value):
    weekday = value.weekday()
    return days.get((weekday + 1) % 7)



@register.filter
def persian_date_info(value):

    # استخراج عدد ماه، نام روز هفته و عدد روز
    month_number = value.strftime("%m")
    day_number = str(int(value.strftime("%d")))  # عدد روز
    weekday = value.weekday()

    persian_month = months.get(month_number, "")
    persian_weekday = days.get((weekday + 1) % 7)

    return f"{persian_weekday} {day_number} {persian_month}"
