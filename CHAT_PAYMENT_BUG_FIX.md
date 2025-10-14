# Chat Payment Bug Fix - Critical Update

## 🐛 Bug Description

### The Problem  
The chat (online consultation) payment system had the **exact same critical bug** as the reservation system:

1. **ChatRequest Created Before Payment**: When a user requested an online consultation with direct payment, the `ChatRequest` was created immediately in the database (line 59-67 in `chatmed/views.py`)

2. **Failed Payments Still Created Requests**: If payment failed or was cancelled, the `ChatRequest` remained in the database with `payment_status='pending'`

3. **No Retry Mechanism**: Users had no way to retry payment for a failed consultation request

4. **Ghost Requests**: Abandoned payments created permanent pending requests in the database

## ✅ The Solution

We've implemented the same **session-based request intent system** used for reservations, ensuring ChatRequests are only created AFTER successful payment verification.

### Key Changes

#### 1. **Session-Based Request Intent** (`chatmed/views.py`)
- For direct payment, chat request data is stored in the session (`pending_chat_request`)
- No `ChatRequest` is created in the database until payment succeeds
- Wallet payments continue to work as before (immediate creation)

```python
if payment_method == 'direct':
    # CRITICAL FIX: DON'T create ChatRequest yet!
    request.session['pending_chat_request'] = {
        'doctor_id': doctor_id,
        'patient_id': patient.id,
        'disease_summary': disease_summary,
        'amount': consultation_fee,
        'patient_name': full_name,
        'patient_national_id': patient_national_id,
        'phone': phone,
        'payment_method': 'direct'
    }
    # Redirect to payment (no DB record yet)
    return redirect('payments:chat_payment', chat_request_id=0)
```

#### 2. **Modified Chat Payment View** (`payments/views.py`)
- Accepts either session-based requests (ID=0) or database-based requests
- Works with session data for direct payment flow
- Validates session data before showing payment page

```python
if chat_request_id == 0 or chat_request_data:
    # Session-based - get data from session
    doctor = Doctor.objects.get(id=chat_request_data['doctor_id'])
    # Create temporary object for display (not saved to DB)
else:
    # Database-based - get existing ChatRequest
    chat_request = get_object_or_404(ChatRequest, id=chat_request_id)
```

#### 3. **Smart Payment Callback** (`payments/views.py`)
- Creates `ChatRequest` ONLY after successful payment verification
- Uses atomic transactions to ensure data consistency
- Sends notifications only after successful creation

```python
if is_session_based:
    # Session-based - CREATE ChatRequest NOW after payment success
    with db_transaction.atomic():
        chat_request = ChatRequest.objects.create(
            patient=patient,
            doctor=doctor,
            payment_status='paid',  # Already paid!
            payment_request=payment_request
        )
        # Clear session data
        del request.session['pending_chat_request']
```

#### 4. **Retry Payment Mechanism** (`payments/views.py`)
- New view: `retry_chat_payment()`
- Allows users to retry payment if it failed
- Checks session for request data

```python
@login_required
def retry_chat_payment(request):
    chat_data = request.session.get('pending_chat_request', {})
    if not chat_data:
        messages.error(request, 'اطلاعات درخواست یافت نشد')
        return redirect('chat:list_doctors')
    return redirect('payments:chat_payment', chat_request_id=0)
```

#### 5. **Enhanced Payment Response** (`templates/payments/payment_response.html`)
- Shows specific messages for chat payment
- Displays "Retry Payment" button for failed payments
- Clear indication that no request was created if payment failed

## 🔄 New Chat Payment Flow

### Direct Payment Flow (Fixed)
1. ✅ User selects doctor and fills consultation details
2. ✅ User chooses "Direct Payment"
3. ✅ Request data stored in session (NO database record)
4. ✅ User redirected to payment gateway
5. ✅ User completes payment
6. ✅ **Payment callback creates ChatRequest ONLY NOW**
7. ✅ Doctor gets notification
8. ✅ User gets confirmation

