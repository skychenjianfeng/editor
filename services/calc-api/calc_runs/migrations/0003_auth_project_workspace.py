from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


LEGACY_USERNAME = "legacy-data@internal.invalid"


def _legacy_user(apps):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    user, _ = User.objects.get_or_create(
        username=LEGACY_USERNAME,
        defaults={"email": LEGACY_USERNAME},
    )
    User.objects.filter(pk=user.pk).update(
        email=LEGACY_USERNAME,
        password="!",
        is_active=False,
        is_staff=False,
        is_superuser=False,
    )
    return user


def ensure_legacy_user(apps, schema_editor):
    _legacy_user(apps)


def assign_legacy_owner(apps, schema_editor):
    legacy_user = _legacy_user(apps)
    CalcRun = apps.get_model("calc_runs", "CalcRun")
    ScaffoldProject = apps.get_model("calc_runs", "ScaffoldProject")
    CalcRun.objects.filter(owner__isnull=True).update(owner=legacy_user)
    ScaffoldProject.objects.filter(owner__isnull=True).update(owner=legacy_user)


def release_legacy_owner(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    legacy_user = User.objects.filter(username=LEGACY_USERNAME).first()
    if legacy_user is None:
        return
    CalcRun = apps.get_model("calc_runs", "CalcRun")
    ScaffoldProject = apps.get_model("calc_runs", "ScaffoldProject")
    CalcRun.objects.filter(owner=legacy_user).update(owner=None)
    ScaffoldProject.objects.filter(owner=legacy_user).update(owner=None)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("calc_runs", "0002_scaffoldproject_scaffoldscheme"),
    ]

    operations = [
        migrations.RunPython(ensure_legacy_user, migrations.RunPython.noop),
        migrations.AddField(
            model_name="calcrun",
            name="owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="scaffoldproject",
            name="owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="scaffoldproject",
            name="region",
            field=models.CharField(
                choices=[
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
                ],
                default="全国",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="scaffoldproject",
            name="status",
            field=models.CharField(
                choices=[
                    ("preparing", "筹备中"),
                    ("calculating", "计算中"),
                    ("completed", "已完成"),
                ],
                default="preparing",
                max_length=20,
            ),
        ),
        migrations.RunPython(assign_legacy_owner, release_legacy_owner),
        migrations.AlterField(
            model_name="calcrun",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                db_index=True,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="scaffoldproject",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                db_index=True,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
