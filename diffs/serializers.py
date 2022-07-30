# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from diffs.models import *


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
                fields=('project', 'last_commit_hash', 'release'),
                message="The release has existed in the project. You should check the info."
            )
        ]

class CommitSerializer(serializers.ModelSerializer):
    release = ReleaseSerializer
    time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")

    class Meta:
        model = Commit
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=Commit.objects.all(),
                fields=("hash"),
                message="The commit has existed."
            )
        ]


class ObjectSerializer(serializers.ModelSerializer):
    project = ProjectSerializer

    class Meta:
        model = Object
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=Commit.objects.all(),
                fields=("funcion_id","file_path","project"),
                message="The object has existed."
            )
        ]
        
        



# class ObjectChangeSerializer(serializers.ModelSerializer):
#     release = ReleaseSerializer 
#     project = ProjectSerializer
#     commit = CommitSerializer
#     object = ObjectSerializer

#     class Meta:
#         model = ObjectChange
#         fields = "__all__"
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=ObjectChange.objects.all(),
#                 fields=('commit', 'object','project','release'),
#                 message="The object_change has existed."
#             )
#         ]



# class TempObjectChangeSerializer(serializers.ModelSerializer):
#     commit = CommitSerializer

#     class Meta:
#         model = TempObjectChange
#         fields = "__all__"
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=TempObjectChange.objects.all(),
#                 fields=('commit', 'new_object_id'),
#                 message="The temp_object_change has existed."
#             )
#         ]