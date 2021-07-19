# -*- coding: utf-8 -*-
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from review.serializers import ReviewerSerializer
from review.serializers import RuleSerializer
from diffs.serializers import ProjectSerializer
from diffs.models import Project

@api_view(['POST'])
def commit_reviewers(request):
    """
    You can commit the reviewer of the specific file
    """
    # get the project
    project = request.data['project']
    files = request.data['file']
    project_serializer = ProjectSerializer(data=project)
    if project_serializer.is_valid():
        project_id = project_serializer.save().id
    else:
        project_id = Project.objects.get(pid=project['pid']).id
    # create reviewer
    for file in files:
        reviewer = {
            'project': project_id,
            'file_path': file['path'],
            'review_rule': file['owner_rule'],
            'reviewer': None,
        }
        for owner in file['owners']:
            reviewer['reviewer'] = owner
            reviewerSerializer = ReviewerSerializer(data=reviewer)
            if reviewerSerializer.is_valid():
                reviewerSerializer.save()
    return Response(status=status.HTTP_201_CREATED)


@api_view(['POST'])
def commit_rules(request):
    """
    You can commit the white rule(file) of the specific file
    """
    project = request.data['project']
    files = request.data['file']
    projectSerializer = ProjectSerializer(data=project)
    if projectSerializer.is_valid():
        projectId = projectSerializer.save().id
    else:
        projectId = Project.objects.get(pid=project['pid']).id
    # create rule
    for file in files:
        rule = {
            'project': projectId,
            'file': file,
        }
        ruleSerializer = RuleSerializer(data=rule)
        if ruleSerializer.is_valid():
            ruleSerializer.save()
    return Response(status=status.HTTP_201_CREATED)
