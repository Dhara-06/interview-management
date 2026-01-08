from django.contrib import admin
from .models import Interview

class InterviewAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'HR'

    def has_change_permission(self, request, obj=None):
        return hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'HR'

    def has_delete_permission(self, request, obj=None):
        return hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'HR'

admin.site.register(Interview, InterviewAdmin)
