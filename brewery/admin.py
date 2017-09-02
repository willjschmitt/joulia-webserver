"""Admin panel registrations for brewery app.
"""

from django.contrib import admin

from brewery import models

admin.site.register(models.JouliaControllerRelease, admin.ModelAdmin)

admin.site.register(models.Brewery, admin.ModelAdmin)
admin.site.register(models.BrewingCompany, admin.ModelAdmin)

admin.site.register(models.Brewhouse, admin.ModelAdmin)
admin.site.register(models.AssetSensor, admin.ModelAdmin)

admin.site.register(models.Recipe, admin.ModelAdmin)
admin.site.register(models.RecipeInstance, admin.ModelAdmin)

admin.site.register(models.BeerStyle, admin.ModelAdmin)
admin.site.register(models.MaltIngredient, admin.ModelAdmin)
admin.site.register(models.BitteringIngredient, admin.ModelAdmin)
admin.site.register(models.MaltIngredientAddition, admin.ModelAdmin)
admin.site.register(models.BitteringIngredientAddition, admin.ModelAdmin)
