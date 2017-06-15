from django.contrib import admin

from user import models


admin.site.register(models.UserPreferences, admin.ModelAdmin)
