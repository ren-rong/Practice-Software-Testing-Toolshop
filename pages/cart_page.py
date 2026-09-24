from playwright.sync_api import Page

from pages.browser_utils import wait_for_verification


class CartPage:
    """购物车页页面对象"""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        # 购物车商品行（站点用 table 展示）
        self.item_rows = page.locator("table tbody tr")

    def open(self):
        """打开购物车页"""
        self.page.goto(f"{self.base_url}/checkout",
                       wait_until="domcontentloaded", timeout=60000)
        # 购物车页可能命中 Cloudflare 验证页，先等其自动通过
        wait_for_verification(self.page)

    def get_items_count(self) -> int:
        """获取购物车商品行数（站点用 table tbody tr 展示商品）"""
        return self.item_rows.count()

    def get_total_text(self) -> str:
        """获取购物车合计金额文本"""
        # 合计位于表格最后一行或页面右下角，取可见文本兜底
        return self.page.locator("table tfoot").first.text_content() or ""

    def click_checkout(self):
        """点击结算按钮"""
        self.page.click('button:has-text("Checkout")')

    def expect_cart_has_items(self, min_count: int = 1):
        """断言购物车中至少有指定数量的商品"""
        # 兜底：数据加载期间若被下发验证页，先等其自动通过
        wait_for_verification(self.page)
        # CI 数据中心网络下，Angular 重新引导 + GET /carts/{id} 可能较慢，给足 30s
        try:
            self.item_rows.first.wait_for(timeout=30000)
        except Exception:
            # 失败时把页面真实状态带进断言，便于从日志定位（空车 / 跳登录 / 挑战页）
            state = self.page.evaluate(
                "() => ({ url: location.href, title: document.title, "
                "text: document.body.innerText.slice(0, 300) })")
            raise AssertionError(
                f"购物车商品行未在 30s 内出现；页面状态: {state}")

        count = self.item_rows.count()
        assert count >= min_count, f"购物车商品行数 {count} 小于 {min_count}"
