class InvoiceApi:
    """订单/发票相关 API 封装"""

    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url

    def create_invoice(self, payload, token=None):
        """
        创建订单/发票
        payload 示例：
        {
          "billing_address": "Street 1",
          "billing_city": "City",
          "billing_country": "Netherlands",
          "billing_postcode": "1234AA",
          "billing_state": "State",
          "cart_id": "...",
          "comment": "",
          "payment": "cash-on-delivery",
          "shipping_address": "Street 1",
          "shipping_city": "City",
          "shipping_country": "Netherlands",
          "shipping_postcode": "1234AA",
          "shipping_state": "State"
        }
        """
        url = f"{self.base_url}/invoices"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self.session.post(url, json=payload, headers=headers)

    def list_invoices(self, token, page=None):
        """获取发票列表（需要登录）"""
        url = f"{self.base_url}/invoices"
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if page is not None:
            params["page"] = page
        return self.session.get(url, headers=headers, params=params)

    def get_invoice(self, invoice_id, token):
        """获取发票详情"""
        url = f"{self.base_url}/invoices/{invoice_id}"
        headers = {"Authorization": f"Bearer {token}"}
        return self.session.get(url, headers=headers)
