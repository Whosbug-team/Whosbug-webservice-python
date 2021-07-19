# -*- coding: utf-8 -*-
from diffs.models import Object


class Method:

    def __init__(self, obj: Object):
        self.name = obj.name
        self.file_path = obj.file_path
        self.owner = obj.owner
        self.commit_time = obj.commit_time
        self.hash = obj.hash
        self.parent_name = obj.parent_name
        self.parent_hash = obj.parent_hash
        self.weight = 1

    def normalization_commit_time_weight(self, max_commit_time, min_commit_time) -> None:
        if max_commit_time == min_commit_time:
            return
        length = max_commit_time - min_commit_time
        self.weight = (self.commit_time - min_commit_time).total_seconds() / length.total_seconds()


class BugOwner:
    """
    to store methods information each bug owner have
    """

    def __init__(self, name):
        self.name = name
        self.confidence = 0
        self.methods = []
        self.method_confidence = []

    def add_method(self, method: Method):
        self.methods.append(method)
        self.method_confidence.append(method.weight)
        self.confidence += method.weight

    def analysis(self, tot_weight: float) -> dict:
        result = {
            'owner': self.name,
            'confidence': self.confidence / tot_weight,
            'methods': None,
            'src': None,
        }
        methods = []
        src = []
        for method in self.methods:
            methods.append(method.name)
            src.append(method.file_path)
        result['methods'] = methods
        result['src'] = src
        return result