### Failed Payment Flow (New)
1. ✅ User attempts payment
2. ✅ Payment fails or is cancelled
3. ✅ **No ChatRequest created in database**
4. ✅ User sees clear error message
5. ✅ User can click "Retry Payment" button
6. ✅ If still wants to proceed → retry payment
7. ✅ Otherwise → return to doctors list

### Wallet Payment Flow (Unchanged)
1. ✅ User selects doctor and fills consultation details
2. ✅ User chooses "Wallet Payment"
3. ✅ Amount deducted from wallet immediately
4. ✅ ChatRequest created and confirmed instantly
5. ✅ User gets confirmation

## 🛡️ Safety Features

1. **Atomic Transactions**: All database operations wrapped in transactions
2. **Session Validation**: Checks session data before processing
3. **Error Handling**: Graceful handling of missing data or failures
4. **Automatic Cleanup**: Session data cleared after successful payment

## 📋 Files Modified

1. ✅ `chatmed/views.py` - Session-based request intent for direct payment
2. ✅ `payments/views.py` - Updated chat_payment view + payment callback + retry view
3. ✅ `payments/urls.py` - Added retry chat payment URL
4. ✅ `templates/payments/payment_response.html` - Enhanced UI with retry option for chat

## 🧪 Testing Recommendations

### Test Scenarios

1. **Normal Flow**
   - [ ] Direct payment → successful payment → ChatRequest created
   - [ ] Wallet payment → immediate confirmation → ChatRequest created

2. **Failed Payment**
   - [ ] Direct payment → failed payment → no ChatRequest in database
   - [ ] Direct payment → cancelled payment → no ChatRequest in database
   - [ ] Retry button works for failed payments

3. **Edge Cases**
   - [ ] User closes browser during payment → no ChatRequest created
   - [ ] Payment gateway timeout → no ChatRequest created
   - [ ] Session expiry during payment → handled gracefully

4. **Wallet Payment (Should Still Work)**
   - [ ] Sufficient balance → immediate confirmation
   - [ ] Insufficient balance → proper error handling

## 🚀 Deployment Steps

1. **Deploy Code**
   ```bash
   cd /home/siavash-rahimi/Desktop/dr_hamedan
   git pull
   source env/bin/activate
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

2. **Restart Services**
   ```bash
   sudo systemctl restart dr_turn
   sudo systemctl restart nginx
   ```

3. **Monitor Logs**
   ```bash
   tail -f logs/django.log
   ```

## 📊 Benefits

✅ **No More Ghost Chat Requests**: Requests only created after confirmed payment
✅ **Better User Experience**: Retry payment without starting over
✅ **Clearer Communication**: Users know exactly what happened
✅ **Resource Efficiency**: No wasted database records from failed/abandoned payments
✅ **Consistent Behavior**: Same fix pattern as reservation system

## ⚠️ Important Notes

1. **Session Storage**: Request intent is stored in sessions - ensure session backend is reliable
2. **Session Timeout**: Default Django session timeout is 2 weeks
3. **Backwards Compatibility**: Wallet payments work exactly as before
4. **Testing**: Thoroughly test in staging before production deployment

## 🔍 Monitoring

Monitor these metrics after deployment:

- Number of failed chat payments vs successful payments
- Frequency of retry attempts
- Session cleanup command results
- User feedback on chat request flow

## 📝 Comparison with Reservation Fix

Both systems now use the **exact same pattern**:

| Feature | Reservations | Chat Requests |
|---------|-------------|---------------|
| Session key | `pending_direct_booking` | `pending_chat_request` |
| Payment view | `reservation_payment` | `chat_payment` |
| Retry view | `retry_reservation_payment` | `retry_chat_payment` |
| Callback handling | Creates Reservation after payment | Creates ChatRequest after payment |
| Race condition handling | Auto-refund if slot taken | N/A (no race condition) |

---

**Status**: ✅ Implemented and Ready for Testing
**Priority**: 🔴 Critical Bug Fix  
**Impact**: High - Affects all direct payment chat consultations
**Related**: See `PAYMENT_RESERVATION_BUG_FIX.md` for reservation system fix

