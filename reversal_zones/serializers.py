from rest_framework import serializers
from .models import ReversalZone, SyntheticPathSegment, ReversalStatus


class ReversalZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReversalZone
        fields = '__all__'


class SyntheticPathSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyntheticPathSegment
        fields = '__all__'


class ReversalStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReversalStatus
        fields = '__all__'
