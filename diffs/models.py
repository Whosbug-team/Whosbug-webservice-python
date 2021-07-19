# -*- coding: utf-8 -*-
from django.db import models


class Project(models.Model):
    pid = models.CharField(max_length=200, verbose_name="Project ID String", unique=True)

    def __str__(self):
        return f"{self.id}: {self.pid}"


class Release(models.Model):
    release = models.CharField(max_length=50, verbose_name="Product Release", default="")
    commit_hash = models.CharField(max_length=100, verbose_name="Product Commit Hash")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Product Belongs to Project")

    def __str__(self):
        return f"{self.id}: {self.project.pid}-{self.release}"


class Object(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Object Belongs to the Project")
    release = models.ForeignKey(Release, on_delete=models.CASCADE, verbose_name="Object Belongs to the Product")

    name = models.CharField(max_length=100, verbose_name="Object Name")
    file_path = models.CharField(max_length=200)
    owner = models.CharField(max_length=100, verbose_name="Object Belongs to Owner")
    commit_time = models.DateTimeField('commit time')

    hash = models.CharField(max_length=100)
    parent_name = models.CharField(max_length=100, blank=True, null=True)  # parent_node is class or null
    parent_hash = models.CharField(max_length=100, blank=True, null=True)
    old_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.id}: {self.project.pid}-{self.name}"
