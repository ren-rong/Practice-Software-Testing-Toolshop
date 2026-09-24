import pytest
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.product_page import ProductPage
from pages.cart_page import CartPage

pytestmark = [pytest.mark.ui]


def test_home_page_loads(page, base_url):
    """首页能正常加载"""
    home = HomePage(page, base_url)
    home.open()
    assert "Practice Software Testing" in home.get_page_title()


def test_customer_login(page, base_url, fresh_user_ui):
    """使用运行时注册的新账号登录，避免公共 demo 账号被锁定"""
    # 先打开首页（Cloudflare 对首页放行），再通过 Angular 客户端路由进入登录页；
    # 直接 goto /auth/login 整页加载会被 Cloudflare 强制验证并卡死
    home = HomePage(page, base_url)
    home.open()
    home.click_login()

    login = LoginPage(page, base_url)
    login.login(fresh_user_ui["email"], fresh_user_ui["password"])
    login.expect_login_success()


def test_search_product_and_open_detail(page, base_url, test_data):
    """搜索商品并打开详情页"""
    home = HomePage(page, base_url)
    home.open()

    keyword = test_data["products"]["search_keyword"]
    home.search(keyword)
    home.click_first_product()

    product = ProductPage(page, base_url)
    name = product.get_product_name()
    assert keyword.lower() in name.lower(), f"商品详情页名称不包含关键字: {name}"


def test_add_product_to_cart(page, base_url, test_data):
    """搜索商品 -> 加入购物车 -> 购物车页校验"""
    home = HomePage(page, base_url)
    home.open()

    keyword = test_data["products"]["search_keyword"]
    home.search(keyword)
    home.click_first_product()

    product = ProductPage(page, base_url)
    product.add_to_cart(quantity=1)
    product.expect_add_to_cart_success()

    # 通过 Angular 客户端路由进入购物车页；直接 goto /checkout 整页加载
    # 会被 Cloudflare 强制验证并卡死，而购物车数据 XHR 本就走不拦截的 API 子域
    home.click_cart()

    cart = CartPage(page, base_url)
    cart.expect_cart_has_items(min_count=1)
