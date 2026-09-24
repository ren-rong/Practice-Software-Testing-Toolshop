"""结账页 PO：填地址、选支付方式、提交订单。"""
import re


class CheckoutPage:
    def __init__(self, page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

        # 地址表单字段
        self.address = page.locator("input[formcontrolname='address']")
        self.city = page.locator("input[formcontrolname='city']")
        self.state = page.locator("input[formcontrolname='state']")
        self.country = page.locator("input[formcontrolname='country']")
        self.postcode = page.locator("input[formcontrolname='postcode']")
        # 下一步 / 提交按钮
        self.next_button = page.get_by_role("button", name=re.compile("next|continue", re.I))
        self.confirm_button = page.get_by_role("button", name=re.compile("complete|confirm|submit order", re.I))

    def fill_address(self, address: str, city: str, state: str,
                     country: str, postcode: str):
        self.address.fill(address)
        self.city.fill(city)
        self.state.fill(state)
        self.country.fill(country)
        self.postcode.fill(postcode)
        return self

    def go_next(self):
        self.next_button.click()
        return self

    def confirm_order(self):
        self.confirm_button.click()
        return self

    def order_success_visible(self) -> bool:
        return self.page.get_by_text(re.compile("thank you|order.*success|success", re.I)) \
                   .first.is_visible(timeout=5000)
