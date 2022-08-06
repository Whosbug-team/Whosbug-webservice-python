# -*- coding: utf-8 -*-
import logging
import logging.config
from rest_framework.decorators import api_view
from rest_framework import status
from diffs.models import Project
from diffs.models import Release
from diffs.models import Object, Commit
from diffs.models import *
from diffs.serializers import ReleaseSerializer
from django.db.models import Max
from rest_framework.response import Response
from diffs.utils import generate_object_dict
from django.db import transaction, IntegrityError

import math
from diffs.serializers import ReleaseSerializer
import numpy as np
import tqdm
from django.http.response import JsonResponse

logging.config.fileConfig(fname="logger.ini", disable_existing_loggers=False)
logger = logging.getLogger(__name__)


@api_view(["POST"])
def create_project_and_release(request):
    """
    进入分析前，上传project&release信息
    传入的信息格式为:
    {
        "project": { "pid": "123" },
        "release": {
            "release": "5.0",
            "commit_hash": "IGTmZ+aSzNUTkGtZwplohhxw1qDrJn8i1LNIuulc685xG+wjuIZhhD4="
        }
    }
    """
    project = request.data["project"]
    release = request.data["release"]
    save_id = transaction.savepoint()

    project_model, created = Project.objects.get_or_create(pid=project["pid"])
    project_model.save()
    release_model, created = Release.objects.get_or_create(
        project=project_model, version=release["version"])
    if (created == False
            and release_model.last_commit_hash == release["last_commit_hash"]):
        return Response(
            "The Project and Release already exist, update the commit" +
            str(project) + str(release),
            status=404,
        )
    release_model.last_commit_hash = release["last_commit_hash"]
    release_model.save()
    return Response(status=status.HTTP_201_CREATED)


@api_view(["POST"])
def upload_commits_info(request):
    """
    上传所有的commits信息列表，格式如下：
    {
        "project": { "pid": "123" },
        "release": {
            "version": "5.0",
            "last_commit_hash": "IGTmZ+aSzNUTkGtZwplohhxw1qDrJn8i1LNIuulc685xG+wjuIZhhD4="
        },
        "commits": [
            {
            "hash": "IGTmZ+aSzNUTkGtZwplohhxw1qDrJn8i1LNIuulc685xG+wjuIZhhA==",
            "email": "eGfya7/OyJkBzmh60M1g3G5UoLjouSM=",
            "author": "kevinmatthe",
            "time": "2021-10-14T20:43:08+08:00"
            },
            {
            "hash": "KjS9OrWVyNwUlzlekcs/2vPCOsnsyA0sEswxMRmRaaON4blyMHEe7Q==",
            "email": "eGfya7/OyJkBzmh60M1g3G5UoLjouSM=",
            "author": "kevinmatthe",
            "time": "2021-10-14T17:20:18+08:00"
            },
            {
            "hash": "dzqwMOPAm9oQkzwNkJ8/ieAKOcyXSlPHT8SgxVhc1Aj+9BAqsg37kQ==",
            "email": "eGfya7/OyJkBzmh60M1g3G5UoLjouSM=",
            "author": "kevinmatthe",
            "time": "2021-10-14T17:16:05+08:00"
            }
        ]
    }
    """
    project = request.data["project"]
    release = request.data["release"]
    commits = request.data["commits"]

    try:
        project = Project.objects.get(pid=project["pid"])
    except Project.DoesNotExist:
        return Response("The Project Not Found: " +
                        str(request.data["project"]),
                        status=404)
    except:
        logging.exception("Project fails")
    try:
        release = Release.objects.get(
            project=project,
            version=release["version"],
            last_commit_hash=release["last_commit_hash"],
        )
    except Release.DoesNotExist:
        return Response("The Release Not Found: " +
                        str(request.data["release"]),
                        status=404)
    except:
        logging.info("Release fails")
    save_id = transaction.savepoint()
    ret = Response()
    try:
        for commit in commits:
            commit_model = Commit(
                release=release,
                hash=commit["hash"],
                time=commit["time"],
                author=commit["author"],
                email=commit["email"],
            )
            try:
                commit_model.save()
            except IntegrityError:
                logging.exception("Commmit error:")
                ret = Response(f"commit:{commit_model} integrity error",
                               status=404)
            except:
                logging.exception("commit insert error")
                ret = Response(f"commit:{commit} error", status=404)
                raise IntegrityError
    except:
        logging.exception("")
        transaction.savepoint_rollback(save_id)
        return ret

    return Response(status=status.HTTP_201_CREATED)


