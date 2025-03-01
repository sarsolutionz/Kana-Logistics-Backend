from django.contrib import admin
from AuthApp.models import Driver
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.


class DriverAdmin(admin.ModelAdmin):
    list_display = ["short_id", "email", "name", "number", "is_deleted"]
    list_filter = ["email"]
    fieldsets = [
        ("User Credentials", {"fields": ["email", "number"]}),
        ("Personal info", {"fields": ["name"]}),
        ("Permissions", {"fields": ["is_deleted"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["email", "name", "number", "is_deleted"],
            },
        ),
    ]
    search_fields = ["email"]
    ordering = ["email", "id"]
    filter_horizontal = []

admin.site.register(Driver, DriverAdmin)