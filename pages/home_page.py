import re

from playwright.sync_api import Page, expect

from pages.browser_utils import wait_for_verification


class HomePage:
    """首页页面对象"""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        # 真实商品卡片：a.card 且带 data-test="product-<id>"
        # 注意：不能用裸 .card —— Angular 骨架屏/旧列表卡片也带 .card，
        # 但没有 data-test，点上去不会跳转，是 UI 测试偶发失败的根源
        self.product_cards = page.locator('a.card[data-test^="product-"]')

    def open(self):
        """打开首页并等待真实商品卡片渲染完成"""
        # demo 站偶发加载慢，load 事件可能超时；DOM ready 后靠等卡片兜底更稳
        self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
        # 命中 Cloudflare 验证页时先等其自动通过
        wait_for_verification(self.page)
        self.product_cards.first.wait_for(timeout=30000)

    def search(self, keyword: str):
        """在首页搜索框输入关键词并搜索，等待搜索结果真正刷新完成"""
        self.page.fill('[data-test="search-query"]', keyword)
        # 记录搜索前第一个真实商品卡片，用于判断列表是否已刷新
        old_id = ""
        if self.product_cards.count():
            old_id = self.product_cards.first.get_attribute("data-test") or ""

        self.page.click('[data-test="search-submit"]')

        # 等待搜索结果刷新：第一个真实商品卡片变了，或其文本已包含关键词。
        # 注意：不依赖网络 response 事件 —— 站点有缓存时 XHR 不一定触发，
        # 直接轮询 DOM 最可靠。若搜索结果第一张卡恰好和原来相同（如搜 "Combination"），
        # 文本匹配关键词也会立即通过，此时点旧卡本来就是同一个商品，无副作用。
        self.page.wait_for_function(
            """([oldId, kw]) => {
                const card = document.querySelector('a.card[data-test^="product-"]');
                if (!card) return false;
                const dt = card.getAttribute('data-test') || '';
                const text = (card.textContent || '').toLowerCase();
                return dt !== oldId || text.includes(kw);
            }""",
            arg=[old_id, keyword.lower()],
            timeout=15000,
        )
        # 给 Angular 一点收尾渲染时间，避免点击瞬间元素被 detach
        self.page.wait_for_timeout(500)

    def click_first_product(self):
        """点击搜索结果中的第一个真实商品，并等待商品详情页渲染完成"""
        self.product_cards.first.click()
        # Angular SPA：先确认路由跳到 /product/<id>，再等加入购物车按钮渲染
        expect(self.page).to_have_url(re.compile(r"/product/"), timeout=15000)
        # 详情页导航可能命中 Cloudflare 验证页，先等其自动通过
        wait_for_verification(self.page)
        self.page.locator('[data-test="add-to-cart"]').wait_for(timeout=15000)

    def click_login(self):
        """点击导航栏登录按钮"""
        self.page.click('[data-test="nav-login"]')

    def get_page_title(self):
        """获取页面标题"""
        return self.page.title()

    def expect_product_list_visible(self):
        """断言商品列表可见"""
        self.product_cards.first.wait_for(timeout=15000)
        count = self.product_cards.count()
        assert count >= 1, f"首页商品卡片数量 {count}，预期至少 1"
