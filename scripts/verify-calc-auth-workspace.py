from __future__ import annotations

import argparse
import json
import re
import secrets
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Response, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "artifacts" / "auth-workspace-qa"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PROJECT_PATH = re.compile(r"/projects/([0-9a-f-]{36})/calc$")


def print_step(message: str) -> None:
    print(f"STEP {message}", flush=True)


def api_path(response: Response) -> str:
    return urlparse(response.url).path


def is_api_response(response: Response) -> bool:
    return "/api/v1/" in response.url


def overflow_state(page) -> dict[str, int | bool]:
    values = page.evaluate(
        """() => ({
            innerWidth: window.innerWidth,
            htmlScrollWidth: document.documentElement.scrollWidth,
            bodyScrollWidth: document.body.scrollWidth,
            offenders: [...document.querySelectorAll('body *')]
              .map((element) => {
                const rect = element.getBoundingClientRect()
                return {
                  tag: element.tagName.toLowerCase(),
                  className: typeof element.className === 'string' ? element.className : '',
                  left: Math.round(rect.left),
                  right: Math.round(rect.right),
                  width: Math.round(rect.width),
                  text: (element.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 120),
                }
              })
              .filter((item) => item.width > 0 && (item.left < -1 || item.right > window.innerWidth + 1))
              .slice(0, 20),
        })"""
    )
    values["overflow"] = (
        values["htmlScrollWidth"] > values["innerWidth"] + 1
        or values["bodyScrollWidth"] > values["innerWidth"] + 1
    )
    return values


def assert_no_overflow(page, label: str, evidence: dict) -> None:
    state = overflow_state(page)
    evidence[f"{label}_overflow"] = state
    if state["overflow"]:
        raise AssertionError(f"{label} has horizontal overflow: {state}")


def screenshot(page, path: Path, evidence: dict) -> None:
    page.screenshot(path=str(path))
    evidence["screenshots"].append(str(path.resolve()))
    print_step(f"screenshot {path.resolve()}")


def wait_for_computed(page, timeout: int = 90_000) -> None:
    page.get_by_text(re.compile(r"已计算 · \d+ 项")).first.wait_for(timeout=timeout)


def wait_for_workspace(page) -> None:
    page.get_by_role("heading", name="项目工作台").wait_for(timeout=30_000)


def login(page, base_url: str, email: str, password: str, next_path: str = "/workspace") -> None:
    page.goto(f"{base_url}{next_path}", wait_until="domcontentloaded")
    page.wait_for_url(re.compile(r"/login\?next="), timeout=30_000)
    page.get_by_label("邮箱", exact=True).fill(email)
    page.get_by_label("密码", exact=True).fill(password)
    page.get_by_role("button", name="登录", exact=True).click()
    page.wait_for_url(re.compile(re.escape(next_path) + r"$"), timeout=30_000)


def register(page, email: str, password: str) -> None:
    page.get_by_label("邮箱", exact=True).fill(email)
    page.get_by_label("密码", exact=True).fill(password)
    page.get_by_label("确认密码", exact=True).fill(password)
    page.get_by_role("button", name="注册", exact=True).click()
    page.wait_for_url("**/workspace", timeout=30_000)


