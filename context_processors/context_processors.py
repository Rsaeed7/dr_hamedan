from support.models import Contact
from doctors.models import Specialization,City
from wallet.models import Transaction

def context_processors(request):
    specializations = Specialization.objects.all().order_by('name')
    contact = Contact.objects.last()
    cities = City.objects.all()
    balance = 0
    doctor = None

    if request.user.is_authenticated:
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
        balance = sum(
            t.amount if t.transaction_type in ['deposit', 'refund'] else -t.amount
            for t in transactions.filter(status='completed')
        )

        if hasattr(request.user, 'doctor'):
            doctor = request.user.doctor

    return {
        'specializations': specializations,
        'contact': contact,
        'cities': cities,
        'balance': balance,
        'doctor': doctor
    }
