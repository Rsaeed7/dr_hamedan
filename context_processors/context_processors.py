from support.models import Contact
from doctors.models import Specialization,City
from wallet.models import Transaction, Wallet

def context_processors(request):
    """
    Context processor to make all specializations available in all templates
    """

    specializations = Specialization.objects.all().order_by('name')
    contact = Contact.objects.last()
    cities = City.objects.all()
    
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
