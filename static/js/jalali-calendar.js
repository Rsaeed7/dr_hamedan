/**
 * Jalali Calendar Component
 * A modern, pure JavaScript Jalali calendar implementation
 * No external dependencies required
 */

class JalaliDate {
    constructor(year = null, month = null, day = null) {
        if (year === null) {
            const now = new Date();
            const jalali = this.gregorianToJalali(now.getFullYear(), now.getMonth() + 1, now.getDate());
            this.year = jalali.year;
            this.month = jalali.month;
            this.day = jalali.day;
        } else {
            this.year = year;
            this.month = month;
            this.day = day;
        }
    }

    gregorianToJalali(gy, gm, gd) {
        const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
        
        let jy;
        if (gy <= 1600) {
            jy = 0;
            gy -= 621;
        } else {
            jy = 979;
            gy -= 1600;
        }
        
        const gy2 = (gm > 2) ? (gy + 1) : gy;
        let days = (365 * gy) + (Math.floor((gy2 + 3) / 4)) - (Math.floor((gy2 + 99) / 100)) + 
                   (Math.floor((gy2 + 399) / 400)) - 80 + gd + g_d_m[gm - 1];
        
        jy += 33 * Math.floor(days / 12053);
        days %= 12053;
        
        jy += 4 * Math.floor(days / 1461);
        days %= 1461;
        
        if (days >= 366) {
            jy += Math.floor((days - 1) / 365);
            days = (days - 1) % 365;
        }
        
        let jp = 0;
        let jm;
        
        if (days < 186) {
            jm = 1 + Math.floor(days / 31);
            jp = 1 + (days % 31);
        } else {
            jm = 7 + Math.floor((days - 186) / 30);
            jp = 1 + ((days - 186) % 30);
        }
        
        return {year: jy, month: jm, day: jp};
    }

    jalaliToGregorian(jy, jm, jd) {
        let gy, days;
        if (jy <= 979) {
            gy = 1600;
            jy -= 979;
        } else {
            gy = 621;
            jy -= 979;
        }
        
        if (jm < 7) {
            days = (jm - 1) * 31;
        } else {
            days = (jm - 7) * 30 + 186;
        }
        days += (365 * jy) + (Math.floor(jy / 33) * 8) + (Math.floor(((jy % 33) + 3) / 4)) + jd;
        
        if (jy <= 979) {
            days += 1948321;
        } else {
            days += 1948321;
        }
        
        gy += 400 * Math.floor(days / 146097);
        days %= 146097;
        
        let leap = true;
        if (days >= 36525) {
            days--;
            gy += 100 * Math.floor(days / 36524);
            days %= 36524;
            if (days >= 365) {
                days++;
                leap = false;
            }
        }
        
        gy += 4 * Math.floor(days / 1461);
        days %= 1461;
        
        if (days >= 366) {
            leap = false;
            days--;
            gy += Math.floor(days / 365);
            days = days % 365;
        }
        
        let gd = days + 1;
        
        const sal_a = [0, 31, ((leap ? 29 : 28)), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
        let gm;
        for (gm = 0; gm < 13 && gd > sal_a[gm]; gm++) {
            gd -= sal_a[gm];
        }
        
        return {year: gy, month: gm, day: gd};
    }

    getWeekDay() {
        const gregorian = this.jalaliToGregorian(this.year, this.month, this.day);
        const date = new Date(gregorian.year, gregorian.month - 1, gregorian.day);
        return (date.getDay() + 2) % 7;
    }

    format(pattern = 'Y/m/d') {
        const year = this.year.toString();
        const month = this.month.toString().padStart(2, '0');
        const day = this.day.toString().padStart(2, '0');
        
        return pattern
            .replace('Y', year)
            .replace('m', month)
            .replace('d', day);
    }

    addDays(days) {
        const gregorian = this.jalaliToGregorian(this.year, this.month, this.day);
        const date = new Date(gregorian.year, gregorian.month - 1, gregorian.day);
        date.setDate(date.getDate() + days);
        
        const jalali = this.gregorianToJalali(date.getFullYear(), date.getMonth() + 1, date.getDate());
        return new JalaliDate(jalali.year, jalali.month, jalali.day);
    }

    isAfter(otherDate) {
        if (this.year !== otherDate.year) return this.year > otherDate.year;
        if (this.month !== otherDate.month) return this.month > otherDate.month;
        return this.day > otherDate.day;
    }

    isBefore(otherDate) {
        if (this.year !== otherDate.year) return this.year < otherDate.year;
        if (this.month !== otherDate.month) return this.month < otherDate.month;
        return this.day < otherDate.day;
    }

    isEqual(otherDate) {
        return this.year === otherDate.year && 
               this.month === otherDate.month && 
               this.day === otherDate.day;
    }

    getDaysInMonth() {
        if (this.month <= 6) return 31;
        if (this.month <= 11) return 30;
        
        const gy = this.jalaliToGregorian(this.year, 12, 1).year;
        const isLeap = ((gy % 4 === 0) && (gy % 100 !== 0)) || (gy % 400 === 0);
        return isLeap ? 30 : 29;
    }

    getMonthName() {
        const months = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ];
        return months[this.month - 1];
    }

