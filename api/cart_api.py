class CartApi:
    """购物车相关 API 封装"""

    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url

    def create_cart(self):
        """创建购物车"""
        url = f"{self.base_url}/carts"
        return self.session.post(url)

    def add_item(self, cart_id, product_id, quantity):
        """向购物车添加商品"""
        url = f"{self.base_url}/carts/{cart_id}"
        payload = {
            "product_id": product_id,
            "quantity": quantity
        }
        return self.session.post(url, json=payload)

    def update_item_quantity(self, cart_id, product_id, quantity):
        """更新购物车中某商品数量"""
        url = f"{self.base_url}/carts/{cart_id}/product/quantity"
        payload = {
            "product_id": product_id,
            "quantity": quantity
        }
        return self.session.put(url, json=payload)

    def remove_item(self, cart_id, product_id):
        """从购物车删除商品"""
        url = f"{self.base_url}/carts/{cart_id}/product/{product_id}"
        return self.session.delete(url)

    def get_cart(self, cart_id):
        """获取购物车详情"""
        url = f"{self.base_url}/carts/{cart_id}"
        return self.session.get(url)

    def delete_cart(self, cart_id):
        """删除购物车"""
        url = f"{self.base_url}/carts/{cart_id}"
        return self.session.delete(url)
