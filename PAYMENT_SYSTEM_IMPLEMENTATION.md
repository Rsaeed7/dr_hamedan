# Payment System Implementation - Dr. Turn Project

## Overview

This document describes the implementation of a separate payment app that integrates with the existing wallet system and provides ZarinPal API integration for the Dr. Turn healthcare appointment booking system.

## Architecture

### 1. New Payment App Structure

```
payments/
├── __init__.py
├── apps.py
├── models.py
├── views.py
├── urls.py
├── admin.py
├── services.py
├── signals.py
└── management/
    └── commands/
        └── setup_zarinpal_gateway.py
```

### 2. Key Models

#### PaymentGateway
- **Purpose**: Manages payment gateway configurations
- **Features**:
  - Support for multiple gateway types (ZarinPal, Mellat, etc.)
  - Sandbox/Production environment switching
  - Commission calculation
  - Amount limits
  - API URL management

#### PaymentRequest
- **Purpose**: Tracks individual payment requests
- **Features**:
  - Status tracking (pending, processing, completed, failed, etc.)
  - Integration with wallet transactions
  - Authority and reference ID management
  - Expiration handling
  - Metadata storage

#### PaymentLog
- **Purpose**: Comprehensive logging of payment activities
- **Features**:
  - Request, callback, verify, and error logging
  - JSON data storage for debugging
  - Audit trail

### 3. Payment Service Layer

#### ZarinPalPaymentService
- **Features**:
  - Real ZarinPal API integration
  - Request creation and verification
  - Error handling and logging
  - Sandbox/Production environment support

#### PaymentService
- **Features**:
  - Gateway-agnostic payment processing
  - Amount validation
  - Unified API for different payment types

## Integration with Existing System

### 1. Wallet Integration
- Payment requests automatically create wallet transactions
- Balance updates on successful payments
- Transaction linking for audit trails

### 2. Reservation Integration
- Direct payment processing for appointments
- Discount application support
- Automatic reservation confirmation on payment

### 3. Backward Compatibility
- Existing wallet views redirect to new payment system
- Seamless transition for users
- No breaking changes to existing functionality

## API Endpoints

### 1. Payment Creation
```
POST /payments/api/create/
{
    "amount": 50000,
    "description": "Payment description",
    "gateway_type": "zarinpal",
    "callback_url": "https://example.com/callback",
    "metadata": {...}
}
```

### 2. Payment Verification
```
POST /payments/api/verify/
{
    "authority": "A000000000000000000000000000000000000",
    "amount": 50000
}
```

### 3. Payment Status
```
GET /payments/api/status/{payment_id}/
```

## URL Structure

### 1. User-Facing URLs
- `/payments/` - Payment dashboard
- `/payments/list/` - Payment history
- `/payments/wallet-deposit/` - Wallet top-up
- `/payments/reservation/{id}/` - Reservation payment
- `/payments/callback/` - Payment callback

### 2. API URLs
- `/payments/api/create/` - Create payment
- `/payments/api/verify/` - Verify payment
- `/payments/api/status/{id}/` - Get payment status

## ZarinPal Integration

### 1. Configuration
```bash
# Set up sandbox gateway
python manage.py setup_zarinpal_gateway --sandbox

# Set up production gateway
python manage.py setup_zarinpal_gateway --merchant-id YOUR_MERCHANT_ID
```

### 2. API Flow
1. **Payment Request**: Create payment request with ZarinPal
2. **User Redirect**: Redirect user to ZarinPal payment page
3. **Payment Processing**: User completes payment on ZarinPal
4. **Callback**: ZarinPal redirects back with Authority code
5. **Verification**: Verify payment with ZarinPal API
6. **Completion**: Update payment status and wallet balance

### 3. Error Handling
- Network timeouts
- Invalid responses
- Payment failures
- Expired requests
- Duplicate verifications

## Admin Interface

### 1. PaymentGateway Admin
- Gateway configuration management
- Environment switching
- Commission settings
- API URL management

### 2. PaymentRequest Admin
- Payment request monitoring
- Status management
- Transaction linking
- Log access

### 3. PaymentLog Admin
- Comprehensive logging
- Debug information
- Audit trails

## Security Features

### 1. Input Validation
- Amount limits
- Gateway validation
- User authentication
- CSRF protection

### 2. Transaction Safety
- Database transactions
- Atomic operations
- Rollback on failures
- Duplicate prevention

### 3. Logging & Monitoring
- Complete audit trail
- Error tracking
- Performance monitoring
- Security logging

## Usage Examples

### 1. Wallet Deposit
```python
from payments.services import PaymentService

# Create wallet deposit payment
result = PaymentService.create_payment(
    user=request.user,
    amount=50000,
    description="Wallet deposit",
    gateway_type='zarinpal',
    metadata={'type': 'wallet_deposit'}
)

if result['success']:
    return redirect(result['startpay_url'])
```

### 2. Reservation Payment
```python
# Process reservation payment
result = PaymentService.create_payment(
    user=request.user,
    amount=reservation.amount,
    description=f"Appointment with {reservation.doctor}",
    gateway_type='zarinpal',
    metadata={
        'type': 'reservation_payment',
        'reservation_id': reservation.id
    }
)
```

### 3. Payment Verification
```python
# Verify payment callback
result = PaymentService.verify_payment(
    authority=authority,
    amount=amount
)

if result['success']:
    # Payment successful
    payment_request = result['payment_request']
    # Update reservation status, etc.
```

## Migration Guide

### 1. Database Migration
```bash
python manage.py makemigrations payments
python manage.py migrate
```

### 2. Gateway Setup
```bash
python manage.py setup_zarinpal_gateway --sandbox
```

### 3. URL Updates
- Update main URLs to include payment app
- Existing wallet URLs redirect to new payment system
- No breaking changes for users

## Testing

### 1. Sandbox Testing
- Use ZarinPal sandbox environment
- Test payment flows
- Verify error handling
- Test callback processing

### 2. Production Deployment
- Configure production merchant ID
- Update callback URLs
- Test with real payments
- Monitor logs and performance

## Benefits

### 1. Separation of Concerns
- Payment logic separated from wallet
- Modular architecture
- Easy to extend and maintain

### 2. Real Payment Integration
- Actual ZarinPal API integration
- Production-ready implementation
- Comprehensive error handling

### 3. Enhanced Features
- Multiple gateway support
- Detailed logging
- Admin management
- API endpoints

### 4. Better User Experience
- Seamless payment flow
- Clear status tracking
- Error recovery
- Mobile-friendly interface

## Future Enhancements

### 1. Additional Gateways
- Mellat Bank integration
- Parsian Bank integration
- Saman Bank integration

### 2. Advanced Features
- Recurring payments
- Payment scheduling
- Refund processing
- Dispute handling

### 3. Analytics
- Payment analytics
- Revenue tracking
- Performance metrics
- User behavior analysis

## Conclusion

The new payment system provides a robust, scalable, and maintainable solution for handling payments in the Dr. Turn project. It successfully integrates with the existing wallet system while providing real payment gateway functionality and comprehensive logging and monitoring capabilities. 