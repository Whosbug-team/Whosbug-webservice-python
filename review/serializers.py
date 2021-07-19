# -*- coding: utf-8 -*-
from rest_framework import serializers
from diffs.serializers import ProjectSerializer
from review.models import Reviewer
from review.models import Rule


class ReviewerSerializer(serializers.ModelSerializer):
    project = ProjectSerializer

    class Meta:
        model = Reviewer
        fields = "__all__"


class RuleSerializer(serializers.ModelSerializer):
    project = ProjectSerializer

    class Meta:
        model = Rule
        fields = "__all__"
