from django.conf import settings
from django.db import models


class TripQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(models.Q(owner=user) | models.Q(members__user=user)).distinct()


class Trip(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_trips",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TripQuerySet.as_manager()

    ROLE_OWNER = "owner"

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.start_date}~{self.end_date})"

    def role_of(self, user):
        if self.owner_id == user.id:
            return self.ROLE_OWNER
        member = next((m for m in self.members.all() if m.user_id == user.id), None)
        return member.role if member else None


class TripMember(models.Model):
    class Role(models.TextChoices):
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trip_memberships",
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("trip", "user")]

    def __str__(self):
        return f"{self.user} in {self.trip} ({self.role})"


class TripDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="days")
    date = models.DateField()
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]
        unique_together = [("trip", "date")]

    def __str__(self):
        return f"{self.trip_id} - {self.date}"


class Attraction(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, default="")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_attractions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Activity(models.Model):
    day = models.ForeignKey(TripDay, on_delete=models.CASCADE, related_name="activities")
    attraction = models.ForeignKey(
        Attraction,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activities",
    )
    title = models.CharField(max_length=255)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    note = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [
            models.Index(fields=["day", "order"]),
        ]

    def __str__(self):
        return f"{self.title} (day={self.day_id})"
