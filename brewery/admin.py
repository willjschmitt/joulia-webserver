from django.contrib import admin

from . import models

admin.site.register(models.BrewingFacility, admin.ModelAdmin)
admin.site.register(models.BrewingCompany, admin.ModelAdmin)

admin.site.register(models.Brewhouse, admin.ModelAdmin)
admin.site.register(models.AssetSensor, admin.ModelAdmin)

admin.site.register(models.Recipe,admin.ModelAdmin)
admin.site.register(models.RecipeInstance,admin.ModelAdmin)
admin.site.register(models.BeerStyle,admin.ModelAdmin)
