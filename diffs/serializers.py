# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from diffs.models import Release
from diffs.models import Project
from diffs.models import Object


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class ReleaseSerializer(serializers.ModelSerializer):
    project = ProjectSerializer

    class Meta:
        model = Release
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=Release.objects.all(),
                fields=('project', 'commit_hash', 'release'),
                message="The release has existed in the project. You should check the info."
            )
        ]


class ObjectSerializer(serializers.ModelSerializer):
    project = ProjectSerializer
    release = ReleaseSerializer
    commit_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")

    class Meta:
        model = Object
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=Object.objects.all(),
                fields=('project', 'release', 'name', 'file_path', 'commit_time'),
                message="The object has existed."
            )
        ]





