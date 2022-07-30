# -*- coding: utf-8 -*-
from django.http import JsonResponse
from diffs.bug_owner import Method
from diffs.bug_owner import BugOwner
from diffs.models import Object

def get_matched_methods(all_objects, methods: list, file_paths: list):
    # match name and file_path
    all_matched_methods = []
    all_matched_methods_hash = []
    for method, file_path in zip(methods, file_paths):
        matched_methods = all_objects.filter(name__contains=method, file_path__contains=file_path)
        if len(matched_methods) == 0:
            continue
        for m in matched_methods:
            all_matched_methods.append(Method(m))
            all_matched_methods_hash.append(m.hash)
    return all_matched_methods, all_matched_methods_hash


def get_reviewers(methods: Method, review_objects, reviewer_cnt: dict):
    # get reviewers of all matched methods
    for method in methods:
        reviewers = review_objects.filter(file_path__contains=method.file_path)
        for reviewer in reviewers:
            cnt = reviewer_cnt.get(reviewer.reviewer, 0)
            cnt += 1
            reviewer_cnt[reviewer.reviewer] = cnt
    return reviewer_cnt


def calculate_method_weight(matched_methods, mode=None, connection_weights=None):
    # 归一化commit_time
    max_commit_time = max(matched_methods, key=lambda k: k.commit_time).commit_time
    min_commit_time = min(matched_methods, key=lambda k: k.commit_time).commit_time

    bug_owners = {}
    to_parent_weights = {}
    stack_weights = 0
    # calculate method weight (normalized commit_time)
    for method in matched_methods:
        method.normalization_commit_time_weight(max_commit_time, min_commit_time)
        if mode == "exact":
            weights = to_parent_weights.get(method.parent_hash, 0) + method.weight
            to_parent_weights[method.parent_hash] = weights
        elif mode == "fuzzy":
            # if the method has a parent class, more pure feature.
            if method.parent_hash in to_parent_weights:
                method.weight = method.weight * 0.4 + connection_weights[method.parent_hash] * 0.6
            # if the method is a parent class that its subclass is modified
            elif method.hash in to_parent_weights:
                method.weight = method.weight * 0.4 + connection_weights[method.hash] * 0.4
        bug_owner = bug_owners.get(method.name, BugOwner(method.owner))
        bug_owner.add_method(method)
        bug_owners[method.owner] = bug_owner
        stack_weights += method.weight
    return bug_owners, stack_weights, to_parent_weights


def analysis_stack(bug_owners: dict, weights: int, owner_confidence: dict, mode="exact", exact_bug_owners=None):
    # analysis one stack totally
    analysis = []
    for (name, bug_owner) in zip(bug_owners.keys(), bug_owners.values()):
        result = bug_owner.analysis(weights)
        confidence = owner_confidence.get(name, 0)
        if mode == "fuzzy":
            result['confidence'] *= 0.7
            if name in exact_bug_owners:
                result['confidence'] += exact_bug_owners[name].confidence * 0.3
        confidence += result['confidence']
        owner_confidence[name] = confidence
        analysis.append(result)
    analysis.sort(key=lambda k: k['confidence'], reverse=True)
    return analysis, owner_confidence


def analysis_total(reviewer_cnt: dict, owner_confidence: dict):
    # analysis stacks totally
    # code reviewers
    reviewers = []
    sorted(reviewer_cnt.items(), key=lambda item: item[1], reverse=True)
    for (reviewer, cnt) in reviewer_cnt.items():
        result = {
            'reviewer': reviewer,
            'count': cnt,
        }
        reviewers.append(result)

    # bug_owners
    analysis = []
    sum_confidences = sum(owner_confidence.values())
    sorted(owner_confidence.items(), key=lambda item: item[1], reverse=True)
    for (owner, confidence) in owner_confidence.items():
        result = {
            'developer': owner,
            'confidence': confidence / sum_confidences if sum_confidences != 0 else 0,
        }
        analysis.append(result)
    return reviewers, analysis


def generate_object_dict(jsonres, method: Object, commit) -> dict:
    return {
        "method_id": method.object_id,
        "path": method.path,
        "parameters": method.parameters,
        "method_owner": {
            "author": commit.author,
            "email": commit.email,
            "time": commit.time,
            "confidence": method.confidence
        },
        "owner_list": method.owner_info
    }


