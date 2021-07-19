# -*- coding: utf-8 -*-
from django.db import models
from django.core.validators import MinValueValidator
from diffs.models import Project


class Reviewer(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Reviewer Belongs to the Project")
    file_path = models.CharField(max_length=200)
    reviewer = models.CharField(max_length=100, verbose_name="review the file")
    review_rule = models.IntegerField(validators=[MinValueValidator(-1)])

    def __str__(self):
        return f"{self.id}: {self.reviewer}-{self.file_path}"


class Rule(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="White Rule of The Project")
    file = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.id}-{self.project.id}: {self.file}"
