from support.models import Contact
from doctors.models import Specialization,City
from wallet.models import Transaction

def context_processors(request):
    """
    Context processor to make all specializations available in all templates
    """


    specializations = Specialization.objects.all().order_by('name')
    contact = Contact.objects.last()
    cities = City.objects.all()
    if request.user.is_authenticated:
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
        balance = sum(
            t.amount if t.transaction_type in ['deposit', 'refund'] else -t.amount
            for t in transactions.filter(status='completed')
            )

    else:
        balance = 0

    return {'specializations': specializations , 'contact': contact , 'cities': cities , 'balance' : balance}
