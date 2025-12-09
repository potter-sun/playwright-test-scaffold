# 🎭 Playwright Test Scaffold

> 通用的 Playwright 自动化测试脚手架 - 一键生成测试计划、测试代码和测试报告

## ✨ 特性

- 🔍 **自动页面分析** - 自动识别页面类型、元素、表单结构
- 📝 **测试计划生成** - 根据页面分析自动生成 Markdown 测试计划
- ⚡ **代码生成** - 自动生成 Page Object 和测试用例代码
- 🚀 **一键执行** - 分析 → 生成 → 测试 → 报告 全流程自动化
- 📊 **Allure 报告** - 美观的可视化测试报告
- 🔧 **高度可配置** - YAML 配置，支持多环境

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/playwright-test-scaffold.git
cd playwright-test-scaffold
```

### 2. 初始化环境

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
playwright install chromium
```

或使用 CLI 工具：

```bash
python cli.py init
```

### 3. 配置项目

编辑 `config/project.yaml`：

```yaml
project:
  name: "My Web App"
  
environments:
  default: "dev"
  dev:
    base_url: "http://localhost:3000"
    api_url: "http://localhost:8080/api"
```

### 4. 一键生成测试

```bash
# 完整流程：分析页面 → 生成测试计划 → 生成代码
python cli.py full --url https://example.com/login

# 生成后立即运行测试
python cli.py full --url https://example.com/login --run-tests
```

## 📖 使用指南

### CLI 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `init` | 初始化项目 | `python cli.py init` |
| `analyze` | 分析页面结构 | `python cli.py analyze --url https://example.com` |
| `plan` | 生成测试计划 | `python cli.py plan --url https://example.com` |
| `generate` | 生成测试代码 | `python cli.py generate --url https://example.com` |
| `run` | 运行测试 | `python cli.py run --tests tests/` |
| `report` | 查看 Allure 报告 | `python cli.py report` |
| `full` | 完整流程 | `python cli.py full --url https://example.com` |

### 分步执行

```bash
# 步骤1: 分析页面
python cli.py analyze --url https://example.com/login

# 步骤2: 生成测试计划
python cli.py plan --url https://example.com/login

# 步骤3: 生成测试代码
python cli.py generate --url https://example.com/login

# 步骤4: 运行测试
python cli.py run --tests tests/test_login.py

# 步骤5: 查看报告
python cli.py report
```

### 运行测试

```bash
# 运行所有测试
python cli.py run --tests tests/

# 只运行 P0 测试（核心功能）
python cli.py run --tests tests/ --markers P0

# 并行执行
python cli.py run --tests tests/ --parallel auto

# 显示浏览器窗口
python cli.py run --tests tests/ --headed

# 慢速执行（便于观察）
python cli.py run --tests tests/ --headed --slow
```

### 直接使用 pytest

```bash
# 基本运行
pytest tests/ -v

# 按优先级运行
pytest tests/ -v -m P0
pytest tests/ -v -m "P0 or P1"

# 并行运行
pytest tests/ -v -n auto

# 生成 Allure 报告
pytest tests/ -v --alluredir=allure-results
allure serve allure-results
```

## 📁 项目结构

```
playwright-test-scaffold/
├── core/                     # 核心框架（不建议修改）
│   ├── base_page.py         # 页面基类
│   ├── page_utils.py        # 页面工具
│   └── fixtures.py          # pytest fixtures
│
├── utils/                    # 工具模块
│   ├── logger.py            # 日志系统
│   └── config.py            # 配置管理
│
├── generators/               # 代码生成器
│   ├── page_analyzer.py     # 页面分析器
│   ├── test_plan_generator.py   # 测试计划生成
│   └── test_code_generator.py   # 代码生成
│
├── pages/                    # Page Objects（自动生成/手动编写）
│   └── login_page.py        # 示例
│
├── tests/                    # 测试用例（自动生成/手动编写）
│   └── test_login.py        # 示例
│
├── test-data/               # 测试数据
│   └── login_data.json      # 示例
│
├── config/                   # 配置文件
│   └── project.yaml         # 项目配置
│
├── docs/                     # 文档
│   └── test-plans/          # 测试计划
│
├── reports/                  # 测试报告（自动生成）
├── screenshots/              # 截图（自动生成）
├── allure-results/          # Allure 数据（自动生成）
│
├── cli.py                   # CLI 工具
├── conftest.py              # pytest 配置
├── pytest.ini               # pytest 配置
├── requirements.txt         # 依赖
└── README.md               # 本文档
```

## 🔧 自定义开发

### 创建 Page Object

```python
# pages/my_page.py
from core.base_page import BasePage


class MyPage(BasePage):
    """我的页面"""
    
    # 选择器
    TITLE = "h1"
    SUBMIT_BUTTON = "button[type='submit']"
    
    # 页面加载指示器
    page_loaded_indicator = "h1"
    
    def navigate(self):
        self.goto("/my-page")
    
    def is_loaded(self):
        return self.is_visible(self.TITLE)
    
    def click_submit(self):
        self.click(self.SUBMIT_BUTTON)
```

