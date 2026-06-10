from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from trips.models import Attraction, Trip, TripMember
from trips.serializers import (
    ActivitySerializer,
    AttractionSerializer,
    TripDaySerializer,
    TripDetailSerializer,
    TripListSerializer,
    TripMemberCreateSerializer,
    TripMemberSerializer,
    TripSerializer,
)


class TripListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Trip.objects.for_user(self.request.user).prefetch_related("members")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TripSerializer
        return TripListSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TripDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Trip.objects.for_user(self.request.user).prefetch_related("members", "days__activities__attraction")

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return TripSerializer
        return TripDetailSerializer

    def get_object(self):
        trip = super().get_object()
        role = trip.role_of(self.request.user)
        if self.request.method in ("PUT", "PATCH") and role not in (Trip.ROLE_OWNER, TripMember.Role.EDITOR):
            raise PermissionDenied("僅行程擁有者或編輯者可修改行程。")
        if self.request.method == "DELETE" and role != Trip.ROLE_OWNER:
            raise PermissionDenied("僅行程擁有者可刪除行程。")
        return trip


class AttractionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AttractionSerializer
    queryset = Attraction.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AttractionDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AttractionSerializer
    queryset = Attraction.objects.all()


class TripNestedMixin:
    """巢狀於行程下的資源：非參與者一律 404，寫入需 owner / editor 角色。"""

    permission_classes = [IsAuthenticated]
    write_methods = ("POST", "PUT", "PATCH", "DELETE")

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.trip = get_object_or_404(Trip.objects.for_user(request.user), pk=self.kwargs["trip_id"])
        if request.method in self.write_methods:
            role = self.trip.role_of(request.user)
            if role not in (Trip.ROLE_OWNER, TripMember.Role.EDITOR):
                raise PermissionDenied("僅行程擁有者或編輯者可編輯行程內容。")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["trip"] = self.trip
        return context


class TripDayListCreateView(TripNestedMixin, generics.ListCreateAPIView):
    serializer_class = TripDaySerializer

    def get_queryset(self):
        return self.trip.days.all()

    def perform_create(self, serializer):
        serializer.save(trip=self.trip)


class TripDayDetailView(TripNestedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TripDaySerializer

    def get_queryset(self):
        return self.trip.days.all()


class TripDayNestedMixin(TripNestedMixin):
    """巢狀於某一天之下的資源：URL 的 day 必須屬於該行程，否則 404。"""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.day = get_object_or_404(self.trip.days, pk=self.kwargs["day_id"])


class ActivityListCreateView(TripDayNestedMixin, generics.ListCreateAPIView):
    serializer_class = ActivitySerializer

    def get_queryset(self):
        return self.day.activities.select_related("attraction")

    def perform_create(self, serializer):
        serializer.save(day=self.day)


class ActivityDetailView(TripDayNestedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ActivitySerializer

    def get_queryset(self):
        return self.day.activities.select_related("attraction")


class TripMemberListCreateView(TripNestedMixin, generics.ListCreateAPIView):
    # 成員管理不走 owner / editor 的內容編輯規則，由本 view 自行檢查僅 owner 可新增
    write_methods = ()

    def get_queryset(self):
        return self.trip.members.select_related("user")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TripMemberCreateSerializer
        return TripMemberSerializer

    def create(self, request, *args, **kwargs):
        if self.trip.owner_id != request.user.id:
            raise PermissionDenied("僅行程擁有者可分享行程。")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        return Response(TripMemberSerializer(member).data, status=status.HTTP_201_CREATED)


class TripMemberRemoveView(TripNestedMixin, APIView):
    write_methods = ()

    def delete(self, request, trip_id, user_id):
        is_owner = self.trip.owner_id == request.user.id
        if not (is_owner or user_id == request.user.id):
            raise PermissionDenied("僅行程擁有者可移除成員。")
        member = self.trip.members.filter(user_id=user_id).first()
        if member is None:
            raise NotFound("該使用者不是行程成員。")
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
