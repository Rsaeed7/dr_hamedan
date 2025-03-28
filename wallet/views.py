from decimal import Decimal
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet, InsufficientFunds


# ----- Forms for Wallet Operations -----
class DepositForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Deposit Amount",
        help_text="Enter the amount you wish to deposit."
    )


class WithdrawForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Withdrawal Amount",
        help_text="Enter the amount you wish to withdraw."
    )


# ----- Views -----
@login_required
def wallet_dashboard(request):
    """
    Display the user's wallet dashboard with the current balance and a list of recent transactions.

    If the user does not have a wallet, a new one is created.

    Templates:
        wallet/dashboard.html
    Context:
        wallet: The user's Wallet instance.
        transactions: A queryset of transactions related to the wallet, ordered by timestamp.
    """
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    transactions = wallet.transactions.order_by('-timestamp')
    context = {
        'transactions': transactions
    }
    return render(request, 'wallet/wallet_dashbord.html', context)


@login_required
def deposit(request):
    """
    Handle deposits into the user's wallet.

    Processes the deposit form submission, updates the wallet balance,
    logs the transaction, and displays a success message.

    Templates:
        wallet/deposit.html
    Context:
        form: The deposit form instance.
    """
    wallet = get_object_or_404(Wallet, user=request.user)
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            wallet.deposit(amount)
            messages.success(request, f" افزایش موجودی ({amount} تومان) با موفقیت انجام شد! ")
            return redirect('wallet:wallet_dashboard')
        else:
            messages.error(request, "لطفا مقدار صحیح برای افزایش موجودی وارد کنید!")
    else:
        form = DepositForm()
    return render(request, 'wallet/wallet_deposit.html', {'form': form})


@login_required
def withdraw(request):
    """
    Handle withdrawals from the user's wallet.

    Processes the withdrawal form submission, attempts to deduct the specified
    amount from the wallet, and handles errors if funds are insufficient.

    Templates:
        wallet/withdraw.html
    Context:
        form: The withdrawal form instance.
    """
    wallet = get_object_or_404(Wallet, user=request.user)
    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            try:
                wallet.withdraw(amount)
                messages.success(request, f" برداشت وجه ({amount} تومان) با موفقیت انجام شد! ")
                return redirect('wallet:wallet_dashboard')
            except InsufficientFunds:
                messages.error(request, "موجودی کافی نیست")
        else:
            messages.error(request, "لطفا مبلغ معتبری را برای برداشت وارد کنید.")
    else:
        form = WithdrawForm()
    return render(request, 'wallet/wallet_withdraw.html', {'form': form})
