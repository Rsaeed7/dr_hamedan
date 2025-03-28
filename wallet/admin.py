from django.contrib import admin
from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('created_at',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'timestamp')
    search_fields = ('wallet__user__username',)
    list_filter = ('transaction_type', 'timestamp')
