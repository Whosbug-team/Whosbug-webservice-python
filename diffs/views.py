# -*- coding: utf-8 -*-
from typing import List

from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework import mixins, generics
from diffs.models import Project, Release, Object
from review.models import Rule, Reviewer
from diffs.serializers import ProjectSerializer
from diffs.serializers import ReleaseSerializer
from diffs.serializers import ObjectSerializer
import json
from django.db.models import Max
from .bug_owner import Method
from .utils import get_matched_methods
from .utils import calculate_method_weight
from .utils import analysis_stack
from .utils import analysis_total
from .utils import get_reviewers
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


@api_view(['POST'])
def get_last_release(request):
    """
    You can automatically find the last release in the project.
    """
    try:
        project = Project.objects.get(pid=request.data['pid'])
    except Project.DoesNotExist:
        return Response("The Project Not Found.", status=404)
    releases = Release.objects.filter(project=project)
    try:
        latest_release = Release.objects.get(pk=releases.aggregate(Max('id'))['id__max'])
    except Release.DoesNotExist:
        return Response("The Project has no Release now.", status=404)
    serializer = ReleaseSerializer(latest_release)
    return Response(serializer.data)


@swagger_auto_schema(
    operation_summary='一次性POST project,release 和objects',
    operation_description='一次性上传方法或类的信息，其中还包括该修改方法所发布的产品信息和项目信息\n',
    methods=['POST'],
    request_body=openapi.Schema(
        type="object",
        properties={
            'project': openapi.Schema(
                type="object",
                properties={
                    'PID': openapi.Schema(type="string")
                }
            ),
            'release': openapi.Schema(
                type="object",
                properties={
                    'commit_hash': openapi.Schema(type="string"),
                    'version': openapi.Schema(type="string")
                }
            ),
            'objects': openapi.Schema(
                type="array",
                items=openapi.Schema(
                    type="object",
                    properties={
                        'name': openapi.Schema(type="string"),
                        'hash': openapi.Schema(type="string"),
                        'file_path': openapi.Schema(type="string"),
                        'owner': openapi.Schema(type="string"),
                        'commit_time': openapi.Schema(type="string"),
                        'parent_name': openapi.Schema(type="string"),
                        'parent_hash': openapi.Schema(type="string"),
                        'old_name': openapi.Schema(type="string")
                    }
                )
            )
        }
    ),
    responses={201: 'All data has been inserted to database.'}
)
@api_view(['POST'])
def commit_diffs(request):
    """
    You can commit info: Project, Release and Objects at once.
    """
    project = request.data['project']
    release = request.data['release']
    objects = request.data['objects']

    project_serializer = ProjectSerializer(data=project)
    # serializer use id.
    try:
        project_id = Project.objects.get(pid=project['pid']).id
    except Project.DoesNotExist:
        if project_serializer.is_valid():
            project_id = project_serializer.save().id
        else:
            return Response("The project format is not valid.", status=404)
    release['project'] = project_id
    release_serializer = ReleaseSerializer(data=release)
    try:
        release_id = Release.objects.get(project=project_id, release=release['release']).id
    except Release.DoesNotExist:
        if release_serializer.is_valid():
            release_id = release_serializer.save().id
        else:
            return Response("The release format is not valid.", status=404)

    # create objects
    for obj in objects:
        obj['project'] = project_id
        obj['release'] = release_id
        object_serializer = ObjectSerializer(data=obj)
        if object_serializer.is_valid():
            object_serializer.save()
        else:
            return Response("The object format is not valid.", status=404)
    return Response(status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    operation_summary='返回造成该堆栈错误的bug owners',
    operation_description='参数是project_PID, release_version, object_name',
    methods=['POST'],
    request_body=openapi.Schema(
        type="object",
        properties={
            'PID': openapi.Schema(type="string"),
            'version': openapi.Schema(type="string"),
            'match_choice(exact|prop)': openapi.Schema(
                type="string",
                enum=['exact', 'prop']
            ),
            'stacks': openapi.Schema(
                type="array",
                items=openapi.Schema(
                    type="object",
                    properties={
                        'methods': openapi.Schema(
                            type="array",
                            items=openapi.Schema(type="string")
                        ),
                        'file_path': openapi.Schema(
                            type="array",
                            items=openapi.Schema(type="string")
                        )
                    }
                )
            )
        }
    ),
    responses={
        200: openapi.Schema(
            type="object",
            properties={
                'total_analysis': openapi.Schema(
                    type="array",
                    items=openapi.Schema(
                        type="object",
                        properties={
                            'owner': openapi.Schema(type="string"),
                            'confidence': openapi.Schema(type="integer")

                        }
                    )
                ),
                'stack_analysis': openapi.Schema(
                    type="array",
                    items=openapi.Schema(
                        type="object",
                        properties={
                            'owner': openapi.Schema(type="string"),
                            'confidence': openapi.Schema(type="integer"),
                            'methods': openapi.Schema(
                                type="array",
                                items=openapi.Schema(type="string")
                            )
                        }
                    )
                )
            }
        )
    }
)
@api_view(['POST'])
def get_bug_owners(request):
    """
    You can get the bug owners.
    """

    try:
        project = Project.objects.get(pid=request.data['pid'])
    except Project.DoesNotExist:
        return Response("The project Dose Not Exist.", status=404)
    try:
        release = Release.objects.get(release=request.data['release'], project=project)
    except Release.DoesNotExist:
        return Response("The Release Dose Not Exist.", status=404)

    stacks = request.data['stacks']
    if (request.data['match_choice(exact|fuzzy)'] != 'exact'
            and request.data['match_choice(exact|fuzzy)'] != 'fuzzy'):
        return Response("Please Choose match_choice again!", status=404)

    # all objects modified before the release in the project
    all_objects = Object.objects.filter(project=project, release_id__lte=release.id).order_by('-commit_time')
    white_objects = Rule.objects.filter(project=project)
    # exclude all objects in white rules
    for white_object in white_objects:
        all_objects.exclude(file_path=white_object.file)
    review_objects = Reviewer.objects.filter(project=project)

    result = {
        'total_analysis': {
            'reviewers': None,
            'bug_owners': None,
        },
        'stack_analysis': None,
    }
    stacks_analysis = []
    fuzzy_stacks_analysis = []
    stacks_confidence = {}
    fuzzy_stacks_confidence = {}
    reviewer_count = {}

    for stack in stacks:
        # exact match
        exact_matched_methods, exact_methods_hash = get_matched_methods(all_objects,
                                                                        stack['methods'],
                                                                        stack['file_path'])
        # If not matched
        if len(exact_matched_methods) == 0:
            return Response("The method in stacks Dose Not Exist in database.", status=404)
        # calculate method weight
        bug_owners, stack_weights, to_parent_weights = calculate_method_weight(matched_methods=exact_matched_methods,
                                                                               mode="exact",
                                                                               connection_weights=None)
        # exact match
        if request.data['match_choice(exact|fuzzy)'] == 'exact':
            # statistic and analysis methods in one stack and bug owners
            analysis_result, stacks_confidence = analysis_stack(bug_owners, stack_weights, stacks_confidence)
            stacks_analysis.append(analysis_result)
            # statistic reviewers about one stack methods
            reviewer_count = get_reviewers(exact_matched_methods, review_objects, reviewer_count)
            continue

        # fuzzy match

        # raw query: RECURSIVE SELECT: find all methods which have connection with exact matched method
        # (parent class or old_name methods)
        # foreign key : diffs_object.project_id
        # 想遍历RawQuerySet必须要select id才行
        query = '''
            WITH RECURSIVE cte AS (
                SELECT id, name, hash, old_name, parent_name, parent_hash, owner, commit_time
                FROM diffs_object
                WHERE diffs_object.project_id = %s and diffs_object.release_id <= %s and hash in %s 
                UNION ALL 
                SELECT o.id, o.name, o.hash, o.old_name, o.parent_name,o.parent_hash, o.owner, o.commit_time
                FROM diffs_object o inner join cte on o.hash = cte.parent_hash OR o.name = cte.old_name
                WHERE o.project_id = %s and o.release_id <= %s 
                )
            SELECT * FROM cte 
            ORDER BY commit_time DESC;
            '''
        fuzzy_matched_objects = Object.objects.raw(query,
                                                   [project.id,
                                                    release.id,
                                                    tuple(exact_methods_hash),
                                                    project.id,
                                                    release.id])
        fuzzy_matched_methods: List[Method] = []
        for obj in fuzzy_matched_objects:
            fuzzy_matched_methods.append(Method(obj))
        # calculate fuzzy methods weight
        fuzzy_bug_owners, fuzzy_stack_weights, _ = calculate_method_weight(matched_methods=fuzzy_matched_methods,
                                                                           mode="fuzzy",
                                                                           connection_weights=to_parent_weights)
        # statistic and analysis fuzzy methods in one stack and bug owners
        fuzzy_analysis_result, fuzzy_stacks_confidence = analysis_stack(fuzzy_bug_owners,
                                                                        fuzzy_stack_weights,
                                                                        fuzzy_stacks_confidence,
                                                                        "fuzzy", bug_owners)
        fuzzy_stacks_analysis.append(fuzzy_analysis_result)
        # statistic reviewers about one stack methods
        reviewer_count = get_reviewers(fuzzy_matched_methods, review_objects, reviewer_count)

    # result
    if request.data['match_choice(exact|fuzzy)'] == 'exact':
        result['stack_analysis'] = stacks_analysis
        result['total_analysis']['reviewers'], result['total_analysis']['bug_owners'] = analysis_total(
            reviewer_cnt=reviewer_count,
            owner_confidence=stacks_confidence)
    else:
        result['stack_analysis'] = fuzzy_stacks_analysis
        result['total_analysis']['reviewers'], result['total_analysis']['bug_owners'] = analysis_total(
            reviewer_cnt=reviewer_count,
            owner_confidence=fuzzy_stacks_confidence)

    resultSerializer = json.dumps(result, sort_keys=False, indent=4, separators=(',', ':'))
    return HttpResponse(resultSerializer, status=200, content_type='application/json')


