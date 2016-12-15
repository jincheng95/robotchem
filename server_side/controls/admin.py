from django.contrib import admin

from .models import Calorimeter, Run, DataPoint


@admin.register(Calorimeter)
class CalorimeterAdmin(admin.ModelAdmin):
    pass


class DataPointInline(admin.TabularInline):
    model = DataPoint
    extra = 1
    max_num = 15


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    inlines = (DataPointInline, )