@api_view(["POST"])
def commit_diffs(request):
    """
    上传Object
    {
        "project": {
            "pid": "test"
        },
        "release": {
            "version": "5.0.0",
            "last_commit_hash": "5f424ce931a75ec032573cd85750745286383c4d"
        },
        "objects": [
            {
                "hash": "27c5237b06b3736076d58b7f7a86c28c6772a9a8",
                "object_id": "BankersAlgorithm.calculateNeed",
                "old_object_id": "",
                "path": "Others/BankersAlgorithm.java",
                "start_line": 36,
                "end_line": 43,
                "old_line_count": 1,
                "current_line_count": 8,
                "removed_line_count": 0,
                "added_new_line_count": 7
            }
        ]
    }
    """
    project = request.data["project"]
    release = request.data["release"]
    objects = request.data["objects"]
    # 匹配project&release
    try:
        project = Project.objects.get(pid=project["pid"])
    except:
        logging.exception("Finding Project Error")
        return Response("Cannot find the project" + str(project))
    try:
        release = Release.objects.get(
            project=project,
            version=release["version"],
            last_commit_hash=release["last_commit_hash"],
        )
    except:
        logging.exception("Finding Release Error")
        return Response("Cannot find the release" + str(release))
    ret = Response("The object Formatter is invalid.", status=404)
    save_point = transaction.savepoint()
    # 准备插入待计算表
    try:
        for obj_change in objects:
            # 获取commit信息
            try:
                commit = Commit.objects.get(release__project=project,
                                            hash=obj_change["hash"])
            except:
                logging.exception("Invalid commit info." + str(commit))
                continue
            object_change_model = UnCalculateObjectChange(
                commit=commit,
                old_object_id=obj_change["old_object_id"],
                object_id=obj_change["object_id"],
                path=obj_change["path"],
                old_line_count=obj_change["old_line_count"],
                current_line_count=obj_change["current_line_count"],
                deleted_line_count=obj_change["removed_line_count"],
                added_line_count=obj_change["added_new_line_count"],
                hash=obj_change["hash"],
                parameters=obj_change["parameters"],
                start_line=obj_change["start_line"],
                end_line=obj_change["end_line"],
                release=release,
            )
            try:
                object_change_model.save()
            except BaseException as e:
                # 异常处理，可能存在异常
                logging.warning(e)
                continue
    except:
        transaction.savepoint_rollback(save_point)
        logging.exception("test")
        return ret
    return Response(status=status.HTTP_200_OK)


obj_loop_time = 0
get_or_create_time = 0


# TODO:完善训练数据集的方法
@api_view(["POST"])
def train_method(request):
    global obj_loop_time
    global get_or_create_time
    obj_loop_time = 0
    get_or_create_time = 0
    my_res = {}
    project = request.data['project']
    # project = {"pid": "test"}
    release = request.data['release']
    # release = {
    #     "version": "5.0.0",
    #     "last_commit_hash": "d127a361b0d88ece194b9d1398bc4e03318f4f16",
    # }
    try:
        project = Project.objects.get(pid=project["pid"])
    except:
        logging.exception("Finding Project Error")
        return Response("Cannot find the project" + str(project))
    try:
        release = Release.objects.get(
            project=project,
            version=release["version"],
            last_commit_hash=release["last_commit_hash"],
        )
    except:
        logging.exception("Finding Release Error")
        return Response("Cannot find the release" + str(release))

    uncalculate_objects = UnCalculateObjectChange.objects.filter(
        release=release).order_by("-commit_id")
    print(uncalculate_objects.count())
    for i in tqdm.tqdm(np.arange(0, 1, 0.1), desc="Calculating"):
        Training_array = []
        calculate(release, uncalculate_objects, cc=i)
        objects = Object.objects.all()
        for object_item in objects:
            Training_array.append(object_item.confidence)
        Object.objects.all().delete()
        my_res[i] = np.std(Training_array)
        print(
            "\nloop_total_time",
            obj_loop_time,
            "get_or_create",
            get_or_create_time,
        )
    # calculate(project, uncalculate_objects, cc=0.5)
    return JsonResponse(my_res,
                        safe=False,
                        json_dumps_params={"ensure_ascii": False})


