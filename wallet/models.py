from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models import F


class InsufficientFunds(Exception):
    """Raised when the wallet balance is insufficient for a withdrawal or payment."""
    pass


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet', verbose_name='کاربر')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name='موجودی')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف های پول'

    def __str__(self) -> str:
        return f"{self.user.username} - Balance: {self.balance}"

    def deposit(self, amount: Decimal) -> None:
        """
        Deposit funds into the wallet.

        Args:
            amount (Decimal): The amount to deposit.
        """
        with transaction.atomic():
            self.balance += amount  # directly update the balance
            self.save(update_fields=['balance'])
            Transaction.objects.create(wallet=self, amount=amount, transaction_type=Transaction.DEPOSIT)

    def withdraw(self, amount: Decimal) -> None:
        """
        Withdraw funds from the wallet if sufficient balance exists.

        Args:
            amount (Decimal): The amount to withdraw.

        Raises:
            InsufficientFunds: If the wallet balance is less than the withdrawal amount.
        """
        with transaction.atomic():
            self.refresh_from_db(fields=['balance'])
            if self.balance < amount:
                raise InsufficientFunds("Insufficient funds in wallet.")
            self.balance -= amount  # directly update the balance
            self.save(update_fields=['balance'])
            Transaction.objects.create(wallet=self, amount=-amount, transaction_type=Transaction.WITHDRAWAL)

    def make_payment(self, amount: Decimal) -> None:
        """
        Make a payment by withdrawing the specified amount.

        Args:
            amount (Decimal): The payment amount.

        Raises:
            InsufficientFunds: If the wallet balance is insufficient.
        """
        self.withdraw(amount)


class Transaction(models.Model):
    DEPOSIT = 'واریز'
    WITHDRAWAL = 'برداشت'
    PURCHASE = 'purchase'

    TRANSACTION_TYPES = [
        (DEPOSIT, 'واریز'),
        (WITHDRAWAL, 'برداشت'),
        (PURCHASE, 'Purchase'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2 ,verbose_name='مقدار')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.wallet.user.username} - {self.transaction_type} - {self.amount}"
