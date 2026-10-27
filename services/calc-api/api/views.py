import csv
import io

from django.http import HttpResponse
from django.db.models import Prefetch, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from calc_runs.models import CalcRun, ScaffoldProject, ScaffoldScheme
from calc_runs.serializers import (
    InputValidationError,
    validate_project_payload,
    validate_scheme_payload,
)
from calc_core import scaffold_fastener
from calc_core.batch import batch_csv, run_batch
from calc_core.drawing import build_geometry_for_module, export_dxf, export_png
from calc_core.modules import SCAFFOLD_FASTENER  # noqa: F401  (registers modules)
from calc_core import registry


def _json_body(request):
    content_type = (request.content_type or "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        return None, Response(
            {"detail": "request body must be JSON"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        data = request.data
    except Exception:
        return None, Response(
            {"detail": "request body must be valid JSON"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not isinstance(data, dict):
        return None, Response(
            {"detail": "JSON body must be an object"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return data, None


def _parse_limit(raw_limit) -> int:
    try:
        return int(raw_limit)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(
            "limit must be an integer between 1 and 200"
        ) from exc


def _project_detail_response(project: ScaffoldProject) -> Response:
    schemes = [scheme.metadata() for scheme in project.schemes.all()]
    return Response(project.metadata(schemes=schemes))


def _validation_error_response(exc: InputValidationError) -> Response:
    payload = {"detail": str(exc)}
    if exc.field:
        payload["errors"] = {exc.field: [str(exc)]}
    return Response(payload, status=status.HTTP_400_BAD_REQUEST)


def _last_run_for_module(last_run_id, module_key: str, owner):
    if last_run_id is None:
        return None, None
    try:
        record = CalcRun.objects.get(id=last_run_id, owner=owner)
    except CalcRun.DoesNotExist:
        return None, Response(
            {"detail": "run not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    if record.module != module_key:
        return None, Response(
            {"detail": "last_run module must match scheme module"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return record, None


class ProjectListView(APIView):
    def get(self, request):
        try:
            limit = _parse_limit(request.query_params.get("limit", 50))
        except InputValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not 1 <= limit <= 200:
            return Response(
                {"detail": "limit must be an integer between 1 and 200"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = ScaffoldProject.objects.filter(owner=request.user).order_by(
            "-updated_at",
            "-created_at",
        )
        search = (request.query_params.get("search") or "").strip()
        if search:
            records = records.filter(
                Q(name__icontains=search)
                | Q(region__icontains=search)
                | Q(code__icontains=search)
                | Q(client__icontains=search)
                | Q(location__icontains=search)
                | Q(designer__icontains=search)
                | Q(note__icontains=search)
            )
        status_value = (request.query_params.get("status") or "").strip()
        if status_value:
            allowed_statuses = {
                choice[0] for choice in ScaffoldProject.STATUS_CHOICES
            }
            if status_value not in allowed_statuses:
                return _validation_error_response(
                    InputValidationError(
                        "status must be one of: "
                        + ", ".join(sorted(allowed_statuses)),
                        field="status",
                    )
                )
            records = records.filter(status=status_value)
        records = records.prefetch_related(
            Prefetch(
                "schemes",
                queryset=ScaffoldScheme.objects.select_related(
                    "last_run"
                ).order_by("-updated_at", "-created_at"),
            )
        )
        projects = [
            record.metadata(
                schemes=[scheme.metadata() for scheme in record.schemes.all()]
            )
            for record in records[:limit]
        ]
        return Response({"projects": projects})

    def post(self, request):
        data, error = _json_body(request)
        if error:
            return error
        try:
            cleaned = validate_project_payload(data)
        except InputValidationError as exc:
            return _validation_error_response(exc)
        record = ScaffoldProject.objects.create(owner=request.user, **cleaned)
        return Response(
            record.metadata(schemes=[]),
            status=status.HTTP_201_CREATED,
        )


class ProjectDetailView(APIView):
    def get(self, request, project_id):
        try:
            record = ScaffoldProject.objects.prefetch_related(
                Prefetch(
                    "schemes",
                    queryset=ScaffoldScheme.objects.select_related(
                        "last_run"
                    ).order_by("-updated_at", "-created_at"),
                )
            ).get(id=project_id, owner=request.user)
        except ScaffoldProject.DoesNotExist:
            return Response(
                {"detail": "project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return _project_detail_response(record)

    def patch(self, request, project_id):
        try:
            record = ScaffoldProject.objects.get(
                id=project_id,
                owner=request.user,
            )
        except ScaffoldProject.DoesNotExist:
            return Response(
                {"detail": "project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        data, error = _json_body(request)
        if error:
            return error
        try:
            cleaned = validate_project_payload(data, partial=True)
        except InputValidationError as exc:
            return _validation_error_response(exc)
        for field, value in cleaned.items():
            setattr(record, field, value)
        record.save()
        return _project_detail_response(record)

    def delete(self, request, project_id):
        try:
            record = ScaffoldProject.objects.get(
                id=project_id,
                owner=request.user,
            )
        except ScaffoldProject.DoesNotExist:
            return Response(
                {"detail": "project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectSchemeListView(APIView):
    def get(self, request, project_id):
        try:
            project = ScaffoldProject.objects.get(
                id=project_id,
                owner=request.user,
            )
        except ScaffoldProject.DoesNotExist:
            return Response(
                {"detail": "project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        schemes = project.schemes.select_related("last_run").all()
        return Response({"schemes": [scheme.metadata() for scheme in schemes]})

    def post(self, request, project_id):
        try:
            project = ScaffoldProject.objects.get(
                id=project_id,
                owner=request.user,
            )
        except ScaffoldProject.DoesNotExist:
            return Response(
                {"detail": "project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        data, error = _json_body(request)
        if error:
            return error
        try:
            cleaned = validate_scheme_payload(data)
        except InputValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        defn = registry.get(cleaned["module"])
        if defn is None:
            return Response(
                {"detail": f"unknown module: {cleaned['module']}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        last_run_id = cleaned.pop("last_run_id", None)
        last_run, error = _last_run_for_module(
            last_run_id,
            defn.key,
            request.user,
        )
        if error:
            return error
        record = ScaffoldScheme.objects.create(
            project=project,
            module_title=defn.title,
            last_run=last_run,
            **cleaned,
        )
        return Response(record.metadata(), status=status.HTTP_201_CREATED)


class SchemeDetailView(APIView):
    def get(self, request, scheme_id):
        try:
            record = ScaffoldScheme.objects.select_related(
                "project",
                "last_run",
            ).get(id=scheme_id, project__owner=request.user)
        except ScaffoldScheme.DoesNotExist:
            return Response(
                {"detail": "scheme not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(record.metadata())

    def patch(self, request, scheme_id):
        try:
            record = ScaffoldScheme.objects.select_related(
                "project",
                "last_run",
            ).get(id=scheme_id, project__owner=request.user)
        except ScaffoldScheme.DoesNotExist:
            return Response(
                {"detail": "scheme not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        data, error = _json_body(request)
        if error:
            return error
        try:
            cleaned = validate_scheme_payload(data, partial=True)
        except InputValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        final_module = cleaned.get("module", record.module)
        defn = registry.get(final_module)
        if defn is None:
            return Response(
                {"detail": f"unknown module: {final_module}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "last_run_id" in cleaned:
            last_run, error = _last_run_for_module(
                cleaned.pop("last_run_id"),
                defn.key,
                request.user,
            )
            if error:
                return error
            record.last_run = last_run
        elif record.last_run_id and record.last_run.module != defn.key:
            return Response(
                {"detail": "last_run module must match scheme module"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "module" in cleaned:
            record.module = defn.key
            record.module_title = defn.title
        for field, value in cleaned.items():
            setattr(record, field, value)
        record.save()
        return Response(record.metadata())

    def delete(self, request, scheme_id):
        try:
            record = ScaffoldScheme.objects.get(
                id=scheme_id,
                project__owner=request.user,
            )
        except ScaffoldScheme.DoesNotExist:
            return Response(
                {"detail": "scheme not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ParamSpecView(APIView):
    def get(self, request, module: str):
        defn = registry.get(module)
        if defn is None:
            return Response(
                {"detail": f"unknown module: {module}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(defn.param_spec())


class RunView(APIView):
    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 50))
        except (TypeError, ValueError):
            limit = 0
        if not 1 <= limit <= 200:
            return Response(
                {"detail": "limit must be an integer between 1 and 200"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = CalcRun.objects.filter(owner=request.user).order_by(
            "-created_at"
        )
        module = request.query_params.get("module")
        if module:
            records = records.filter(module=module)
        return Response({"runs": [record.metadata() for record in records[:limit]]})

    def post(self, request):
        params = request.data.get("params") or {}
        module = request.data.get("module", scaffold_fastener.MODULE_KEY)
        defn = registry.get(module)
        if defn is None:
            return Response(
                {"detail": f"unknown module: {module}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            payload = defn.run(params)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        record = CalcRun(
            owner=request.user,
            module=defn.key,
            title=defn.title,
            standard=str(payload.get("standard") or defn.standard),
            verified=bool(payload.get("verified", defn.verified)),
            params=payload.get("params") or params,
            payload=payload,
            summary=payload.get("summary") or {},
        )
        payload["run_id"] = str(record.id)
        record.payload = payload
        record.save()
        return Response(payload)


class RunDetailView(APIView):
    def get(self, request, run_id):
        try:
            record = CalcRun.objects.get(id=run_id, owner=request.user)
        except CalcRun.DoesNotExist:
            return Response({"detail": "run not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(record.payload)


class ReportView(APIView):
    def post(self, request):
        params = request.data.get("params") or {}
        module = request.data.get("module", scaffold_fastener.MODULE_KEY)
        defn = registry.get(module)
        if defn is None:
            return Response({"detail": f"unknown module: {module}"}, status=status.HTTP_404_NOT_FOUND)
        try:
            payload = defn.run(params)
            meta = request.data.get("meta") or {}
            meta["moduleKey"] = defn.key
            meta.setdefault("moduleTitle", defn.title)
            meta.setdefault("documentTitle", f"{defn.title}计算书")
            content = defn.report(params, payload, meta)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = 'attachment; filename="scaffold-report.docx"'
        return response


class GeometryView(APIView):
    def post(self, request):
        params = request.data.get("params") or {}
        view = request.data.get("view", "elevation")
        module = request.data.get("module", scaffold_fastener.MODULE_KEY)
        defn = registry.get(module)
        if defn is None:
            return Response({"detail": f"unknown module: {module}"}, status=status.HTTP_404_NOT_FOUND)
        return Response(build_geometry_for_module(module, defn.title, params, view))


class DxfExportView(APIView):
    def post(self, request):
        params = request.data.get("params") or {}
        view = request.data.get("view", "elevation")
        module = request.data.get("module", scaffold_fastener.MODULE_KEY)
        defn = registry.get(module)
        if defn is None:
            return Response({"detail": f"unknown module: {module}"}, status=status.HTTP_404_NOT_FOUND)
        return HttpResponse(
            export_dxf(
                params,
                view,
                module_key=module,
                module_title=defn.title,
            ),
            content_type="application/dxf",
            headers={"Content-Disposition": f'attachment; filename="{module}.dxf"'},
        )


class PngExportView(APIView):
    def post(self, request):
        params = request.data.get("params") or {}
        view = request.data.get("view", "elevation")
        module = request.data.get("module", scaffold_fastener.MODULE_KEY)
        defn = registry.get(module)
        if defn is None:
            return Response({"detail": f"unknown module: {module}"}, status=status.HTTP_404_NOT_FOUND)
        return HttpResponse(
            export_png(
                params,
                view,
                module_key=module,
                module_title=defn.title,
            ),
            content_type="image/png",
            headers={"Content-Disposition": f'attachment; filename="{module}.png"'},
        )


class BatchView(APIView):
    def post(self, request):
        cases = request.data.get("cases") or []
        module = request.data.get("module", scaffold_fastener.MODULE_KEY)
        defn = registry.get(module)
        if defn is None:
            return Response({"detail": f"unknown module: {module}"}, status=status.HTTP_404_NOT_FOUND)
        try:
            return Response(run_batch(cases, defn.run))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class BatchCsvView(APIView):
    def post(self, request):
        cases = request.data.get("cases") or []
        module = request.data.get("module", scaffold_fastener.MODULE_KEY)
        defn = registry.get(module)
        if defn is None:
            return Response({"detail": f"unknown module: {module}"}, status=status.HTTP_404_NOT_FOUND)
        try:
            content = batch_csv(run_batch(cases, defn.run))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return HttpResponse(
            content,
            content_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="batch-results.csv"'},
        )


class ModulesView(APIView):
    def get(self, request):
        return Response({"modules": registry.list_modules()})


class ResultsCsvView(APIView):
    def post(self, request):
        params = request.data.get("params") or {}
        module = request.data.get("module", scaffold_fastener.MODULE_KEY)
        defn = registry.get(module)
        if defn is None:
            return Response({"detail": f"unknown module: {module}"}, status=status.HTTP_404_NOT_FOUND)
        try:
            payload = defn.run(params)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["项次", "计算项", "计算值", "限值", "单位", "利用率", "判定", "规范条文", "控制项"])
        for r in payload["results"]:
            writer.writerow(
                [
                    r["no"],
                    r["item"],
                    r["value"],
                    r["limit"],
                    r["unit"],
                    f"{r['ratio'] * 100:.1f}%",
                    "满足要求" if r["ok"] else "不满足要求",
                    r["clause"],
                    "是" if r["control"] else "否",
                ]
            )
        content = ("\ufeff" + buf.getvalue()).encode("utf-8")
        return HttpResponse(
            content,
            content_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="results.csv"'},
        )
