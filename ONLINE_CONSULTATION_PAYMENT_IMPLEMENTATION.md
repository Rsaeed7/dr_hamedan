# Online Doctor Consultation Payment System Implementation

## Overview
This document describes the implementation of a comprehensive payment system for online doctor consultations in the Dr. Turn project. The system integrates wallet-based payments with the existing chat consultation feature.

## Architecture

### Core Components

1. **Wallet System** (`wallet/` app)
   - User wallet management
   - Transaction processing
   - Balance tracking
   - Payment gateway integration

2. **Chat Medical System** (`chatmed/` app)
   - Online consultation requests
   - Real-time messaging
   - Payment integration
   - Doctor availability management

3. **Context Processors** (`context_processors/`)
   - Global wallet balance access
   - Template context enhancement

## Key Features Implemented

### 1. Wallet Balance Display
- **Location**: `templates/chat/online_doctors.html`
- **Features**:
  - Real-time wallet balance display
  - Quick access to wallet charging
  - Visual balance indicator

### 2. Payment Validation
- **Pre-payment Check**: Before consultation booking
- **Balance Verification**: Automatic balance checking
- **User Feedback**: Clear payment status messages

### 3. Enhanced Consultation Booking Modal
- **Payment Status Display**: Shows current balance vs. required amount
- **Visual Indicators**: 
  - Green checkmark for sufficient balance
  - Warning icon for insufficient balance
- **Smart Redirects**: Automatic redirect to wallet charging with suggested amounts

### 4. Wallet Integration
- **Automatic Wallet Creation**: For all users
- **Balance Management**: Add/subtract operations
- **Transaction Tracking**: Complete audit trail

## Technical Implementation

### 1. Template Enhancements (`templates/chat/online_doctors.html`)

#### Wallet Balance Section
```html
<!-- Wallet Balance Display -->
{% if user.is_authenticated %}
<div class="container">
    <div class="wallet-balance">
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <i class="icon-wallet"></i>
                <span>موجودی کیف پول شما</span>
                <div class="balance-amount">{{ user.wallet.balance|floatformat:0|default:"0" }} تومان</div>
            </div>
            <div>
                <a href="{% url 'wallet:deposit' %}" class="btn btn-light btn-sm">
                    <i class="icon-plus"></i> شارژ کیف پول
                </a>
            </div>
        </div>
    </div>
</div>
{% endif %}
```

#### Payment Status Modal
```html
<!-- Payment Status Display -->
<div id="payment-status" class="payment-info" style="display: none;">
    <div class="d-flex justify-content-between align-items-center">
        <div>
            <strong>موجودی کیف پول:</strong>
            <span id="current-balance">{{ user.wallet.balance|floatformat:0|default:"0" }}</span> تومان
        </div>
        <div>
            <span id="balance-status-icon"></span>
            <span id="balance-status-text"></span>
        </div>
    </div>
    <div id="insufficient-balance-warning" style="display: none;">
        <hr>
        <p class="text-warning mb-2">
            <i class="icon-attention"></i>
            موجودی کیف پول شما برای این مشاوره کافی نیست.
        </p>
        <p class="mb-2">مبلغ مورد نیاز: <span id="needed-amount"></span> تومان</p>
        <a href="#" id="charge-wallet-btn" class="btn btn-warning btn-sm">
            <i class="icon-plus"></i> شارژ کیف پول
        </a>
    </div>
</div>
```

### 2. JavaScript Payment Logic
```javascript
// Get user's current wallet balance
const userBalance = {{ user.wallet.balance|default:"0" }};

function showDynamicForm(doctorId, fee, actionUrl, doctorName) {
    const consultationFee = parseFloat(fee);
    const hasEnoughBalance = userBalance >= consultationFee;
    
    if (hasEnoughBalance) {
        // Sufficient balance - allow booking
        paymentStatus.className = 'payment-info sufficient-balance';
        balanceStatusIcon.innerHTML = '<i class="icon-ok text-success"></i>';
        balanceStatusText.textContent = 'موجودی کافی است';
        submitBtn.disabled = false;
    } else {
        // Insufficient balance - show warning and disable booking
        paymentStatus.className = 'payment-info insufficient-balance';
        balanceStatusIcon.innerHTML = '<i class="icon-attention text-warning"></i>';
        balanceStatusText.textContent = 'موجودی ناکافی';
        
        // Calculate and suggest deposit amount
        const neededAmount = consultationFee - userBalance;
        const suggestedAmount = Math.max(10000, Math.ceil((neededAmount * 1.1) / 10000) * 10000);
        
        // Set charge wallet link with suggested amount
        chargeWalletBtn.href = `/wallet/deposit/?amount=${suggestedAmount}&redirect_to=${currentPath}`;
        submitBtn.disabled = true;
    }
}
```