@api_view(['GET'])
def liveness_probe(request):
    """
    secure the liveness of the webservice
    """
    return Response('Webservice survive', status=200)


class ProjectList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @swagger_auto_schema(
        operation_summary='返回Project列表'
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='新建一个Project'
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    # 继承APIView的写法
    # def get(self, request, format=None):
    #     projects = Project.objects.all()
    #     serializer = ProjectSerializer(projects, many=True)
    #     return Response(serializer.data)
    #
    # # POST a new project
    # def post(self, request, format=None):
    #     serializer = ProjectSerializer(data=request.data)
    #     # create a project
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @swagger_auto_schema(
        operation_summary='检索一个Project'
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='更新一个Project'
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='删除一个Project'
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    # 继承APIView的写法
    # def get_project(self, pk):
    #     try:
    #         return Project.objects.get(pk=pk)
    #     except Project.DoesNotExist:
    #         raise Http404
    #
    # # get a project
    # def get(self, request, pk, format=None):
    #     project = self.get_project(pk)
    #     serializer = ProjectSerializer(project)
    #     return Response(serializer.data)
    #
    # # update a project
    # def put(self, request, pk, format=None):
    #     project = self.get_project(pk)
    #     serializer = ProjectSerializer(project, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #
    # # delete a project
    # def delete(self, request, pk, format=None):
    #     project = self.get_project(pk)
    #     project.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class ReleaseList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer

    @swagger_auto_schema(
        operation_summary='返回Release列表'
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='新建一个Release'
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ReleaseDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer

    @swagger_auto_schema(
        operation_summary='检索一个Release'
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='更新一个Release'
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='删除一个Release'
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class ObjectList(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 generics.GenericAPIView):
    queryset = Object.objects.all()
    serializer_class = ObjectSerializer

    @swagger_auto_schema(
        operation_summary='返回Object列表'
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='新建一个Object'
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ObjectDetail(mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   generics.GenericAPIView):
    queryset = Object.objects.all()
    serializer_class = ObjectSerializer

    @swagger_auto_schema(
        operation_summary='检索一个Object'
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='更新一个Object'
    )
    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='删除一个Object'
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
