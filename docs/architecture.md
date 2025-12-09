# Playwright Test Scaffold - Architecture

> 架构文档 - 记录系统设计决策与模块职责

## 目录结构

```
playwright-test-scaffold/
├── cli.py                        # 命令行入口
├── conftest.py                   # pytest 根配置
├── pytest.ini                    # pytest 配置
├── requirements.txt              # 依赖清单
│
├── config/
│   └── project.yaml              # 项目配置 (环境/浏览器/账号)
│
├── core/                         # 核心框架层 (稳定，不建议修改)
│   ├── __init__.py
│   ├── base_page.py              # Page Object 基类 - 模板方法模式
│   ├── fixtures.py               # pytest fixtures - 浏览器/页面/环境
│   └── page_utils.py             # 页面工具函数
│
├── generators/                   # 代码生成引擎
│   ├── __init__.py
│   ├── utils.py                  # 🆕 公共工具 - 命名转换/元素提取
│   ├── page_analyzer.py          # 页面分析器 - Playwright 快照分析
│   ├── test_plan_generator.py    # 测试计划生成 - Markdown 文档
│   └── test_code_generator.py    # 代码生成 - Page Object + Tests
│
├── pages/                        # Page Object 实现层 (自动生成/手动编写)
│   ├── __init__.py
│   └── example_page.py
│
├── tests/                        # 测试用例层 (自动生成/手动编写)
│   ├── __init__.py
│   └── test_example.py
│
├── test-data/                    # 测试数据 (JSON)
│   └── example_data.json
│
├── utils/                        # 工具模块
│   ├── __init__.py
│   ├── config.py                 # 配置管理器 - 单例，YAML + ENV
│   └── logger.py                 # 日志系统
│
├── docs/                         # 文档
│   ├── architecture.md           # 本文档
│   └── test-plans/               # 生成的测试计划
│
├── reports/                      # 测试报告 (自动生成)
├── screenshots/                  # 截图 (自动生成)
└── allure-results/               # Allure 数据 (自动生成)
```

## 模块职责

### `generators/utils.py` (公共工具)

提取自 `test_plan_generator.py` 和 `test_code_generator.py` 的重复代码。

| 函数 | 职责 |
|------|------|
| `to_snake_case()` | 转换为蛇形命名 |
| `to_class_name()` | 转换为 PascalCase |
| `to_constant_name()` | 转换为 CONSTANT_CASE |
| `get_page_name_from_url()` | 从 URL 提取页面名称 |
| `get_file_name_from_url()` | 从 URL 提取文件名 |
| `get_tc_prefix_from_url()` | 生成测试用例前缀 |
| `get_element_name()` | 获取元素显示名称 |
| `get_element_constant_name()` | 获取元素常量名 |
| `get_element_description()` | 获取元素描述 |

### `generators/page_analyzer.py` (页面分析器)

- 使用 Playwright 获取页面快照
- 自动识别页面类型 (LOGIN, FORM, LIST...)
- 提取可交互元素 (input, button, link, select)
- 输出 `PageInfo` 数据结构

### `generators/test_plan_generator.py` (测试计划生成)

- 输入: `PageInfo`
- 输出: Markdown 格式测试计划
- 包含: 页面概述、元素映射、P0/P1/P2 测试用例、测试数据设计

### `generators/test_code_generator.py` (代码生成)

- 输入: `PageInfo`
- 输出: 
  - `pages/{name}_page.py` - Page Object 类
  - `tests/test_{name}.py` - pytest 测试用例
  - `test-data/{name}_data.json` - 测试数据

### `core/base_page.py` (Page Object 基类)

- 模板方法模式
- 强制子类实现 `navigate()` 和 `is_loaded()`
- 提供统一操作接口: `click()`, `fill()`, `is_visible()`...

### `utils/config.py` (配置管理)

- 单例模式
- 配置优先级: 环境变量 > YAML > 默认值
- 支持点号语法: `config.get("browser.viewport.width")`

## 设计原则

1. **DRY** - 公共逻辑提取到 `generators/utils.py`
2. **单一职责** - 每个模块只做一件事
3. **开闭原则** - 新增页面类型无需修改核心代码
4. **模板方法** - `BasePage` 定义骨架，子类实现细节

## 变更日志

| 日期 | 变更 |
|------|------|
| 2025-12-09 | 创建 `generators/utils.py`，重构生成器消除代码重复 |
| 2025-12-09 | `test_plan_generator.py`: 607行 → ~280行 |
| 2025-12-09 | `test_code_generator.py`: 755行 → ~320行 |
