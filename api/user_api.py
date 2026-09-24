class UserApi:
    """用户相关 API 封装"""

    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url

    def register(self, first_name, last_name, email, password,
                 address="Street 1", city="City", state="State",
                 country="Country", postcode="1234AA", phone="1234567890",
                 dob="1970-01-01"):
        """
        用户注册
        默认账号格式参考：https://practicesoftwaretesting.com
        注意：该接口要求 address 字段为数组，元素包含完整地址。
        """
        url = f"{self.base_url}/users/register"

        # 支持调用方直接传入地址数组或字符串；字符串时自动包装为数组
        if isinstance(address, list):
            address_payload = address
        else:
            address_payload = [
                {
                    "street": address,
                    "city": city,
                    "state": state,
                    "country": country,
                    "postal_code": postcode,
                }
            ]

        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "password_confirmation": password,
            "address": address_payload,
            "phone": phone,
            "dob": dob,
        }
        return self.session.post(url, json=payload)

    def login(self, email, password):
        """用户登录，返回 access_token / refresh_token"""
        url = f"{self.base_url}/users/login"
        payload = {
            "email": email,
            "password": password
        }
        return self.session.post(url, json=payload)

    def get_profile(self, token=None):
        """获取当前登录用户信息"""
        url = f"{self.base_url}/users/profile"
        headers = self._auth_header(token)
        return self.session.get(url, headers=headers)

    def forgot_password(self, email):
        """忘记密码"""
        url = f"{self.base_url}/users/forgot-password"
        return self.session.post(url, json={"email": email})

    def _auth_header(self, token):
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
