from .models import Wallet


def wallet(request):
    if request.user.is_authenticated:
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        return {'wallet': wallet}
    else:
        return {'wallet': None}