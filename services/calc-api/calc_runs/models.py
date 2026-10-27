import uuid

from django.conf import settings
from django.db import models


class CalcRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        on_delete=models.CASCADE,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    module = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    standard = models.CharField(max_length=100)
    verified = models.BooleanField()
    params = models.JSONField(default=dict)
    payload = models.JSONField(default=dict)
    summary = models.JSONField(default=dict)

    def metadata(self) -> dict:
        summary = self.summary or {}
        return {
            "run_id": str(self.id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "module": self.module,
            "title": self.title,
            "standard": self.standard,
            "verified": self.verified,
            "summary": summary,
            "total": summary.get("total"),
            "failed": summary.get("failed"),
            "control_failed": summary.get("control_failed"),
        }

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"


class ScaffoldProject(models.Model):
    REGION_CHOICES = (
        ("全国", "全国"),
        ("上海", "上海"),
        ("江苏", "江苏"),
        ("浙江", "浙江"),
        ("北京", "北京"),
        ("山东", "山东"),
        ("广东", "广东"),
        ("湖北", "湖北"),
        ("福建", "福建"),
        ("重庆", "重庆"),
    )
    STATUS_CHOICES = (
        ("preparing", "筹备中"),
        ("calculating", "计算中"),
        ("completed", "已完成"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        on_delete=models.CASCADE,
        db_index=True,
    )
    name = models.CharField(max_length=200)
    region = models.CharField(max_length=20, choices=REGION_CHOICES, default="全国")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="preparing")
    code = models.CharField(max_length=100, blank=True, default="")
    client = models.CharField(max_length=200, blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    designer = models.CharField(max_length=100, blank=True, default="")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def metadata(self, *, schemes: list[dict] | None = None) -> dict:
        data = {
            "id": str(self.id),
            "project_id": str(self.id),
            "name": self.name,
            "region": self.region,
            "status": self.status,
            "status_label": self.get_status_display(),
            "code": self.code,
            "client": self.client,
            "location": self.location,
            "designer": self.designer,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if schemes is not None:
            data["scheme_count"] = len(schemes)
            data["schemes"] = schemes
            runs = [
                scheme["last_run"]
                for scheme in schemes
                if scheme.get("last_run")
            ]
            last_run = max(
                runs,
                key=lambda item: item["created_at"],
                default=None,
            )
            data["last_calculated_at"] = (
                last_run["created_at"] if last_run else None
            )
            data["failed_control_count"] = sum(
                int(
                    (scheme.get("last_run") or {})
                    .get("summary", {})
                    .get("control_failed")
                    or 0
                )
                for scheme in schemes
            )
        return data

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"


class ScaffoldScheme(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ScaffoldProject,
        related_name="schemes",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=200)
    module = models.CharField(max_length=100)
    module_title = models.CharField(max_length=200)
    params = models.JSONField(default=dict)
    last_run = models.ForeignKey(
        CalcRun,
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def metadata(self) -> dict:
        return {
            "id": str(self.id),
            "scheme_id": str(self.id),
            "project_id": str(self.project_id),
            "name": self.name,
            "module": self.module,
            "module_title": self.module_title,
            "params": self.params or {},
            "last_run_id": str(self.last_run_id) if self.last_run_id else None,
            "last_run": self.last_run.metadata() if self.last_run_id and self.last_run else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"
