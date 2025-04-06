from contact.models import Contact


def context_proccesors(request):
    contact = Contact.objects.last()
    return {'contact': contact}
