"""
商品 / 购物车域接口封装
  - GET  /products             商品列表（支持分页、分类、搜索）
  - GET  /products/{id}        商品详情
  - GET  /categories           分类列表
  - GET  /brands               品牌列表
  - POST /carts                创建空购物车，返回 {id}
  - POST /carts/{id}/items     加购：{product_id, quantity}
  - GET  /carts/{id}           查询购物车明细
  - DELETE /carts/{id}/items/{item_id}   删除购物车里的某一行
"""


class ProductApi:
    """商品与购物车相关 API 封装"""

    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url

    # ---------- 商品 ----------
    def list_products(self, page: int = 1, per_page: int = 12,
                      category: str = None, search: str = None):
        params = {"page": page, "per_page": per_page}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        url = f"{self.base_url}/products"
        return self.session.get(url, params=params)

    def search_products(self, keyword: str, page: int = 1, per_page: int = 12):
        """按关键字搜索商品，等价于 list_products(search=keyword)。"""
        return self.list_products(page=page, per_page=per_page, search=keyword)

    def get_product(self, product_id: str):
        url = f"{self.base_url}/products/{product_id}"
        return self.session.get(url)

    def categories(self):
        url = f"{self.base_url}/categories"
        return self.session.get(url)

    def brands(self):
        url = f"{self.base_url}/brands"
        return self.session.get(url)

    # ---------- 购物车 ----------
    def create_cart(self):
        """创建一个空购物车，返回体里带 id。"""
        url = f"{self.base_url}/carts"
        return self.session.post(url)

    def add_to_cart(self, cart_id: str, product_id: str, quantity: int = 1):
        url = f"{self.base_url}/carts/{cart_id}/items"
        payload = {"product_id": product_id, "quantity": quantity}
        return self.session.post(url, json=payload)

    def get_cart(self, cart_id: str):
        url = f"{self.base_url}/carts/{cart_id}"
        return self.session.get(url)

    def remove_cart_item(self, cart_id: str, item_id: str):
        url = f"{self.base_url}/carts/{cart_id}/items/{item_id}"
        return self.session.delete(url)
