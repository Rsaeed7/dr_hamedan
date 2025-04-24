from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from .models import Transaction
from reservations.models import Reservation

@login_required
def wallet_dashboard(request):
    """Display user's wallet and transaction history summary"""
    # Get user's transactions
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate balance (sum of completed transactions)
    balance = sum(
        t.amount if t.transaction_type in ['deposit', 'refund'] else -t.amount 
        for t in transactions.filter(status='completed')
    )
    
    # Get recent transactions
    recent_transactions = transactions[:5]
    
    context = {
        'balance': balance,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'wallet/dashboard.html', context)

@login_required
def transaction_list(request):
    """Display all user transactions"""
    # Get filter parameters
    transaction_type = request.GET.get('type', 'all')
    status = request.GET.get('status', 'all')
    
    # Get all user transactions
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply filters
    if transaction_type != 'all':
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if status != 'all':
        transactions = transactions.filter(status=status)
    
    context = {
        'transactions': transactions,
        'transaction_type': transaction_type,
        'status': status,
    }
    
    return render(request, 'wallet/transactions.html', context)

def process_payment(request, reservation_id):
    """Process payment for a reservation"""
    # Get the reservation
    reservation = get_object_or_404(Reservation, id=reservation_id, status='pending', payment_status='pending')
    
    if request.method == 'POST':
        # Here you would integrate with a payment gateway
        # For demo purposes, we'll create a transaction and simulate payment
        
        # Create a transaction record
        transaction = Transaction.objects.create(
            user=request.user if request.user.is_authenticated else reservation.patient.user,
            amount=reservation.amount,
            transaction_type='payment',
            status='pending',
            description=f"Payment for appointment with {reservation.doctor} on {reservation.day.date} at {reservation.time}"
        )
        
        # Link transaction to reservation
        reservation.transaction = transaction
        reservation.save()
        
        # In a real system, redirect to payment gateway
        # For demo, simulate successful payment
        return redirect('wallet:payment_callback')
    
    context = {
        'reservation': reservation,
    }
    
    return render(request, 'wallet/payment.html', context)

def payment_callback(request):
    """Handle payment gateway callback"""
    # In a real system, this would verify the payment with the gateway
    # For demo purposes, we'll simulate a successful payment
    
    # Get payment reference from query params
    transaction_id = request.GET.get('transaction_id')
    status = request.GET.get('status', 'completed')  # Default to completed for demo
    
    if transaction_id:
        # Find the transaction
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            transaction.status = status
            transaction.save()
            
            # Update reservation if this transaction is linked to one
            reservations = transaction.reservations.all()
            if reservations.exists():
                reservation = reservations.first()
                reservation.payment_status = 'paid' if status == 'completed' else 'failed'
                reservation.save()
                
                if status == 'completed':
                    # Auto-confirm the appointment
                    reservation.confirm_appointment()
                    messages.success(request, "Payment successful! Your appointment has been confirmed.")
                else:
                    messages.error(request, "Payment failed. Please try again.")
            
            return redirect('reservations:appointment_status', pk=reservation.id)
        
        except Transaction.DoesNotExist:
            messages.error(request, "Transaction not found.")
    
    # Demo: Just simulate a successful payment for the most recent pending reservation
    if request.user.is_authenticated:
        recent_transaction = Transaction.objects.filter(
            user=request.user,
            status='pending',
            transaction_type='payment'
        ).order_by('-created_at').first()
        
        if recent_transaction:
            recent_transaction.status = 'completed'
            recent_transaction.save()
            
            # Update reservation
            reservations = recent_transaction.reservations.all()
            if reservations.exists():
                reservation = reservations.first()
                reservation.payment_status = 'paid'
                reservation.save()
                
                # Auto-confirm the appointment
                reservation.confirm_appointment()
                messages.success(request, "Payment successful! Your appointment has been confirmed.")
                
                return redirect('reservations:appointment_status', pk=reservation.id)
    
    messages.info(request, "Payment process completed.")
    return redirect('home')
