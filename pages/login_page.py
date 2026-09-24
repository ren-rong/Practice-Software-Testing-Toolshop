"""登录页 PO：/auth/login。"""
import re


class LoginPage:
    def __init__(self, page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

        self.email_input = page.locator("input[type='email'], input[formcontrolname='email']")
        self.password_input = page.locator("input[type='password']")
        self.login_button = page.get_by_role("button", name=re.compile("^login$", re.I))
        # 登录失败的报错提示
        self.error_alert = page.locator(".alert-danger, [role='alert']")

    def load(self):
        self.page.goto(f"{self.base_url}/auth/login", wait_until="domcontentloaded", timeout=60000)
        return self

    def open(self):
        """兼容命名：与 HomePage/ProductPage/CartPage 保持统一。"""
        return self.load()

    def login(self, email: str, password: str):
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.login_button.click()
        return self

    def error_text(self) -> str:
        try:
            return self.error_alert.text_content(timeout=2000) or ""
        except Exception:
            return ""

    def is_logged_in(self) -> bool:
        """登录成功后右上角会出现用户菜单 / Logout 链接。"""
        return self.page.get_by_text(re.compile("logout", re.I)).is_visible(timeout=3000)

    def expect_login_success(self):
        """断言登录成功：URL 已离开登录页，或出现 Logout/Sign out 入口。"""
        from playwright.sync_api import expect
        # 优先判断 URL 已跳转，这是最可靠的登录成功信号
        expect(self.page).not_to_have_url(re.compile(r".*/auth/login.*"), timeout=10000)
        # 若仍能看到 logout/sign out 则进一步确认
        try:
            logout_visible = self.page.get_by_text(re.compile("logout|sign out", re.I)).first.is_visible(timeout=2000)
            if logout_visible:
                return
        except Exception:
            pass