def calculate(release, objects, cc=0.5, ip=1):
    # 变动常数
    CHANGE_CONST = cc
    # 初始化常数变量
    INIT_PARAM = ip

    def update_owners(commit: Commit, obj_change: UnCalculateObjectChange,
                      obj_from_table: Object) -> Object:
        if commit.author in obj_from_table.owner_info:
            obj_from_table.owner_info[commit.author] = generate_owner_info(
                commit, obj_change,
                obj_from_table.owner_info[commit.author]['weight'])
        else:
            obj_from_table.owner_info.update(
                {commit.author: generate_owner_info(commit, obj_change, 0)})
        return obj_from_table

    def generate_owner_info(commit: Commit,
                            obj_change: UnCalculateObjectChange,
                            old_weight: float) -> dict:
        if obj_change.added_line_count > obj_change.deleted_line_count:
            weight = obj_change.added_line_count / obj_change.current_line_count
        else:
            weight = obj_change.deleted_line_count / obj_change.old_line_count
        weight = max(weight, old_weight)
        return {
            "email": commit.email,
            "time": commit.time,
            "weight": round(weight, 2)
        }

    def get_confidence(old_lines, added_lines, deleted_lines, old_confidence,
                       last_modify):
        """
        依据行数变更和旧的置信度来计算新的置信度
        """
        remain_lines = old_lines - deleted_lines
        if remain_lines < 0:
            remain_lines = 0
        new_lines = added_lines
        inner_value = (remain_lines * old_confidence + new_lines * math.pow(
            CHANGE_CONST, new_lines) * INIT_PARAM) / old_lines
        new_confidence = math.pow(1 - math.pow(5, -inner_value), last_modify)
        return new_confidence

    def object_get_or_create(object_id, path, parameters):
        """
        判断是否已经存在该Object
        """
        isexists = True
        object_from_table = Object.objects.filter(path=path,
                                                  object_id=object_id,
                                                  parameters=parameters)
        if object_from_table.exists() == False:
            isexists = False
            return (
                Object(path=path, object_id=object_id, parameters=parameters),
                isexists,
            )
        return object_from_table[0], isexists

    for obj_change in objects:
        try:
            commit = Commit.objects.get(release=release, hash=obj_change.hash)
        except:
            logging.exception("invalid commit info:")
            continue
        try:

            object_from_table, isexists = object_get_or_create(
                obj_change.object_id, obj_change.path, obj_change.parameters)
            if not isexists:

                object_from_table.confidence = round(
                    get_confidence(obj_change.old_line_count,
                                   obj_change.current_line_count, 0, 0, 1), 4)
                object_from_table.commit = commit
            else:
                # ? 已存在的object，更新置信度
                object_from_table.old_confidence = object_from_table.confidence
                object_from_table.confidence = round(
                    get_confidence(obj_change.old_line_count,
                                   obj_change.added_line_count,
                                   obj_change.deleted_line_count,
                                   object_from_table.old_confidence, 1), 4)
                object_from_table.commit = commit

            object_from_table = update_owners(commit, obj_change,
                                              object_from_table)

            object_from_table.start_line = obj_change.start_line
            object_from_table.end_line = obj_change.end_line
            object_from_table.save()
        except BaseException as e:
            print(commit)
            logging.exception(e)
            continue


@api_view(["POST"])
def upload_done(request):

    global confidence_params  # !置信度的计算参数å
    project = request.data["project"]
    release = request.data["release"]
    try:
        project = Project.objects.get(pid=project["pid"])
    except:
        logging.exception("Finding Project Error")
        return Response("Cannot find the project" + str(project))
    try:
        release = Release.objects.get(
            project=project,
            version=release["version"],
            last_commit_hash=release["last_commit_hash"],
        )
    except:
        logging.exception("Finding Release Error")
        return Response("Cannot find the release" + str(release))

    objects = UnCalculateObjectChange.objects.filter(
        release=release).order_by("-commit_id")
    calculate(release, objects)
    return Response(status=201)


@api_view(["POST"])
def get_last_release(request):
    """
    获取最新的release信息，传入的信息格式为：
    {
        "pid": "test"
    }
    """
    try:
        project = Project.objects.get(pid=request.data["pid"])
    except Project.DoesNotExist:
        return Response(
            f"The project with pid {request.data['pid']} does not exists.",
            status=status.HTTP_404_NOT_FOUND,
        )
    releases = Release.objects.filter(project=project)
    try:
        latest_release = Release.objects.get(
            pk=releases.aggregate(Max("id"))["id__max"])
    except Release.DoesNotExist:
        return Response("The project has no Release Now.", status)
    serializer = ReleaseSerializer(latest_release)
    return Response(serializer.data)


