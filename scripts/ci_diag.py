"""
CI 临时诊断脚本：在 GitHub Actions（Azure runner）上复现 UI 不渲染问题。
输出：最终 URL / 标题 / body 文本 / 商品卡片数量 / 控制台错误 / 页面异常 / 失败请求 / 异常响应。
对比两种浏览器上下文：A=默认  B=模拟真实 Chrome UA。
诊断完成后此脚本会被移除，不进入最终交付。
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "https://practicesoftwaretesting.com"


def run(p, label, use_real_ua):
    print(f"\n{'=' * 30}\n=== Context {label}: real_ua={use_real_ua}\n{'=' * 30}")
    browser = p.chromium.launch()
    kwargs = {"viewport": {"width": 1920, "height": 1080}, "locale": "en-US"}
    if use_real_ua:
        # 去掉 HeadlessChrome 标记，使用标准 Chrome UA
        kwargs["user_agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
    ctx = browser.new_context(**kwargs)
    page = ctx.new_page()

    console_msgs, page_errors, failed_reqs, bad_responses = [], [], [], []
    page.on("console", lambda m: console_msgs.append(f"{m.type}: {m.text[:200]}"))
    page.on("pageerror", lambda e: page_errors.append(str(e)[:300]))
    page.on("requestfailed", lambda r: failed_reqs.append(
        f"{r.method} {r.url[:150]} -> {r.failure}"))
    page.on("response", lambda r: bad_responses.append(
        f"{r.status} {r.request.method} {r.url[:150]}")
        if r.status >= 400 else None)

    try:
        resp = page.goto(BASE + "/", wait_until="domcontentloaded", timeout=60000)
        print(f"goto status: {resp.status if resp else 'None'} "
              f"(final url: {resp.url if resp else '?'})")
    except Exception as e:
        print(f"goto error: {e}")

    page.wait_for_timeout(25000)

    print(f"final url: {page.url}")
    print(f"title: {page.title()}")
    card_count = page.locator('a.card[data-test^="product-"]').count()
    any_card = page.locator("a.card").count()
    print(f"real product cards: {card_count}; any a.card: {any_card}")
    body_text = page.evaluate("() => document.body.innerText.slice(0, 600)")
    print(f"body text:\n{body_text}")

    # 再试登录页
    try:
        page.goto(BASE + "/auth/login", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)
        print(f"\nlogin url: {page.url}")
        print(f"login title: {page.title()}")
        print(f"email inputs: {page.locator(\"input[type='email']\").count()}")
        print(f"login body text:\n{page.evaluate('() => document.body.innerText.slice(0, 300)')}")
    except Exception as e:
        print(f"login goto error: {e}")

    print("\n--- console (last 15) ---")
    for m in console_msgs[-15:]:
        print(m)
    print("--- pageerror ---")
    for e in page_errors[:15]:
        print(e)
    print("--- requestfailed ---")
    for r in failed_reqs[:15]:
        print(r)
    print("--- responses >=400 ---")
    for r in bad_responses[:20]:
        print(r)

    ctx.close()
    browser.close()


def main():
    with sync_playwright() as p:
        run(p, "A", use_real_ua=False)
        run(p, "B", use_real_ua=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