### 创建测试用例

```python
# tests/test_my_page.py
import pytest
from pages.my_page import MyPage


class TestMyPage:
    
    @pytest.fixture(autouse=True)
    def setup(self, page):
        self.page = MyPage(page)
    
    @pytest.mark.P0
    def test_page_load(self):
        """P0: 页面加载测试"""
        self.page.navigate()
        assert self.page.is_loaded()
    
    @pytest.mark.P1
    def test_submit(self):
        """P1: 提交测试"""
        self.page.navigate()
        self.page.click_submit()
        # 验证...
```

### 测试数据

```json
// test-data/my_page_data.json
{
  "valid_data": {
    "username": "testuser",
    "email": "test@example.com"
  },
  "invalid_data": {
    "username": "",
    "email": "invalid"
  }
}
```

## ⚙️ 配置说明

### 环境配置

```yaml
# config/project.yaml
environments:
  default: "dev"
  
  dev:
    base_url: "http://localhost:3000"
    api_url: "http://localhost:8080"
  
  staging:
    base_url: "https://staging.example.com"
    api_url: "https://staging-api.example.com"
  
  production:
    base_url: "https://www.example.com"
    api_url: "https://api.example.com"
```

### 切换环境

```bash
# 方式1: 环境变量
export TEST_ENV=staging
python cli.py run --tests tests/

# 方式2: 命令行
TEST_ENV=staging python cli.py run --tests tests/
```

### 浏览器配置

```yaml
browser:
  headless: true      # 无头模式
  slow_mo: 0          # 操作延迟（毫秒）
  timeout: 30000      # 默认超时
  viewport:
    width: 1920
    height: 1080
```

## 📊 测试报告

### Allure 报告

```bash
# 运行测试（生成 allure-results）
pytest tests/ -v --alluredir=allure-results

# 查看报告
allure serve allure-results

# 或生成静态报告
allure generate allure-results -o allure-report --clean
```

### HTML 报告

```bash
pytest tests/ -v --html=reports/report.html
```

## 🏷️ 测试标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.P0` | 核心功能测试（必须通过） |
| `@pytest.mark.P1` | 重要功能测试 |
| `@pytest.mark.P2` | 一般功能测试 |
| `@pytest.mark.functional` | 功能测试 |
| `@pytest.mark.validation` | 验证测试 |
| `@pytest.mark.boundary` | 边界测试 |
| `@pytest.mark.exception` | 异常测试 |
| `@pytest.mark.security` | 安全测试 |
| `@pytest.mark.ui` | UI 测试 |

## 🛠️ 自定义生成器

如需修改自动生成的测试计划或测试代码，请编辑 `generators/` 目录下的文件：

### 修改测试计划

编辑 `generators/test_plan_generator.py`：

| 修改需求 | 修改位置 |
|----------|----------|
| 添加/修改测试维度 | `TEST_DIMENSIONS` 字典 |
| 修改优先级规则 | `PRIORITY_RULES` 字典 |
| 修改P0测试模板 | `_generate_p0_tests()` 方法 |
| 修改P1测试模板 | `_generate_p1_tests()` 方法 |
| 修改P2测试模板 | `_generate_p2_tests()` 方法 |
| 添加新测试类型 | 新增 `_generate_xxx_tests()` 方法 |
| 修改测试数据结构 | `_generate_test_data()` 方法 |

### 修改测试代码

编辑 `generators/test_code_generator.py`：

| 修改需求 | 修改位置 |
|----------|----------|
| 修改 Page Object 结构 | `generate_page_object()` 方法 |
| 修改测试类结构 | `generate_test_cases()` 方法 |
| 修改测试方法模板 | `_generate_test_methods()` 方法 |
| 修改测试数据格式 | `generate_test_data()` 方法 |
| 修改选择器生成 | `_generate_selectors()` 方法 |
| 修改操作方法生成 | `_generate_methods()` 方法 |

### 修改页面识别

编辑 `generators/page_analyzer.py`：

| 修改需求 | 修改位置 |
|----------|----------|
| 添加新页面类型 | `PAGE_TYPE_RULES` 字典 |
| 修改元素识别规则 | `_get_inputs()` / `_get_buttons()` 等方法 |

### 快速修改示例

```python
# generators/test_plan_generator.py

# 1. 添加新页面类型的测试维度
TEST_DIMENSIONS = {
    ...
    "PAYMENT": ["functional", "security", "transaction"],  # 新增
}

# 2. 添加新测试类型方法
def _generate_security_tests(self, page_info) -> List[str]:
    """生成安全测试用例"""
    # 返回测试用例列表
    pass
```

## 🤝 贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

MIT License

---

**Happy Testing! 🎭**

