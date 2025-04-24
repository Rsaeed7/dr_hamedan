from doctors.models import Specialization

def specializations_processor(request):
    """
    Context processor to make all specializations available in all templates
    """
    specializations = Specialization.objects.all().order_by('name')
    return {'specializations': specializations} 