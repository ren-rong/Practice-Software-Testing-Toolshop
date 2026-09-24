from playwright.sync_api import Page, expect


class CartPage:
    """购物车页页面对象"""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self):
        """打开购物车页"""
        self.page.goto(f"{self.base_url}/checkout", wait_until="domcontentloaded", timeout=60000)

    def get_items_count(self) -> int:
        """获取购物车商品行数（站点用 table tbody tr 展示商品）"""
        return self.page.locator('table tbody tr').count()

    def get_total_text(self) -> str:
        """获取购物车合计金额文本"""
        # 合计位于表格最后一行或页面右下角，取可见文本兜底
        return self.page.locator('table tfoot').first.text_content() or ""

    def click_checkout(self):
        """点击结算按钮"""
        self.page.click('button:has-text("Checkout")')

    def expect_cart_has_items(self, min_count: int = 1):
        """断言购物车中至少有指定数量的商品"""
        # 等待至少一行出现
        self.page.locator('table tbody tr').first.wait_for(timeout=10000)
        count = self.page.locator('table tbody tr').count()
        assert count >= min_count, f"购物车商品行数 {count} 小于 {min_count}"
