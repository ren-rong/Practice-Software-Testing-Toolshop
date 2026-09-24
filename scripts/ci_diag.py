"""
CI 临时诊断脚本：在 GitHub Actions（Azure runner）上复现/绕过 Cloudflare 质询。
Context A: 默认 Chromium
Context B: 真实 Chrome UA
Context C: 真实 UA + stealth init script + 等待挑战自动通过
诊断完成后此脚本会被移除，不进入最终交付。
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "https://practicesoftwaretesting.com"
REAL_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

# 轻量 stealth：隐藏最明显的自动化指纹（不依赖第三方包）
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
window.chrome = { runtime: {} };
"""


def report(page, label):
    card_count = page.locator('a.card[data-test^="product-"]').count()
    any_card = page.locator("a.card").count()
    print(f"[{label}] final url: {page.url}")
    print(f"[{label}] title: {page.title()}")
    print(f"[{label}] real cards: {card_count}; any a.card: {any_card}")
    body = page.evaluate("() => document.body.innerText.slice(0, 300)")
    print(f"[{label}] body text:\n{body}")
    return card_count


def run(p, label, use_real_ua, stealth=False, wait_pass=False):
    print(f"\n{'='*30}\n=== Context {label}: real_ua={use_real_ua} stealth={stealth} wait={wait_pass}\n{'='*30}")
    browser = p.chromium.launch()
    kwargs = {"viewport": {"width": 1920, "height": 1080}, "locale": "en-US"}
    if use_real_ua:
        kwargs["user_agent"] = REAL_UA
    ctx = browser.new_context(**kwargs)
    if stealth:
        ctx.add_init_script(STEALTH_JS)
    page = ctx.new_page()

    console_msgs, page_errors, failed_reqs, bad_resp = [], [], [], []
    page.on("console", lambda m: console_msgs.append(f"{m.type}: {m.text[:180]}"))
    page.on("pageerror", lambda e: page_errors.append(str(e)[:250]))
    page.on("requestfailed", lambda r: failed_reqs.append(
        f"{r.method} {r.url[:140]} -> {r.failure}"))
    page.on("response", lambda r: bad_resp.append(
        f"{r.status} {r.request.method} {r.url[:140]}") if r.status >= 400 else None)

    try:
        resp = page.goto(BASE + "/", wait_until="domcontentloaded", timeout=60000)
        print(f"goto status: {resp.status if resp else 'None'}")
    except Exception as e:
        print(f"goto error: {e}")

    if wait_pass:
        # 轮询等待 Cloudflare 挑战自动放行（标题离开 Just a moment 且出现卡片）
        try:
            page.wait_for_function(
                """() => !document.title.includes('Just a moment')
                   && document.querySelectorAll('a.card[data-test^=\"product-\"]').length > 0""",
                timeout=45000)
            print("challenge PASSED automatically within 45s")
        except Exception:
            print("challenge did NOT pass within 45s")
    else:
        page.wait_for_timeout(25000)

    report(page, label)

    print("--- console (last 10) ---")
    for m in console_msgs[-10:]:
        print(m)
    print("--- pageerror ---")
    for e in page_errors[:10]:
        print(e)
    print("--- requestfailed ---")
    for r in failed_reqs[:10]:
        print(r)
    print("--- responses >=400 (last 15) ---")
    for r in bad_resp[-15:]:
        print(r)

    ctx.close()
    browser.close()


def main():
    with sync_playwright() as p:
        run(p, "A", use_real_ua=False)
        run(p, "B", use_real_ua=True)
        run(p, "C", use_real_ua=True, stealth=True, wait_pass=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
