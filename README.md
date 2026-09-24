# Practice Software Testing (Toolshop) UI+API 自动化测试

[![Toolshop CI](https://github.com/ren-rong/Practice-Software-Testing-Toolshop/actions/workflows/toolshop-ci.yml/badge.svg)](https://github.com/ren-rong/Practice-Software-Testing-Toolshop/actions/workflows/toolshop-ci.yml)

面向测试开发工程师的实践项目，基于公共演示站点 [Practice Software Testing (Toolshop)](https://practicesoftwaretesting.com)，使用 **Python + pytest + requests + Playwright** 构建分层自动化测试体系（API / UI / 混合），并通过 **GitHub Actions** 实现持续集成。

---

## 项目简介

项目围绕 Toolshop 电商核心链路（用户、商品、购物车、下单），分别从接口层、界面层以及接口+界面混合三个维度进行自动化覆盖。每次 push / pull request 都会自动触发 CI，API 测试与 UI/混合测试并行执行。

- Web 前端：<https://practicesoftwaretesting.com>
- API 后端：<https://api.practicesoftwaretesting.com>
- Swagger 文档：<https://api.practicesoftwaretesting.com/api/documentation>

## 技术栈

- Python 3.11
- pytest
- requests（API 层）
- Playwright + pytest-playwright（UI 层）
- pytest-rerunfailures（失败自动重跑，抵御公共环境抖动）
- allure-pytest（测试报告，可选）
- GitHub Actions（持续集成）

## 项目结构

```
.
├── .github/workflows/toolshop-ci.yml  # GitHub Actions CI 工作流
├── conftest.py                        # 全局 fixtures（base_url、API 对象、Playwright 配置）
├── api/                               # API 接口封装层
│   ├── user_api.py                    #   注册 / 登录 / profile
│   ├── product_api.py                 #   商品 / 分类 / 购物车
│   ├── cart_api.py                    #   购物车增删改查
│   └── invoice_api.py                 #   订单 / 发票
├── pages/                             # UI 页面对象层（POM）
│   ├── home_page.py                   #   首页 / 搜索
│   ├── login_page.py                  #   登录
│   ├── product_page.py                #   商品详情 / 加购
│   ├── cart_page.py                   #   购物车
│   └── checkout_page.py               #   结账
├── tests/                             # 测试用例
│   ├── test_api.py                    #   API 用例（标记 api）
│   ├── test_ui_flow.py                #   UI 用例（标记 ui）
│   └── test_mixed.py                  #   混合用例（标记 mixed）
├── test_data/
│   └── data.yaml                      # 测试数据（地址、默认账号、搜索关键字）
├── pytest.ini
├── requirements.txt
└── README.md
```

## 测试覆盖

| 层级 | 文件 | 用例数 | 覆盖内容 |
|---|---|---|---|
| API | `tests/test_api.py` | 8 | 默认账号登录、注册新用户、新用户登录、鉴权访问 profile、商品列表、商品详情、商品搜索、购物车完整流程 |
| UI | `tests/test_ui_flow.py` | 4 | 首页加载、用户登录、搜索并打开详情、搜索加购并校验购物车 |
| 混合 | `tests/test_mixed.py` | 1 | API 取真实商品 → UI 搜索并校验展示 |

共 **13 条用例**（默认账号在公共环境被锁定等极少数情况下会安全跳过，不计为失败）。

## 快速开始

### 1. 创建虚拟环境并安装依赖

建议使用纯英文路径，避免中文路径导致 pip 编码问题：

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 安装 Playwright 浏览器

```bash
python -m playwright install chromium
```

### 3. 运行测试

```bash
# 全部用例
pytest -v

# 仅 API 用例（无需浏览器）
pytest -m api -v

# 仅 UI 用例
pytest -m ui -v

# UI + 混合用例
pytest -m "ui or mixed" -v
```

### 4. 生成 Allure 报告（可选）

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

## CI/CD 说明

`.github/workflows/toolshop-ci.yml` 包含两个并行任务：

1. **api-tests**：安装依赖 → 运行 `pytest -m api`；
2. **ui-tests**：安装依赖 → 安装 Chromium 及系统依赖 → 运行 `pytest -m "ui or mixed"`。

特性：

- 触发条件：push / pull request 到 `main`（或 `master`），也支持手动 `workflow_dispatch`；
- 运行环境：Ubuntu Latest + Python 3.11；
- 失败重跑：`--reruns 2`，避免公共演示站偶发抖动造成误报；
- 失败留证：UI 任务在失败时自动保留截图与 Playwright trace，并上传为 artifact。

### 关于 Cloudflare 安全质询

Toolshop 前端位于 Cloudflare 之后。在 GitHub Actions 的数据中心网络下，**Playwright 默认的 `HeadlessChrome` User-Agent 会触发 Cloudflare 托管质询**（HTTP 403，页面停留在 "Just a moment..."，Angular 应用不渲染），而 API 子域不受影响。

解决方案见 `conftest.py` 的 `browser_context_args`：统一使用不含 `HeadlessChrome` 标记的标准 Chrome UA，并设置 `locale` 与 `Accept-Language`，Cloudflare 边缘即直接放行（已在 CI 实测验证）。

> 说明：测试直接访问公共演示站点，其可用性与数据状态不由本项目控制。代码已对 5xx 做了重试、对默认账号锁定等情况做了安全跳过，以保证 CI 结果稳定可复现。