@api_view(["POST"])
def delete_all_related_data(request):
    project = request.data['project']['pid']
    release = request.data['release']['version']
    try:
        project = Project.objects.get(pid=request.data['project']['pid'])
    except:
        logging.exception("Project get fails")
        return Response("no such project:" + request.data['project']['pid'],
                        status=400)

    try:
        release = Release.objects.get(
            version=request.data['release']['version'], project=project)
    except:
        logging.exception("Release get fails")
        return Response("no such release:" +
                        request.data['release']['version'],
                        status=400)

    try:
        Object.objects.filter(commit__release=release).delete()
        # Object.objects.all().delete()
        UnCalculateObjectChange.objects.filter(
            commit__release=release).delete()
        Commit.objects.filter(release=release).delete()
        Release.objects.filter(version=request.data['release']['version'],
                               project=project).delete()
        # Project.objects.all().delete()
    except:
        logging.exception("Delete all stuff error")

    return Response("Success", status=200)


@api_view(["POST"])
def delete_uncalculate(request):
    project = request.data['project']['pid']
    release = request.data['release']['version']

    try:
        project = Project.objects.get(pid=request.data['project']['pid'])
    except:
        logging.exception("Project get fails")
        return Response("no such project:" + request.data['project']['pid'],
                        status=400)
    try:
        release = Release.objects.get(
            version=request.data['release']['version'], project=project)
    except:
        logging.exception("Release get fails")
        return Response("no such release:" +
                        request.data['release']['version'],
                        status=400)
    try:
        UnCalculateObjectChange.objects.filter(
            commit__release=release).delete()
    except BaseException as e:
        logging.exception("Delete error")
        return Response(e, status=500)
    return Response("Success", status=200)


@api_view(['GET'])
def liveness_probe(request):
    """
    secure the liveness of the webservice
    """
    return Response('Webservice Working...', status=200)


@api_view(['POST'])
def get_confidence_and_infos(request):
    '''
    {
        "project": {
            "pid": "test1"
        },
        "release": {
            "version": "5.0.0"
        },
        "methods": [
            {
            "method_id": "HeapSort.swap",
            "filepath": "HeapSort.java",
            "parameters": "int first, int second"
            }
        ]
    }
    '''
    project = request.data["project"]
    release = request.data["release"]
    report_methods = request.data['methods']
    # 首先寻找project是否存在
    try:
        project = Project.objects.get(pid=project['pid'])
    except:
        logging.exception(f"Project {project} not exists")
        return Response(f"Project {project} not exists")

    # 寻找release是否存在
    try:
        release = Release.objects.get(project=project,
                                      version=release['version'])
    except:
        logging.exception(f"Release {release} not exists")
        return Response(f"Release {release} not exists")

    response = {"status": "ok", "message": "", "objects": {}}
    for report_method in report_methods:
        # 基于object-id做筛选
        methods_id = Object.objects.filter(
            commit__release=release, object_id=report_method['method_id'])
        if len(methods_id) == 0:
            logging.exception("Get objects error:")
            response['message'] = f"No such objects in release:{release}"
            response['status'] = "may be ok"
            continue

        # 在前置基础上依据path做筛选
        methods_path = methods_id.filter(path=report_method['filepath'])
        if len(methods_path) == 0:
            logging.exception("Get objects error:")
            response['message'] = f"No such objects in path:{report_method['filepath']}, here's results with id"
            for method in methods_id:
                commit = Commit.objects.get(id=method.commit_id)
                response["objects"][report_method['method_id']] = []
                response["objects"][report_method['method_id']].append(
                    generate_object_dict(method, commit))
            response['status'] = "may be ok"
            continue

        # 在此基础上依据params做筛选
        methods_params = methods_path.filter(
            parameters=report_method['parameters'])
        if len(methods_params) == 0:
            logging.exception("Get objects error:")
            response[
                'message'] = f"No such objects in params: {report_method['parameters']}, here's results with path"
            for method in methods_path:
                commit = Commit.objects.get(id=method.commit_id)
                response["objects"][report_method['method_id']] = []
                response["objects"][report_method['method_id']].append(
                    generate_object_dict(method, commit))
            response['status'] = "may be ok"
            continue

    return JsonResponse(response)


def get_encrypted_text(request):
    import requests
    url = "http://golang-web:8080/decrypto"
    r = requests.post(url,
                      data={
                          "pid": request.data['pid'],
                          "key": request.data['key'],
                          "text": request.data['text']
                      })
    return r.content


def get_decrypted_text(request):
    import requests
    url = "http://golang-web:8080/encrypto"
    r = requests.post(url,
                      data={
                          "pid": request.data['pid'],
                          "key": request.data['key'],
                          "text": request.data['text']
                      })
    return r.content