import pytest
from pages.home_page import HomePage

pytestmark = [pytest.mark.mixed]


def test_api_fetches_product_then_ui_displays_it(page, base_url, product_api, test_data):
    """
    混合测试示例：
    1. 通过 API 拿到真实商品名称
    2. 在 UI 中搜索该商品，验证前端能正确展示
    """
    # API 层：获取商品列表
    resp = product_api.list_products()
    assert resp.status_code == 200, f"API 获取商品失败: {resp.text}"
    products = resp.json().get("data", resp.json())
    assert products, "API 返回商品为空"

    # 取第一个商品名（可能较长，只取前几个安全字符）
    product_name = products[0]["name"]
    search_keyword = product_name.split()[0] if " " in product_name else product_name

    # UI 层：用商品名搜索并验证展示
    home = HomePage(page, base_url)
    home.open()
    home.search(search_keyword)

    # 断言搜索结果中至少有一个真实商品卡片（a.card[data-test]），且包含该商品名
    # 不能用裸 .card —— 骨架屏卡片也带 .card 但文本为空
    cards = home.product_cards
    cards.first.wait_for(timeout=10000)
    assert cards.count() >= 1, "UI 搜索未返回商品"
    visible_text = cards.first.text_content() or ""
    assert search_keyword.lower() in visible_text.lower(), f"UI 未展示目标商品: {visible_text}"