    getWeekDayName() {
        const weekdays = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه'];
        return weekdays[this.getWeekDay()];
    }
}

class JalaliCalendar {
    constructor(element, options = {}) {
        this.element = typeof element === 'string' ? document.querySelector(element) : element;
        this.options = {
            minDate: null,
            maxDate: null,
            onSelect: null,
            dateFormat: 'Y/m/d',
            showMonthYear: true,
            highlightToday: true,
            disabledDates: [],
            ...options
        };
        
        this.currentDate = new JalaliDate();
        this.selectedDate = null;
        this.viewDate = new JalaliDate();
        
        this.init();
    }

    init() {
        this.element.classList.add('jalali-calendar-container');
        this.render();
        this.attachEvents();
    }

    render() {
        const monthName = this.viewDate.getMonthName();
        const year = this.viewDate.year;
        const daysHTML = this.generateDaysHTML();
        
        this.element.innerHTML = '<div class="jalali-calendar">' +
            '<div class="calendar-header">' +
                '<button type="button" class="nav-btn prev-btn" data-action="prev">' +
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
                        '<polyline points="15,18 9,12 15,6"></polyline>' +
                    '</svg>' +
                '</button>' +
                '<div class="month-year">' +
                    '<span class="month-name">' + monthName + '</span>' +
                    '<span class="year">' + year + '</span>' +
                '</div>' +
                '<button type="button" class="nav-btn next-btn" data-action="next">' +
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
                        '<polyline points="9,18 15,12 9,6"></polyline>' +
                    '</svg>' +
                '</button>' +
            '</div>' +
            '<div class="calendar-weekdays">' +
                '<div class="weekday">ش</div>' +
                '<div class="weekday">ی</div>' +
                '<div class="weekday">د</div>' +
                '<div class="weekday">س</div>' +
                '<div class="weekday">چ</div>' +
                '<div class="weekday">پ</div>' +
                '<div class="weekday">ج</div>' +
            '</div>' +
            '<div class="calendar-days">' + daysHTML + '</div>' +
        '</div>';
        
        this.addStyles();
    }

    generateDaysHTML() {
        const firstDay = new JalaliDate(this.viewDate.year, this.viewDate.month, 1);
        const daysInMonth = firstDay.getDaysInMonth();
        const startWeekDay = firstDay.getWeekDay();
        
        let html = '';
        
        const prevMonth = this.viewDate.month === 1 ? 12 : this.viewDate.month - 1;
        const prevYear = this.viewDate.month === 1 ? this.viewDate.year - 1 : this.viewDate.year;
        const prevMonthDays = new JalaliDate(prevYear, prevMonth, 1).getDaysInMonth();
        
        for (let i = startWeekDay - 1; i >= 0; i--) {
            const day = prevMonthDays - i;
            const dateStr = prevYear + '/' + prevMonth.toString().padStart(2, '0') + '/' + day.toString().padStart(2, '0');
            html += '<div class="calendar-day prev-month" data-date="' + dateStr + '">' + day + '</div>';
        }
        
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new JalaliDate(this.viewDate.year, this.viewDate.month, day);
            const dateString = date.format('Y/m/d');
            const classes = ['calendar-day'];
            
            if (this.options.highlightToday && date.isEqual(this.currentDate)) {
                classes.push('today');
            }
            
            if (this.selectedDate && date.isEqual(this.selectedDate)) {
                classes.push('selected');
            }
            
            if (this.isDateDisabled(date)) {
                classes.push('disabled');
            }
            
            html += '<div class="' + classes.join(' ') + '" data-date="' + dateString + '">' + day + '</div>';
        }
        
