from django.contrib import admin

from .models import Brewery, Asset, AssetSensor
from .models import Recipe, RecipeInstance,BeerStyle

admin.site.register(Brewery, admin.ModelAdmin)
admin.site.register(Asset, admin.ModelAdmin)
admin.site.register(AssetSensor, admin.ModelAdmin)

admin.site.register(Recipe,admin.ModelAdmin)
admin.site.register(RecipeInstance,admin.ModelAdmin)
admin.site.register(BeerStyle,admin.ModelAdmin)
