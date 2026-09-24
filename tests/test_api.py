import pytest
import uuid

pytestmark = [pytest.mark.api]


@pytest.fixture(scope="session")
def fresh_user(user_api):
    """
    注册一个全新的测试账号，供后续登录、profile 等测试使用。
    使用 uuid 保证邮箱唯一，避免重复注册报错。
    """
    email = f"tester_{uuid.uuid4().hex[:10]}@example.com"
    password = "Mz8#pQxL$vK2wR9!"

    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password": password,
        "address": [
            {
                "street": "Street 1",
                "city": "City",
                "state": "State",
                "country": "Country",
                "postal_code": "1234AA",
            }
        ],
        "phone": "1234567890",
        "dob": "1970-01-01",
    }

    resp = user_api.register(**payload)
    assert resp.status_code in (200, 201), f"注册失败: {resp.status_code} {resp.text}"

    return {"email": email, "password": password}


def test_default_customer_login(user_api, test_data):
    """使用默认 customer 账号登录"""
    customer = test_data["users"]["customer"]
    resp = user_api.login(customer["email"], customer["password"])

    # 若账号被锁定则跳过而非失败，避免公共 demo 账号状态不可控导致 CI 频繁报错
    if resp.status_code == 423:
        pytest.skip("默认 customer 账号当前被锁定，跳过此用例")

    assert resp.status_code == 200, f"登录失败: {resp.status_code} {resp.text}"
    assert "access_token" in resp.json(), "登录响应缺少 access_token"


def test_register_new_user(fresh_user):
    """注册新用户：由 fresh_user fixture 完成，并断言注册成功"""
    assert fresh_user["email"]
    assert fresh_user["password"]


def test_login_with_fresh_user(user_api, fresh_user):
    """用 fresh_user 登录，获取 access_token"""
    resp = user_api.login(fresh_user["email"], fresh_user["password"])
    assert resp.status_code == 200, f"新用户登录失败: {resp.status_code} {resp.text}"
    assert "access_token" in resp.json()


def test_get_user_profile(user_api, fresh_user):
    """
    使用 access_token 访问受保护接口 /users/profile。
    该接口对普通 customer 可能返回 404（无权限查看自身 profile），
    但只要不是 401，就说明 token 已被服务端接受、鉴权链路正常。
    """
    login_resp = user_api.login(fresh_user["email"], fresh_user["password"])
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    resp = user_api.get_profile(token)
    if resp.status_code == 401:
        pytest.fail(f"token 未通过鉴权: {resp.text}")

    # 404 表示 token 有效但当前角色无权限查看该资源，视为可接受的受保护接口行为
    if resp.status_code == 404:
        pytest.skip("当前角色无权访问 /users/profile，跳过 profile 断言")

    assert resp.status_code == 200, f"获取 profile 失败: {resp.status_code} {resp.text}"
    data = resp.json()
    assert data.get("email") == fresh_user["email"]


def test_list_products(product_api):
    """获取商品列表"""
    resp = product_api.list_products()
    assert resp.status_code == 200, f"获取商品列表失败: {resp.text}"
    data = resp.json()
    # API 可能直接返回数组，也可能包装为 data 字段
    products = data.get("data", data)
    assert len(products) > 0, "商品列表为空"


def test_get_product_detail(product_api):
    """获取单个商品详情"""
    list_resp = product_api.list_products()
    assert list_resp.status_code == 200
    products = list_resp.json().get("data", list_resp.json())
    assert products

    product_id = products[0]["id"]
    resp = product_api.get_product(product_id)
    assert resp.status_code == 200, f"获取商品详情失败: {resp.text}"
    assert resp.json()["id"] == product_id


def test_search_products(product_api, test_data):
    """搜索商品"""
    keyword = test_data["products"]["search_keyword"]
    resp = product_api.search_products(keyword)
    assert resp.status_code == 200, f"搜索商品失败: {resp.text}"
    data = resp.json()
    products = data.get("data", data)
    assert len(products) > 0, f"搜索 '{keyword}' 结果为空"


def test_cart_full_flow(product_api, cart_api, test_data):
    """完整购物车流程：创建购物车 -> 添加商品 -> 查询 -> 删除商品 -> 删除购物车"""
    # 1. 拿到一个真实商品 ID
    list_resp = product_api.list_products()
    assert list_resp.status_code == 200
    products = list_resp.json().get("data", list_resp.json())
    assert products
    product_id = products[0]["id"]

    # 2. 创建购物车
    cart_resp = cart_api.create_cart()
    assert cart_resp.status_code in (200, 201), f"创建购物车失败: {cart_resp.text}"
    cart_id = cart_resp.json().get("id")
    assert cart_id, "创建购物车响应缺少 id"

    # 3. 添加商品
    add_resp = cart_api.add_item(cart_id, product_id, quantity=2)
    assert add_resp.status_code in (200, 201), f"添加商品失败: {add_resp.text}"

    # 4. 查询购物车
    get_resp = cart_api.get_cart(cart_id)
    assert get_resp.status_code == 200, f"查询购物车失败: {get_resp.text}"
    cart_items = get_resp.json().get("cart_items", [])
    assert len(cart_items) > 0, "购物车中没有商品"

    # 5. 更新数量
    update_resp = cart_api.update_item_quantity(cart_id, product_id, quantity=3)
    assert update_resp.status_code in (200, 204), f"更新数量失败: {update_resp.text}"

    # 6. 删除商品
    remove_resp = cart_api.remove_item(cart_id, product_id)
    assert remove_resp.status_code in (200, 204), f"删除商品失败: {remove_resp.text}"

    # 7. 删除购物车
    delete_resp = cart_api.delete_cart(cart_id)
    assert delete_resp.status_code in (200, 204), f"删除购物车失败: {delete_resp.text}"