        const totalCells = Math.ceil((startWeekDay + daysInMonth) / 7) * 7;
        const nextMonthDays = totalCells - startWeekDay - daysInMonth;
        const nextMonth = this.viewDate.month === 12 ? 1 : this.viewDate.month + 1;
        const nextYear = this.viewDate.month === 12 ? this.viewDate.year + 1 : this.viewDate.year;
        
        for (let day = 1; day <= nextMonthDays; day++) {
            const dateStr = nextYear + '/' + nextMonth.toString().padStart(2, '0') + '/' + day.toString().padStart(2, '0');
            html += '<div class="calendar-day next-month" data-date="' + dateStr + '">' + day + '</div>';
        }
        
        return html;
    }

    isDateDisabled(date) {
        if (this.options.minDate && date.isBefore(this.options.minDate)) {
            return true;
        }
        
        if (this.options.maxDate && date.isAfter(this.options.maxDate)) {
            return true;
        }
        
        if (this.options.disabledDates.length > 0) {
            const dateString = date.format('Y/m/d');
            return this.options.disabledDates.includes(dateString);
        }
        
        return false;
    }

    attachEvents() {
        this.element.addEventListener('click', (e) => {
            if (e.target.dataset.action === 'prev') {
                this.prevMonth();
            } else if (e.target.dataset.action === 'next') {
                this.nextMonth();
            } else if (e.target.classList.contains('calendar-day') && !e.target.classList.contains('disabled')) {
                this.selectDate(e.target.dataset.date);
            }
        });
    }

    prevMonth() {
        if (this.viewDate.month === 1) {
            this.viewDate.month = 12;
            this.viewDate.year--;
        } else {
            this.viewDate.month--;
        }
        this.render();
    }

    nextMonth() {
        if (this.viewDate.month === 12) {
            this.viewDate.month = 1;
            this.viewDate.year++;
        } else {
            this.viewDate.month++;
        }
        this.render();
    }

    selectDate(dateString) {
        const parts = dateString.split('/').map(Number);
        this.selectedDate = new JalaliDate(parts[0], parts[1], parts[2]);
        
        if (this.options.onSelect) {
            this.options.onSelect(this.selectedDate, dateString);
        }
        
        this.render();
    }

    setDate(dateString) {
        if (!dateString) {
            this.selectedDate = null;
            this.render();
            return;
        }
        
        const parts = dateString.split('/').map(Number);
        this.selectedDate = new JalaliDate(parts[0], parts[1], parts[2]);
        this.viewDate = new JalaliDate(parts[0], parts[1], parts[2]);
        this.render();
    }

    getSelectedDate() {
        return this.selectedDate ? this.selectedDate.format(this.options.dateFormat) : null;
    }

    addStyles() {
        if (document.getElementById('jalali-calendar-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'jalali-calendar-styles';
        style.innerHTML = '.jalali-calendar-container{display:inline-block;font-family:IRANSansWeb,Arial,sans-serif;direction:rtl;z-index:99999!important}.jalali-calendar{background:white;border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 20px 40px rgba(0,0,0,0.15);overflow:hidden;width:320px;z-index:99999!important;position:relative}.calendar-header{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;background:linear-gradient(135deg,#263189 0%,#3f4079 100%);color:white}.nav-btn{background:rgba(255,255,255,0.2);border:none;border-radius:8px;color:white;cursor:pointer;padding:8px;transition:all 0.2s ease}.nav-btn:hover{background:rgba(255,255,255,0.3);transform:scale(1.1)}.month-year{font-size:18px;font-weight:bold;text-align:center}.calendar-weekdays{display:grid;grid-template-columns:repeat(7,1fr);background:#f8fafc;border-bottom:1px solid #e5e7eb}.weekday{padding:12px 0;text-align:center;font-size:12px;font-weight:600;color:#6b7280;background:#f8fafc}.calendar-days{display:grid;grid-template-columns:repeat(7,1fr)}.calendar-day{aspect-ratio:1;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.2s ease;font-size:14px;font-weight:500;position:relative}.calendar-day:hover:not(.disabled){background:#eff6ff;color:#263189}.calendar-day.today{background:#dbeafe;color:#263189;font-weight:bold}.calendar-day.selected{background:#263189;color:white;font-weight:bold}.calendar-day.disabled{color:#d1d5db;cursor:not-allowed;opacity:0.5}.calendar-day.prev-month,.calendar-day.next-month{color:#9ca3af;opacity:0.6}.calendar-day.prev-month:hover,.calendar-day.next-month:hover{background:#f3f4f6}.calendar-day:nth-child(7n){color:#dc2626}.calendar-day:nth-child(7n).today{background:#fee2e2;color:#dc2626}.calendar-day:nth-child(7n).selected{background:#dc2626;color:white}.modal .jalali-calendar{z-index:99999!important;box-shadow:0 25px 50px rgba(0,0,0,0.25)}div[style*="position: absolute"] .jalali-calendar{z-index:99999!important}.modal .jalali-calendar-container,.modal .jalali-calendar-container>div{z-index:99999!important}';
        document.head.appendChild(style);
    }
}

function createJalaliDatePicker(input, options = {}) {
    const container = document.createElement('div');
    container.style.position = 'relative';
    container.style.display = 'inline-block';
    container.style.width = '100%';
    
    input.parentNode.insertBefore(container, input);
    container.appendChild(input);
    
    const calendarContainer = document.createElement('div');
    calendarContainer.style.position = 'absolute';
    calendarContainer.style.top = '100%';
    calendarContainer.style.right = '0';
    calendarContainer.style.zIndex = '99999';
    calendarContainer.style.display = 'none';
    container.appendChild(calendarContainer);
    
    const calendar = new JalaliCalendar(calendarContainer, {
        ...options,
        onSelect: (date, dateString) => {
            input.value = dateString;
            calendarContainer.style.display = 'none';
            
            const event = new Event('change', { bubbles: true });
            input.dispatchEvent(event);
            
            if (options.onSelect) {
                options.onSelect(date, dateString);
            }
        }
    });
    
    input.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        document.querySelectorAll('div[style*="position: absolute"] .jalali-calendar').forEach(cal => {
            cal.parentElement.style.display = 'none';
        });
        
        calendarContainer.style.display = 'block';
        calendarContainer.style.zIndex = '99999';
        
        if (input.value) {
            calendar.setDate(input.value);
        }
    });
    
    input.addEventListener('focus', (e) => {
        e.preventDefault();
        
        document.querySelectorAll('div[style*="position: absolute"] .jalali-calendar').forEach(cal => {
            cal.parentElement.style.display = 'none';
        });
        
        calendarContainer.style.display = 'block';
        calendarContainer.style.zIndex = '99999';
        
        if (input.value) {
            calendar.setDate(input.value);
        }
    });
    
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            calendarContainer.style.display = 'none';
        }
    });
    
    input.readOnly = true;
    input.style.cursor = 'pointer';
    
    return {
        calendar: calendar,
        show: () => {
            calendarContainer.style.display = 'block';
            calendarContainer.style.zIndex = '99999';
        },
        hide: () => {
            calendarContainer.style.display = 'none';
        },
        toggle: () => {
            const isVisible = calendarContainer.style.display !== 'none';
            calendarContainer.style.display = isVisible ? 'none' : 'block';
            if (!isVisible) {
                calendarContainer.style.zIndex = '99999';
            }
        }
    };
}

window.JalaliDate = JalaliDate;
window.JalaliCalendar = JalaliCalendar;
window.createJalaliDatePicker = createJalaliDatePicker;
