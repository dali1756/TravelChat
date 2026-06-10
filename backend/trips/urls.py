from django.urls import path

from trips.views import (
    ActivityDetailView,
    ActivityListCreateView,
    AttractionDetailView,
    AttractionListCreateView,
    TripDayDetailView,
    TripDayListCreateView,
    TripDetailView,
    TripListCreateView,
    TripMemberListCreateView,
    TripMemberRemoveView,
)

urlpatterns = [
    path("", TripListCreateView.as_view(), name="trip_list_create"),
    path("attractions/", AttractionListCreateView.as_view(), name="attraction_list_create"),
    path("attractions/<int:pk>/", AttractionDetailView.as_view(), name="attraction_detail"),
    path("<int:pk>/", TripDetailView.as_view(), name="trip_detail"),
    path("<int:trip_id>/days/", TripDayListCreateView.as_view(), name="trip_day_list_create"),
    path("<int:trip_id>/days/<int:pk>/", TripDayDetailView.as_view(), name="trip_day_detail"),
    path(
        "<int:trip_id>/days/<int:day_id>/activities/",
        ActivityListCreateView.as_view(),
        name="activity_list_create",
    ),
    path(
        "<int:trip_id>/days/<int:day_id>/activities/<int:pk>/",
        ActivityDetailView.as_view(),
        name="activity_detail",
    ),
    path("<int:trip_id>/members/", TripMemberListCreateView.as_view(), name="trip_member_list_create"),
    path("<int:trip_id>/members/<int:user_id>/", TripMemberRemoveView.as_view(), name="trip_member_remove"),
]