### 3. Backend Payment Processing (`chatmed/models.py`)

#### Chat Request Payment Method
```python
def process_payment(self, user):
    """پردازش پرداخت برای درخواست چت"""
    from wallet.models import Wallet, Transaction
    from django.db import transaction as db_transaction
    
    # Get or create user's wallet
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Check if user has sufficient balance
    consultation_fee = self.amount
    if not wallet.can_withdraw(consultation_fee):
        available_balance = wallet.balance
        return False, f"موجودی کیف پول کافی نیست. موجودی فعلی: {available_balance:,} تومان - مبلغ مورد نیاز: {consultation_fee:,} تومان. لطفاً کیف پول خود را شارژ کنید."
    
    try:
        with db_transaction.atomic():
            # Deduct amount from wallet
            if not wallet.subtract_balance(consultation_fee):
                return False, "خطا در کسر مبلغ از کیف پول. لطفاً دوباره تلاش کنید."
            
            # Create payment transaction
            payment_transaction = Transaction.objects.create(
                user=user,
                wallet=wallet,
                amount=consultation_fee,
                transaction_type='payment',
                payment_method='wallet',
                status='completed',
                description=f'پرداخت مشاوره آنلاین دکتر {self.doctor.user.get_full_name()}',
                metadata={
                    'doctor_id': self.doctor.id,
                    'doctor_name': str(self.doctor),
                    'chat_request_id': self.id,
                    'consultation_type': 'online_chat'
                }
            )
            
            # Update chat request
            self.payment_status = 'paid'
            self.transaction = payment_transaction
            self.save()
            
            return True, f"پرداخت با موفقیت انجام شد. مبلغ {consultation_fee:,} تومان از کیف پول شما کسر گردید."
            
    except Exception as e:
        return False, f"خطا در پردازش پرداخت: {str(e)}"
```

### 4. Context Processor Updates (`context_processors/context_processors.py`)

```python
def context_processors(request):
    """
    Context processor to make wallet information available in all templates
    """
    # Initialize wallet-related variables
    balance = 0
    wallet = None
    
    if request.user.is_authenticated:
        # Get or create user's wallet
        try:
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            balance = wallet.balance
        except Exception:
            balance = 0
            wallet = None
        
        # Get recent transactions for the user
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    else:
        transactions = []

    return {
        'specializations': specializations,
        'contact': contact,
        'cities': cities,
        'balance': balance,
        'wallet': wallet,
        'recent_transactions': transactions
    }
```

### 5. View Enhancements (`chatmed/views.py`)

#### Pagination Support
```python
class OnDoctorListView(ListView):
    model = Doctor
    template_name = 'chat/online_doctors.html'
    context_object_name = 'doctors'
    paginate_by = 10  # Show 10 doctors per page
```

#### Chat Request Processing
```python
@login_required
@require_POST
def request_chat(request, doctor_id):
    # ... existing code ...
    
    # Process payment
    success, message = new_request.process_payment(user)
    
    if success:
        messages.success(request, f'درخواست چت با موفقیت ثبت شد. {message}')
        return redirect('chat:request_status', request_id=new_request.id)
    else:
        # Delete the request if payment failed
        new_request.delete()
        
        messages.error(request, message)
        
        # If insufficient balance, redirect to wallet deposit
        if "موجودی کیف پول کافی نیست" in message:
            # Calculate required amount for deposit
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            needed_amount = max(0, consultation_fee - wallet.balance)
            
            # Add 10% extra for safety and round to nearest 10,000 tomans
            suggested_amount = ((int(needed_amount * 1.1) + 9999) // 10000) * 10000
            suggested_amount = max(10000, suggested_amount)
            
            # Redirect to deposit page with suggested amount
            deposit_url = f"{reverse('wallet:deposit')}?amount={suggested_amount}&redirect_to={request.path}"
            messages.warning(request, f'برای درخواست مشاوره آنلاین نیاز به شارژ کیف پول دارید. به صفحه شارژ هدایت می‌شوید.')
            return redirect(deposit_url)
        
        return redirect('chat:list_doctors')
```

