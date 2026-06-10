from rest_framework import serializers

from members.models import User
from trips.models import Activity, Attraction, Trip, TripDay, TripMember


class AttractionSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Attraction
        fields = ["id", "name", "address"]


class ActivityNestedSerializer(serializers.ModelSerializer):
    attraction = AttractionSummarySerializer(read_only=True)

    class Meta:
        model = Activity
        fields = ["id", "title", "attraction", "start_time", "end_time", "note", "order"]


class TripDayNestedSerializer(serializers.ModelSerializer):
    activities = ActivityNestedSerializer(many=True, read_only=True)

    class Meta:
        model = TripDay
        fields = ["id", "date", "note", "activities"]


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ["id", "title", "description", "start_date", "end_date", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_date", self.instance.start_date if self.instance else None)
        end = attrs.get("end_date", self.instance.end_date if self.instance else None)
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "結束日期不得早於起始日期。"})
        if self.instance and self.instance.days.exclude(date__range=(start, end)).exists():
            raise serializers.ValidationError("行程已有排程日期超出新的日期範圍，請先刪除超出範圍的天。")
        return attrs


class AttractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attraction
        fields = ["id", "name", "address", "latitude", "longitude", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class TripDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = TripDay
        fields = ["id", "date", "note", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_date(self, value):
        trip = self.context["trip"]
        if not (trip.start_date <= value <= trip.end_date):
            raise serializers.ValidationError("日期必須在行程起訖範圍內。")
        existing = trip.days.filter(date=value)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError("該日期已存在於此行程。")
        return value


class ActivitySerializer(serializers.ModelSerializer):
    attraction = AttractionSummarySerializer(read_only=True)
    attraction_id = serializers.PrimaryKeyRelatedField(
        source="attraction",
        queryset=Attraction.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    day = serializers.PrimaryKeyRelatedField(queryset=TripDay.objects.all(), required=False)

    class Meta:
        model = Activity
        fields = [
            "id",
            "day",
            "title",
            "attraction",
            "attraction_id",
            "start_time",
            "end_time",
            "note",
            "order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_day(self, value):
        trip = self.context["trip"]
        if value.trip_id != trip.id:
            raise serializers.ValidationError("不能將活動搬移至其他行程的天。")
        return value

    def validate(self, attrs):
        start = attrs.get("start_time", self.instance.start_time if self.instance else None)
        end = attrs.get("end_time", self.instance.end_time if self.instance else None)
        if start and end and end < start:
            raise serializers.ValidationError({"end_time": "結束時間不得早於開始時間。"})
        return attrs


class MemberUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class TripMemberSerializer(serializers.ModelSerializer):
    user = MemberUserSerializer(read_only=True)

    class Meta:
        model = TripMember
        fields = ["id", "user", "role", "created_at"]


class TripMemberCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=TripMember.Role.choices, default=TripMember.Role.VIEWER)

    def validate_user_id(self, value):
        trip = self.context["trip"]
        if not User.objects.public().filter(id=value).exists():
            raise serializers.ValidationError("找不到該使用者。")
        if value == trip.owner_id:
            raise serializers.ValidationError("不能分享給行程擁有者自己。")
        if trip.members.filter(user_id=value).exists():
            raise serializers.ValidationError("該使用者已是行程成員。")
        return value

    def create(self, validated_data):
        return TripMember.objects.create(
            trip=self.context["trip"],
            user_id=validated_data["user_id"],
            role=validated_data["role"],
        )


class TripRoleMixin(serializers.Serializer):
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        return obj.role_of(self.context["request"].user)


class TripListSerializer(TripRoleMixin, TripSerializer):
    class Meta(TripSerializer.Meta):
        fields = [*TripSerializer.Meta.fields, "role"]


class TripDetailSerializer(TripRoleMixin, TripSerializer):
    days = TripDayNestedSerializer(many=True, read_only=True)

    class Meta(TripSerializer.Meta):
        fields = [*TripSerializer.Meta.fields, "role", "days"]
