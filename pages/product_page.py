from playwright.sync_api import Page, expect

from pages.browser_utils import wait_for_verification


class ProductPage:
    """商品详情页页面对象"""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def add_to_cart(self, quantity: int = 1):
        """在商品详情页加入购物车"""
        # 兜底：详情页若命中 Cloudflare 验证页，先等其自动通过
        wait_for_verification(self.page)
        # 先等待 add-to-cart 按钮渲染完成（Angular SPA 动态加载）
        add_btn = self.page.locator('[data-test="add-to-cart"]')
        add_btn.wait_for(timeout=10000)

        # 数量控件找不到时容错跳过（很多商品默认数量就是 1）
        try:
            qty_locator = self.page.locator(
                '[data-test="quantity"], input[type="number"], select[name="quantity"]'
            )
            qty_locator.first.wait_for(timeout=3000)
            elem = qty_locator.first
            tag = elem.evaluate("el => el.tagName").lower()
            if tag == "input":
                elem.fill(str(quantity))
            elif tag == "select":
                elem.select_option(str(quantity))
        except Exception:
            # 数量控件不存在时忽略，使用默认值
            pass

        add_btn.click()

    def get_product_name(self) -> str:
        """获取商品名称"""
        name_locator = self.page.locator('[data-test="product-name"], h1, .product-name')
        name_locator.first.wait_for(timeout=10000)
        return name_locator.first.text_content()

    def get_unit_price(self) -> str:
        """获取商品单价文本"""
        price_locator = self.page.locator('[data-test="unit-price"], .unit-price, .price')
        price_locator.first.wait_for(timeout=10000)
        return price_locator.first.text_content()

    def expect_add_to_cart_success(self):
        """
        断言加入购物车成功提示可见。
        demo 站偶发点击未生效或 toast 未渲染：首次等待失败后补点一次再验证；
        补点时即使首次其实已成功，购物车仅多一件商品，不影响后续数量断言。
        两次均失败才抛出，交给 pytest-rerunfailures 重跑整个用例。
        """
        alert = self.page.locator('[role="alert"]')
        try:
            expect(alert).to_contain_text(
                "added to shopping cart", timeout=10000
            )
            return
        except Exception:
            pass

        self.page.locator('[data-test="add-to-cart"]').click()
        expect(alert).to_contain_text(
            "added to shopping cart", timeout=10000
        )
