from management.models import Hostel_owner, Student


def user_role_flags(request):
    if not request.user.is_authenticated:
        return {'is_owner': False, 'is_student': False, 'is_admin': False}

    user = request.user
    return {
        'is_owner': Hostel_owner.objects.filter(user=user).exists(),
        'is_student': Student.objects.filter(user=user).exists(),
        'is_admin': user.is_staff or user.is_superuser,
    }
