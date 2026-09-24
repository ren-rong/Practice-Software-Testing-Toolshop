"""Cloudflare 安全验证页的统一处理工具。

Toolshop 前端挂在 Cloudflare 之后，GitHub Actions 数据中心 IP 访问时
会被间歇性下发被动验证页（标题 "Just a moment..."，正文
"Performing security verification"）。该验证页无需人工交互，
其 JS 会在数秒至数十秒内自动完成验证并恢复原页面；
本模块提供检测与自动等待能力，供各 Page Object 在导航后调用。
"""
import time


CHALLENGE_TITLE = "Just a moment"
CHALLENGE_BODY = "Performing security verification"

_IS_CHALLENGE_JS = """
() => {
    const t = document.title || '';
    const b = document.body ? (document.body.innerText || '') : '';
    return t.includes('Just a moment')
        || b.includes('Performing security verification');
}
"""

_PASSED_JS = """
() => {
    const t = document.title || '';
    const b = document.body ? (document.body.innerText || '') : '';
    return !t.includes('Just a moment')
        && !b.includes('Performing security verification');
}
"""


def is_challenge_page(page) -> bool:
    """判断当前页面是否为 Cloudflare 安全验证页。"""
    try:
        if page.evaluate(_IS_CHALLENGE_JS):
            return True
    except Exception:
        pass
    return False


def wait_for_verification(page, timeout: int = 30):
    """
    若当前是 Cloudflare 验证页，等待其自动完成验证后返回。

    策略：轮询等待页面离开验证状态；若验证页卡住（headless 下偶发），
    用 reload 触发重新验证。超时仍未通过则抛出 TimeoutError，
    交给 pytest-rerunfailures 做用例级重试。
    """
    if not is_challenge_page(page):
        return

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            page.wait_for_function(_PASSED_JS, timeout=8000)
            page.wait_for_timeout(500)
            if not is_challenge_page(page):
                return
        except Exception:
            pass

        # 验证页卡住：reload 触发重新验证（各接入点均为 GET 页面，reload 安全）
        try:
            page.reload(wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
        except Exception:
            time.sleep(2)

    raise TimeoutError(f"Cloudflare 验证页未在 {timeout}s 内自动通过")