## User Experience Flow

### 1. Consultation Request Flow
1. **User visits online doctors page**
2. **Wallet balance displayed prominently**
3. **User clicks "مشاوره متنی آنلاین" for a doctor**
4. **Modal opens with:**
   - Consultation fee information
   - Current wallet balance
   - Payment status (sufficient/insufficient)
5. **If sufficient balance:**
   - User can proceed with booking
   - Form submission processes payment
6. **If insufficient balance:**
   - Warning message displayed
   - Suggested deposit amount calculated
   - Direct link to wallet charging
   - Booking button disabled

### 2. Payment Processing
1. **Form submission triggers payment processing**
2. **System checks wallet balance**
3. **If sufficient:**
   - Amount deducted from wallet
   - Transaction record created
   - Chat request marked as paid
   - User redirected to request status
4. **If insufficient:**
   - Error message displayed
   - Redirect to wallet deposit with suggested amount

### 3. Error Handling
- **Insufficient Balance**: Clear messaging with exact amounts
- **Payment Failures**: Transaction rollback and user notification
- **System Errors**: Graceful error handling with user-friendly messages

## Security Features

### 1. Transaction Integrity
- **Atomic Operations**: All payment operations wrapped in database transactions
- **Balance Validation**: Double-checking before deduction
- **Audit Trail**: Complete transaction history

### 2. User Authentication
- **Login Required**: All payment operations require authentication
- **Permission Checks**: Users can only access their own wallet data
- **CSRF Protection**: All forms include CSRF tokens

### 3. Data Validation
- **Amount Validation**: Proper decimal handling
- **Balance Checks**: Multiple validation points
- **Input Sanitization**: All user inputs validated

## Testing Results

The payment system has been thoroughly tested with the following results:

- ✅ **Wallet Creation**: Automatic wallet creation for users
- ✅ **Balance Operations**: Add/subtract balance functionality
- ✅ **Transaction Recording**: Complete audit trail
- ✅ **Payment Validation**: Proper insufficient balance detection
- ✅ **Error Handling**: Graceful error messages and recovery
- ✅ **User Interface**: Responsive design with clear status indicators

## Benefits

### 1. User Experience
- **Transparent Pricing**: Clear display of consultation fees
- **Balance Awareness**: Always visible wallet balance
- **Smart Suggestions**: Automatic calculation of required deposit amounts
- **Seamless Flow**: Integrated payment without leaving the page

### 2. Business Logic
- **Secure Payments**: Robust transaction processing
- **Audit Trail**: Complete payment history
- **Refund Support**: Built-in refund mechanism for rejected consultations
- **Scalable Architecture**: Easily extensible for additional payment methods

### 3. Technical Benefits
- **Atomic Operations**: Data consistency guaranteed
- **Error Recovery**: Robust error handling
- **Performance**: Efficient database queries
- **Maintainability**: Clean, well-documented code

## Future Enhancements

### 1. Payment Methods
- **Gateway Integration**: Multiple payment gateways
- **Credit Card Support**: Direct card payments
- **Mobile Payments**: Integration with mobile payment systems

### 2. Advanced Features
- **Subscription Plans**: Monthly consultation packages
- **Loyalty Programs**: Reward points system
- **Bulk Payments**: Family account management

### 3. Analytics
- **Payment Analytics**: Revenue tracking and reporting
- **User Behavior**: Payment pattern analysis
- **Financial Reporting**: Comprehensive financial dashboards

## Conclusion

The online consultation payment system successfully integrates wallet-based payments with the existing chat consultation feature, providing a seamless, secure, and user-friendly experience. The implementation follows Django best practices and includes comprehensive error handling, security measures, and user experience optimizations. 