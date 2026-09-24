import os
import pytest
import requests
import yaml

from api.user_api import UserApi
from api.product_api import ProductApi
from api.cart_api import CartApi
from api.invoice_api import InvoiceApi


# --------------------------- 常量与工具 ---------------------------

@pytest.fixture(scope="session")
def base_url():
    """Web 前端地址"""
    return os.getenv("BASE_URL", "https://practicesoftwaretesting.com")


@pytest.fixture(scope="session")
def api_base_url():
    """API 后端地址"""
    return os.getenv("API_BASE_URL", "https://api.practicesoftwaretesting.com")


@pytest.fixture(scope="session")
def test_data():
    """加载 test_data/data.yaml 测试数据"""
    data_file = os.path.join(os.path.dirname(__file__), "test_data", "data.yaml")
    with open(data_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------- API 会话与接口对象 ---------------------------

@pytest.fixture(scope="session")
def api_session():
    """共享的 requests.Session（对公共 demo 环境偶发的 5xx 自动重试）"""
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json"
    })
    # Toolshop 是公共演示站，后端偶发 500/502/503，加重试避免环境抖动导致误报
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST", "PUT", "PATCH", "DELETE"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    yield session
    session.close()


@pytest.fixture(scope="session")
def user_api(api_session, api_base_url):
    return UserApi(api_session, api_base_url)


@pytest.fixture(scope="session")
def product_api(api_session, api_base_url):
    return ProductApi(api_session, api_base_url)


@pytest.fixture(scope="session")
def cart_api(api_session, api_base_url):
    return CartApi(api_session, api_base_url)


@pytest.fixture(scope="session")
def invoice_api(api_session, api_base_url):
    return InvoiceApi(api_session, api_base_url)


@pytest.fixture(scope="session")
def customer_token(user_api, test_data):
    """
    使用默认 customer 账号登录，返回 access_token。
    该 fixture 在整轮测试中只执行一次。
    """
    customer = test_data["users"]["customer"]
    resp = user_api.login(customer["email"], customer["password"])
    assert resp.status_code == 200, f"customer 登录失败: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def fresh_user_ui(user_api):
    """
    注册一个全新的测试账号，供 UI 登录测试使用。
    使用 uuid 保证邮箱唯一，避免账号锁定和重复注册问题。
    """
    import uuid

    email = f"uitester_{uuid.uuid4().hex[:10]}@example.com"
    password = "Ui#9xK2$mP7!qL4@"
    resp = user_api.register(
        first_name="UI",
        last_name="Tester",
        email=email,
        password=password,
    )
    assert resp.status_code in (200, 201), f"UI 测试账号注册失败: {resp.status_code} {resp.text}"
    return {"email": email, "password": password}


# --------------------------- Playwright 浏览器配置 ---------------------------

@pytest.fixture(scope="session")
def browser_context_args():
    """
    pytest-playwright 提供的 fixture：
    返回的 dict 会传入 browser.new_context()，统一设置 viewport。
    """
    return {
        "viewport": {"width": 1920, "height": 1080},
    }