def logout(page) -> None:
    page.locator("header button").last.click()
    page.get_by_role("menuitem", name="退出登录").click()
    page.wait_for_url("**/login", timeout=30_000)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5179")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    if not CHROME.is_file():
        raise FileNotFoundError(f"Chrome not found: {CHROME}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    run_tag = f"{int(time.time())}-{secrets.token_hex(4)}"
    shots_dir = OUTPUT_ROOT / "shots" / f"verify-{run_tag}"
    result_path = OUTPUT_ROOT / f"auth_workspace_e2e_{run_tag}_result.json"
    shots_dir.mkdir(parents=True, exist_ok=False)

    account_a = f"qa-a-{run_tag}@example.invalid"
    account_b = f"qa-b-{run_tag}@example.invalid"
    password_a = f"QaA!{secrets.token_urlsafe(20)}"
    password_b = f"QaB!{secrets.token_urlsafe(20)}"
    project_name = f"QA-Shanghai-Acceptance-{run_tag}"
    scheme_name = f"QA-Scheme-{secrets.token_hex(3)}"

    console_errors: list[str] = []
    expected_console_401: list[str] = []
    page_errors: list[str] = []
    request_failures: list[str] = []
    api_failures: list[tuple[int, str]] = []
    api_5xx: list[tuple[int, str]] = []
    expected_401: list[str] = []
    authenticated = {"value": False}
    evidence: dict = {
        "run_tag": run_tag,
        "result_path": str(result_path.resolve()),
        "project_name": project_name,
        "project_id": None,
        "steps": [],
        "screenshots": [],
    }

    def sanitize(value: str) -> str:
        cleaned = value
        for secret_value in (
            account_a,
            account_b,
            password_a,
            password_b,
            project_name,
            scheme_name,
        ):
            cleaned = cleaned.replace(secret_value, "[REDACTED]")
        return cleaned

    def on_console(message) -> None:
        if message.type != "error":
            return
        location = urlparse(message.location.get("url", "")).path
        if (
            "status of 401" in message.text
            and not authenticated["value"]
            and location.endswith("/api/v1/auth/me")
        ):
            expected_console_401.append(location)
            return
        console_errors.append(message.text)

    def on_response(response: Response) -> None:
        if not is_api_response(response):
            return
        path = api_path(response)
        status = response.status
        if status >= 500:
            api_5xx.append((status, path))
            return
        if status >= 400:
            if status == 401 and path.endswith("/auth/me") and not authenticated["value"]:
                expected_401.append(path)
            else:
                api_failures.append((status, path))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=str(CHROME),
        )
        context = browser.new_context(
            base_url=base_url,
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()
        page.on("console", on_console)
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on(
            "requestfailed",
            lambda request: request_failures.append(
                f"{request.method} {urlparse(request.url).path}"
            )
            if "/api/v1/" in request.url
            else None,
        )
        page.on("response", on_response)

        try:
            print_step("anonymous /workspace redirects to login with safe next")
            page.goto(f"{base_url}/workspace", wait_until="domcontentloaded")
            page.wait_for_url(re.compile(r"/login\?next="), timeout=30_000)
            next_value = parse_qs(urlparse(page.url).query).get("next", [""])[0]
            assert next_value == "/workspace", f"unexpected next value: {next_value!r}"
            screenshot(page, shots_dir / "login-1440.png", evidence)
            evidence["steps"].append("anonymous workspace redirect")

            print_step("register account A on 390px viewport")
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(f"{base_url}/register", wait_until="domcontentloaded")
            page.get_by_role("button", name="注册", exact=True).wait_for()
            assert_no_overflow(page, "register_390", evidence)
            screenshot(page, shots_dir / "register-390.png", evidence)
            register(page, account_a, password_a)
            authenticated["value"] = True
            evidence["steps"].append("register account A")

            print_step("workspace empty state at 1440px")
            page.set_viewport_size({"width": 1440, "height": 900})
            wait_for_workspace(page)
            page.get_by_text("从第一个项目开始", exact=True).wait_for()
            assert_no_overflow(page, "workspace_empty_1440", evidence)
            screenshot(page, shots_dir / "workspace-empty-1440.png", evidence)
            evidence["steps"].append("workspace empty state")

            print_step("create Shanghai preparing project and enter calculation")
            page.get_by_role("button", name="新建项目", exact=True).click()
            dialog = page.get_by_role("dialog")
            dialog.get_by_label("项目名称", exact=True).fill(project_name)
            dialog.get_by_label("项目地区", exact=True).select_option("上海")
            dialog.get_by_label("项目状态", exact=True).select_option("preparing")
            with page.expect_response(
                lambda response: is_api_response(response)
                and response.request.method == "POST"
                and api_path(response) == "/api/v1/projects"
            ) as created_response:
                dialog.get_by_role("button", name="创建并进入", exact=True).click()
            created = created_response.value
            assert created.status == 201, f"project creation returned {created.status}"
            project_id = created.json()["project_id"]
            evidence["project_id"] = project_id
            page.wait_for_url(re.compile(r"/projects/[0-9a-f-]{36}/calc$"), timeout=30_000)
            match = PROJECT_PATH.search(urlparse(page.url).path)
            assert match and match.group(1) == project_id
            page.get_by_text(project_name, exact=True).wait_for(timeout=30_000)
            context_bar = page.locator("div").filter(has_text=project_name).first
            assert context_bar.get_by_text("上海", exact=True).is_visible()
            assert context_bar.get_by_text("筹备中", exact=True).is_visible()
            evidence["steps"].append("create Shanghai preparing project")

            print_step("wait for calculation and save current project scheme")
            wait_for_computed(page)
            assert_no_overflow(page, "calc_project_1440", evidence)
            screenshot(page, shots_dir / "calc-project-1440.png", evidence)
            page.get_by_role("button", name="方案", exact=True).click()
            scheme_dialog = page.get_by_role("dialog")
            scheme_dialog.get_by_text("当前项目方案", exact=True).wait_for()
            scheme_dialog.get_by_label("方案名称", exact=True).fill(scheme_name)
            with page.expect_response(
                lambda response: is_api_response(response)
                and response.request.method == "POST"
                and api_path(response) == f"/api/v1/projects/{project_id}/schemes"
            ) as scheme_response:
                scheme_dialog.get_by_role("button", name="保存方案", exact=True).click()
            assert scheme_response.value.status == 201
            scheme_dialog.wait_for(state="hidden", timeout=30_000)
            screenshot(page, shots_dir / "scheme-saved-1440.png", evidence)
            evidence["steps"].append("save scheme")

            print_step("return to workspace and verify derived progress")
            page.get_by_role("link", name="返回项目工作台").click()
            page.wait_for_url("**/workspace", timeout=30_000)
            wait_for_workspace(page)
            project_row = page.locator(
                f'[role="row"][aria-label="{project_name} 上海 筹备中"]'
            )
            project_row.wait_for(timeout=30_000)
            row_text = project_row.inner_text()
            assert "1" in row_text, f"scheme count missing from row: {row_text!r}"
            assert "尚未计算" not in row_text
            assert_no_overflow(page, "workspace_project_1440", evidence)
            screenshot(page, shots_dir / "workspace-updated-1440.png", evidence)
            evidence["steps"].append("workspace derived progress")

            print_step("reload workspace and verify session/project persistence")
            page.reload(wait_until="networkidle")
            wait_for_workspace(page)
            page.locator(
                f'[role="row"][aria-label="{project_name} 上海 筹备中"]'
            ).wait_for(timeout=30_000)
            evidence["steps"].append("session and project survive reload")

            print_step("edit project status and verify search/filter/clear")
            project_row.get_by_role(
                "button", name=f"更多操作 {project_name}", exact=True
            ).click()
            page.get_by_role("menuitem", name="编辑项目", exact=True).click()
            edit_dialog = page.get_by_role("dialog")
            edit_dialog.get_by_label("项目状态", exact=True).select_option("calculating")
            with page.expect_response(
                lambda response: is_api_response(response)
                and response.request.method == "PATCH"
                and api_path(response) == f"/api/v1/projects/{project_id}"
            ) as updated_response:
                edit_dialog.get_by_role("button", name="保存修改", exact=True).click()
            assert updated_response.value.status == 200
            edit_dialog.wait_for(state="hidden", timeout=30_000)
            project_row = page.locator(
                f'[role="row"][aria-label="{project_name} 上海 计算中"]'
            )
            project_row.wait_for(timeout=30_000)
            page.get_by_label("搜索项目", exact=True).fill(project_name)
            page.wait_for_url(re.compile(r"search="), timeout=30_000)
            project_row.wait_for(timeout=30_000)
            page.get_by_label("状态筛选", exact=True).select_option("calculating")
            page.wait_for_url(re.compile(r"status=calculating"), timeout=30_000)
            project_row.wait_for(timeout=30_000)
            page.get_by_label("搜索项目", exact=True).fill(f"NO-MATCH-{run_tag}")
            page.get_by_text("没有匹配的项目", exact=True).wait_for(timeout=30_000)
            page.get_by_role("button", name="清除筛选", exact=True).click()
            assert page.get_by_label("搜索项目", exact=True).input_value() == ""
            assert page.get_by_label("状态筛选", exact=True).input_value() == ""
            project_row.wait_for(timeout=30_000)
            evidence["steps"].append("edit/search/filter/clear")

            print_step("workspace and calculation pages at 390px")
            page.set_viewport_size({"width": 390, "height": 844})
            wait_for_workspace(page)
            assert_no_overflow(page, "workspace_390", evidence)
            screenshot(page, shots_dir / "workspace-390.png", evidence)
            page.goto(
                f"{base_url}/projects/{project_id}/calc",
                wait_until="domcontentloaded",
            )
            wait_for_computed(page)
            assert_no_overflow(page, "calc_390", evidence)
            screenshot(page, shots_dir / "calc-390.png", evidence)
            evidence["steps"].append("responsive 390px workspace/calculation")

            print_step("account A logout, account B isolation, then account A login")
            page.set_viewport_size({"width": 1440, "height": 900})
            page.goto(f"{base_url}/workspace", wait_until="domcontentloaded")
            wait_for_workspace(page)
            logout(page)

            page.goto(f"{base_url}/register", wait_until="domcontentloaded")
            register(page, account_b, password_b)
            authenticated["value"] = True
            wait_for_workspace(page)
            page.get_by_text("从第一个项目开始", exact=True).wait_for()
            assert page.get_by_text(project_name, exact=True).count() == 0
            evidence["steps"].append("account B cannot see account A project")

            logout(page)
            authenticated["value"] = False
            login(page, base_url, account_a, password_a)
            authenticated["value"] = True
            wait_for_workspace(page)
            project_row = page.locator(
                f'[role="row"][aria-label="{project_name} 上海 计算中"]'
            )
            project_row.wait_for(timeout=30_000)
            evidence["steps"].append("account A login resumes prior project")

            print_step("verify session and CSRF cookie flags")
            cookies = {cookie["name"]: cookie for cookie in context.cookies(base_url)}
            session_cookie = cookies.get("sessionid")
            csrf_cookie = cookies.get("csrftoken")
            assert session_cookie is not None
            assert csrf_cookie is not None
            assert session_cookie["httpOnly"] is True
            assert csrf_cookie["httpOnly"] is False
            assert session_cookie["sameSite"] == "Lax"
            assert csrf_cookie["sameSite"] == "Lax"
            evidence["cookie_flags"] = {
                "sessionid": {
                    "httpOnly": session_cookie["httpOnly"],
                    "sameSite": session_cookie["sameSite"],
                },
                "csrftoken": {
                    "httpOnly": csrf_cookie["httpOnly"],
                    "sameSite": csrf_cookie["sameSite"],
                },
            }
            evidence["steps"].append("cookie flags")

            print_step("delete account A project with confirmation")
            project_row.get_by_role(
                "button", name=f"更多操作 {project_name}", exact=True
            ).click()
            page.get_by_role("menuitem", name="删除项目", exact=True).click()
            confirm_dialog = page.get_by_role("alertdialog")
            confirm_dialog.get_by_text("级联删除", exact=False).wait_for()
            with page.expect_response(
                lambda response: is_api_response(response)
                and response.request.method == "DELETE"
                and api_path(response) == f"/api/v1/projects/{project_id}"
            ) as deleted_response:
                confirm_dialog.get_by_role("button", name="确认删除", exact=True).click()
            assert deleted_response.value.status == 204
            confirm_dialog.wait_for(state="hidden", timeout=30_000)
            page.get_by_text("从第一个项目开始", exact=True).wait_for(timeout=30_000)
            assert page.get_by_text(project_name, exact=True).count() == 0
            evidence["steps"].append("delete project")

            assert not console_errors, f"{len(console_errors)} console error(s)"
            assert not page_errors, f"{len(page_errors)} page error(s)"
            assert not request_failures, f"{len(request_failures)} failed API request(s)"
            assert not api_failures, f"{len(api_failures)} unexpected API response(s)"
            assert not api_5xx, f"{len(api_5xx)} API 5xx response(s)"

            evidence.update(
                {
                    "success": True,
                    "console_error_count": len(console_errors),
                    "expected_console_401_count": len(expected_console_401),
                    "pageerror_count": len(page_errors),
                    "requestfailure_count": len(request_failures),
                    "api_failure_count": len(api_failures),
                    "api_5xx_count": len(api_5xx),
                    "expected_401_count": len(expected_401),
                }
            )
            result_path.write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(
                json.dumps(
                    {
                        "success": True,
                        "result_path": str(result_path.resolve()),
                        "screenshots": evidence["screenshots"],
                        "console_error_count": len(console_errors),
                        "expected_console_401_count": len(expected_console_401),
                        "pageerror_count": len(page_errors),
                        "requestfailure_count": len(request_failures),
                        "api_failure_count": len(api_failures),
                        "api_5xx_count": len(api_5xx),
                        "expected_401_count": len(expected_401),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                flush=True,
            )
        except Exception as exc:
            evidence.update(
                {
                    "success": False,
                    "failure": sanitize(str(exc)),
                    "console_error_examples": [
                        sanitize(message) for message in console_errors[:5]
                    ],
                    "pageerror_examples": [
                        sanitize(message) for message in page_errors[:5]
                    ],
                    "requestfailure_examples": request_failures[:5],
                    "console_error_count": len(console_errors),
                    "expected_console_401_count": len(expected_console_401),
                    "pageerror_count": len(page_errors),
                    "requestfailure_count": len(request_failures),
                    "api_failure_count": len(api_failures),
                    "api_5xx_count": len(api_5xx),
                    "expected_401_count": len(expected_401),
                    "overflow": {
                        key: value
                        for key, value in evidence.items()
                        if key.endswith("_overflow")
                    },
                }
            )
            result_path.write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(json.dumps(evidence, ensure_ascii=False, indent=2), flush=True)
            raise
        finally:
            browser.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
