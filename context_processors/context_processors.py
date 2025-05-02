from about_us.models import Contact
from doctors.models import Specialization, City


def context_processors(request):
    """
    Context processor to make all specializations available in all templates
    """
    specializations = Specialization.objects.all().order_by('name')
    contact = Contact.objects.last()
    cities = City.objects.all()
    return {'specializations': specializations , 'contact': contact , 'cities': cities}
