from django.contrib import admin

from trips.models import Activity, Attraction, Trip, TripDay, TripMember


class TripMemberInline(admin.TabularInline):
    model = TripMember
    extra = 0
    readonly_fields = ("created_at",)


class TripDayInline(admin.TabularInline):
    model = TripDay
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "start_date", "end_date", "created_at")
    search_fields = ("title",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [TripDayInline, TripMemberInline]


@admin.register(TripDay)
class TripDayAdmin(admin.ModelAdmin):
    list_display = ("id", "trip", "date", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "day", "attraction", "start_time", "end_time", "order", "created_at")
    search_fields = ("title",)
    readonly_fields = ("created_at",)


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address", "created_by", "created_at")
    search_fields = ("name", "address")
    readonly_fields = ("created_at",)


@admin.register(TripMember)
class TripMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "trip", "user", "role", "created_at")
    list_filter = ("role",)
    readonly_fields = ("created_at",)
