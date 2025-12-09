# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Plan Generator
# ═══════════════════════════════════════════════════════════════
"""
测试计划生成器 - 根据页面分析结果生成 Markdown 测试计划

增强功能:
- 测试描述: 测试目的、前置条件
- 测试步骤: 带截图时机标记
- 预期目标: 结构化的验收标准
"""

from typing import List
from pathlib import Path
from datetime import datetime
import json

from generators.page_analyzer import PageInfo, PageElement
from generators.utils import (
    to_snake_case,
    to_class_name,
    get_page_name_from_url,
    get_tc_prefix_from_url,
    get_element_name,
    get_element_constant_name,
    get_element_description,
    get_page_description,
    requires_auth,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class TestPlanGenerator:
    """
    测试计划生成器
    
    根据页面分析结果自动生成 Markdown 测试计划文档
    
    使用方式:
        generator = TestPlanGenerator()
        test_plan = generator.generate(page_info)
        generator.save(test_plan, "docs/test-plans/login.md")
    """
    
    # 页面类型对应的测试维度
    TEST_DIMENSIONS = {
        "LOGIN": ["functional", "security", "boundary", "exception", "ui"],
        "REGISTER": ["functional", "validation", "boundary", "exception", "ui"],
        "FORM": ["functional", "validation", "boundary", "exception", "data"],
        "LIST": ["functional", "pagination", "filter", "performance", "ui"],
        "DETAIL": ["functional", "data", "navigation", "ui"],
        "DASHBOARD": ["functional", "data", "performance", "ui"],
        "SETTINGS": ["functional", "validation", "persistence", "ui"],
    }
    
    def generate(self, page_info: PageInfo) -> str:
        """生成测试计划"""
        logger.info(f"生成测试计划: {page_info.url}")
        
        sections = [
            self._header(page_info),
            self._overview(page_info),
            self._element_mapping(page_info),
            self._test_cases(page_info),
            self._test_data(page_info),
            self._page_object_skeleton(page_info),
            self._notes(page_info),
        ]
        
        return "\n\n".join(sections)
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION GENERATORS
    # ═══════════════════════════════════════════════════════════════
    
    def _header(self, page_info: PageInfo) -> str:
        """文档头部"""
        page_name = get_page_name_from_url(page_info.url)
        return f"""# {page_name} Test Plan

> 自动生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 页面类型: {page_info.page_type}
> 生成工具: Playwright Test Scaffold"""
    
    def _overview(self, page_info: PageInfo) -> str:
        """页面概述"""
        page_name = get_page_name_from_url(page_info.url)
        dimensions = self.TEST_DIMENSIONS.get(page_info.page_type, ["functional"])
        
        return f"""## 1. Page Overview

| Attribute | Value |
|-----------|-------|
| **Page Name** | {page_name} |
| **URL** | `{page_info.url}` |
| **Title** | {page_info.title} |
| **Type** | {page_info.page_type} |
| **Test Dimensions** | {', '.join(dimensions)} |

### 1.1 Page Description

{get_page_description(page_info.page_type)}"""
    
    def _element_mapping(self, page_info: PageInfo) -> str:
        """元素映射表"""
        rows = []
        for element in page_info.elements:
            name = get_element_name(element)
            desc = get_element_description(element)
            rows.append(f"| {name} | {desc} | `{element.selector}` | {element.type} |")
        
        table = "\n".join(rows) if rows else "| (No elements found) | - | - | - |"
        
        return f"""## 2. Element Mapping

| Element Name | Description | Selector | Type |
|--------------|-------------|----------|------|
{table}"""
    
    def _test_cases(self, page_info: PageInfo) -> str:
        """测试用例"""
        cases = []
        
        cases.append("### 3.1 P0 - Critical Tests (核心功能)")
        cases.extend(self._p0_tests(page_info))
        
        cases.append("\n### 3.2 P1 - High Priority Tests (重要功能)")
        cases.extend(self._p1_tests(page_info))
        
        cases.append("\n### 3.3 P2 - Medium Priority Tests (一般功能)")
        cases.extend(self._p2_tests(page_info))
        
        return f"""## 3. Test Cases

{chr(10).join(cases)}"""
    
    def _test_data(self, page_info: PageInfo) -> str:
        """测试数据设计"""
        inputs = [e for e in page_info.elements if e.type == "input"]
        
        valid, invalid, boundary = {}, {}, {}
        
        for elem in inputs:
            field = elem.name or elem.id or "field"
            attr_type = elem.attributes.get("type", "text")
            
            if attr_type == "email":
                valid[field] = "test@example.com"
                invalid[field] = "invalid-email"
                boundary[field] = "a@b.c"
            elif attr_type == "password":
                valid[field] = "ValidPass123!"
                invalid[field] = "123"
                boundary[field] = "a" * 100
            elif attr_type == "tel":
                valid[field] = "13800138000"
                invalid[field] = "abc"
                boundary[field] = "1" * 20
            else:
                valid[field] = "test_value"
                invalid[field] = ""
                boundary[field] = "x" * 256
        
        return f"""## 4. Test Data Design

### 4.1 Valid Data
```json
{json.dumps(valid, indent=2, ensure_ascii=False)}
```

### 4.2 Invalid Data
```json
{json.dumps(invalid, indent=2, ensure_ascii=False)}
```

### 4.3 Boundary Data
```json
{json.dumps(boundary, indent=2, ensure_ascii=False)}
```"""
    
    def _page_object_skeleton(self, page_info: PageInfo) -> str:
        """Page Object 骨架代码 - 带 Allure 集成"""
        page_name = get_page_name_from_url(page_info.url)
        class_name = to_class_name(page_name)
        
        # 选择器代码
        selectors = []
        for elem in page_info.elements:
            const = get_element_constant_name(elem)
            selectors.append(f'    {const} = "{elem.selector}"')
        selectors_code = "\n".join(selectors) if selectors else "    # No elements found"
        
        # 方法代码
        methods = self._page_methods(page_info)
        
        indicator = page_info.elements[0].selector if page_info.elements else "body"
        
        return f"""## 5. Page Object Skeleton

> **注意**: 此骨架已集成 Allure 报告支持，截图会自动附加到报告

```python
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class {class_name}Page(BasePage):
    \"\"\"
    {page_name} 页面对象
    URL: {page_info.url}
    Type: {page_info.page_type}
    
    Allure 集成:
    - take_screenshot() 自动附加截图到报告
    - 所有操作方法记录日志
    \"\"\"
    
    # SELECTORS
{selectors_code}
    
    page_loaded_indicator = "{indicator}"
    
    # NAVIGATION
    def navigate(self) -> None:
        \"\"\"导航到页面\"\"\"
        logger.info(f"导航到 {class_name} 页面")
        self.goto("{page_info.url}")
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        \"\"\"检查页面是否加载完成\"\"\"
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=5000)
        except Exception:
            return False
    
    # ACTIONS
{methods}
    
    # SCREENSHOT HELPERS (继承自 BasePage)
    # take_screenshot(name, full_page=False) - 截图并附加到 Allure 报告
```

### 5.1 Allure 步骤使用示例

```python
import allure

def test_example(self):
    # 附加预期目标
    attach_expected([
        "预期目标 1",
        "预期目标 2"
    ])
    
    # 使用 allure.step 包装关键步骤
    with allure.step("Step 1: 操作描述"):
        self.page.take_screenshot("step1_before")
        # 执行操作
        self.page.take_screenshot("step1_after")
    
    with allure.step("Step 2: 验证结果"):
        assert condition, "断言失败信息"
        self.page.take_screenshot("step2_result")
```"""
    
    def _notes(self, page_info: PageInfo) -> str:
        """实施说明 - 包含 Allure 报告指南"""
        file_name = to_snake_case(get_page_name_from_url(page_info.url))
        auth = "No" if not requires_auth(page_info.page_type) else "Yes (likely)"
        
        return f"""## 6. Implementation Notes

### 6.1 File Locations
| 文件类型 | 路径 |
|----------|------|
| Page Object | `pages/{file_name}_page.py` |
| Test File | `tests/test_{file_name}.py` |
| Test Data | `test-data/{file_name}_data.json` |
| Screenshots | `screenshots/tc_*` |

### 6.2 Execution Commands

```bash
# 运行测试
pytest tests/test_{file_name}.py -v

# 运行 P0 用例
pytest tests/test_{file_name}.py -v -m P0

# 生成 Allure 报告
pytest tests/test_{file_name}.py --alluredir=allure-results
allure serve allure-results
```

### 6.3 Allure 报告增强

生成的测试代码包含以下 Allure 特性:

| 特性 | 用途 |
|------|------|
| `@allure.description()` | 测试描述 (目的、前置条件) |
| `with allure.step()` | 步骤追踪 (支持嵌套) |
| `take_screenshot()` | 关键步骤截图 |
| `attach_expected()` | 预期目标附件 |

### 6.4 截图命名规范

```
tc_{{tc_prefix}}_{{case_number}}_{{timing}}.png

示例:
- tc_{file_name.lower()}_001_initial.png    # 初始状态
- tc_{file_name.lower()}_001_after_click.png # 点击后
- tc_{file_name.lower()}_001_result.png     # 最终结果
```

### 6.5 Dependencies
- Requires authentication: {auth}

---
*Generated by Playwright Test Scaffold - Enhanced Allure Report*"""
    
    # ═══════════════════════════════════════════════════════════════
    # TEST CASE GENERATORS
    # ═══════════════════════════════════════════════════════════════
    
    def _p0_tests(self, page_info: PageInfo) -> List[str]:
        """P0 核心测试用例 - 增强版"""
        tests = []
        tc = get_tc_prefix_from_url(page_info.url)
        
        # 通用：页面加载测试
        tests.append(f"""
#### TC-{tc}-001: 页面加载验证

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 页面加载 |

**测试描述**:
> 验证页面能正常加载，核心元素正确显示

**前置条件**:
- 系统正常运行
- 网络连接正常

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到页面: `{page_info.url}` | 📸 before_navigate |
| 2 | 等待页面加载完成 | 📸 after_navigate |
| 3 | 验证页面标题和核心元素 | 📸 loaded |

**预期目标**:
- [ ] ✓ 页面在 3 秒内加载完成
- [ ] ✓ 页面标题正确: "{page_info.title}"
- [ ] ✓ 核心元素可见""")
        
        # 页面类型特定测试
        type_tests = {
            "LOGIN": self._login_p0,
            "FORM": self._form_p0,
            "LIST": self._list_p0,
        }
        
        if page_info.page_type in type_tests:
            tests.append(type_tests[page_info.page_type](tc))
        
        return tests
    
    def _p1_tests(self, page_info: PageInfo) -> List[str]:
        """P1 重要测试用例 - 增强版"""
        tests = []
        tc = get_tc_prefix_from_url(page_info.url)
        inputs = [e for e in page_info.elements if e.type == "input"]
        
        for i, elem in enumerate(inputs, 1):
            name = get_element_name(elem)
            tests.append(f"""
#### TC-{tc}-1{i:02d}: {name} 输入验证

| 属性 | 值 |
|------|-----|
| **优先级** | P1 |
| **类型** | validation |
| **Allure Story** | 输入验证 |
| **元素选择器** | `{elem.selector}` |

**测试描述**:
> 验证 {name} 字段的输入验证逻辑

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到页面 | 📸 initial |
| 2 | 测试空值输入 | 📸 empty_input |
| 3 | 测试边界值输入 | 📸 boundary |
| 4 | 测试特殊字符输入 | 📸 special_chars |

**测试数据**:
- 空值: `""`
- 正常值: 有效数据
- 边界值: 最小/最大长度
- 特殊字符: `<script>`, `' OR 1=1`

**预期目标**:
- [ ] ✓ 空值显示必填验证
- [ ] ✓ 正常值可接受
- [ ] ✓ 边界值正确处理
- [ ] ✓ 特殊字符被正确转义""")
        
        return tests
    
    def _p2_tests(self, page_info: PageInfo) -> List[str]:
        """P2 一般测试用例 - 增强版"""
        tc = get_tc_prefix_from_url(page_info.url)
        
        return [f"""
#### TC-{tc}-201: UI样式验证

| 属性 | 值 |
|------|-----|
| **优先级** | P2 |
| **类型** | ui |
| **Allure Story** | UI验证 |

**测试描述**:
> 验证页面 UI 样式和布局符合设计规范

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到页面 | 📸 initial |
| 2 | 截取全页截图 | 📸 fullpage (full_page=True) |

**预期目标**:
- [ ] ✓ 布局正确，元素对齐
- [ ] ✓ 响应式适配正常
- [ ] ✓ 样式符合设计规范

#### TC-{tc}-202: 键盘导航测试

| 属性 | 值 |
|------|-----|
| **优先级** | P2 |
| **类型** | accessibility |
| **Allure Story** | 可访问性 |

**测试描述**:
> 验证页面支持键盘导航，符合可访问性标准

**测试步骤**:

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到页面 | 📸 initial |
| 2 | 按 Tab 键遍历元素 | 📸 focus_visible |

**预期目标**:
- [ ] ✓ Tab 顺序正确
- [ ] ✓ 焦点指示器可见
- [ ] ✓ 可通过 Enter 激活按钮"""]
    
    # ═══════════════════════════════════════════════════════════════
    # PAGE TYPE SPECIFIC TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def _login_p0(self, tc: str) -> str:
        return f"""
#### TC-{tc}-002: 正常登录流程

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 登录功能 |

**测试描述**:
> 验证使用有效凭证能成功登录系统

**前置条件**:
- 有效的测试账号
- 账号状态正常

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到登录页面 | 📸 initial |
| 2 | 填写用户名和密码 | 📸 filled |
| 3 | 点击登录按钮 | 📸 after_click |
| 4 | 验证登录结果 | 📸 result |

**预期目标**:
- [ ] ✓ 登录表单正确显示
- [ ] ✓ 输入凭证后无验证错误
- [ ] ✓ 成功跳转到目标页面
- [ ] ✓ Session 正确建立

#### TC-{tc}-003: 错误登录处理

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | exception |
| **Allure Story** | 登录功能 |

**测试描述**:
> 验证使用无效凭证登录时的错误处理

**测试场景**:
- 错误密码
- 不存在的用户名

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到登录页面 | 📸 initial |
| 2 | 输入无效凭证 | 📸 invalid_input |
| 3 | 点击登录并验证 | 📸 error_shown |

**预期目标**:
- [ ] ✓ 显示错误提示信息
- [ ] ✓ 不跳转到登录后页面
- [ ] ✓ 允许重新输入"""
    
    def _form_p0(self, tc: str) -> str:
        return f"""
#### TC-{tc}-002: 表单提交成功

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 表单提交 |

**测试描述**:
> 验证填写有效数据后表单能成功提交

**前置条件**:
- 页面正常加载
- 有效的测试数据

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到表单页面 | 📸 initial |
| 2 | 填写所有必填字段 | 📸 filled |
| 3 | 点击提交按钮 | 📸 before_submit |
| 4 | 验证提交结果 | 📸 result |

**预期目标**:
- [ ] ✓ 表单正确显示所有字段
- [ ] ✓ 填写数据后无验证错误
- [ ] ✓ 提交成功，数据保存
- [ ] ✓ 显示成功提示或跳转

#### TC-{tc}-003: 必填字段验证

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | validation |
| **Allure Story** | 表单验证 |

**测试描述**:
> 验证未填必填字段时的验证提示

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到表单页面 | 📸 initial |
| 2 | 直接点击提交 | 📸 before_submit |
| 3 | 验证错误提示 | 📸 error_shown |

**预期目标**:
- [ ] ✓ 必填字段显示验证错误
- [ ] ✓ 阻止表单提交
- [ ] ✓ 错误提示清晰可读"""
    
    def _list_p0(self, tc: str) -> str:
        return f"""
#### TC-{tc}-002: 列表数据加载

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 列表功能 |

**测试描述**:
> 验证列表页面数据正确加载和显示

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到列表页面 | 📸 initial |
| 2 | 等待数据加载 | 📸 data_loaded |

**预期目标**:
- [ ] ✓ 数据正确显示
- [ ] ✓ 分页信息正确
- [ ] ✓ 无空数据异常

#### TC-{tc}-003: 分页功能

| 属性 | 值 |
|------|-----|
| **优先级** | P0 |
| **类型** | functional |
| **Allure Story** | 列表功能 |

**测试描述**:
> 验证分页功能正常工作

**测试步骤** (带截图时机):

| 步骤 | 操作 | 截图 |
|------|------|------|
| 1 | 导航到列表页面 | 📸 page1 |
| 2 | 点击下一页 | 📸 page2 |
| 3 | 验证 URL 参数 | 📸 url_params |

**预期目标**:
- [ ] ✓ 分页切换正确
- [ ] ✓ URL 参数同步
- [ ] ✓ 数据内容正确更新"""
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _page_methods(self, page_info: PageInfo) -> str:
        """生成 Page Object 方法"""
        methods = []
        
        for elem in page_info.elements:
            const = get_element_constant_name(elem)
            
            if elem.type == "input":
                name = to_snake_case(elem.name or elem.id or "input")
                methods.append(f"""
    def fill_{name}(self, value: str) -> None:
        self.fill(self.{const}, value)""")
            
            elif elem.type == "button":
                text = to_snake_case(elem.text.strip() if elem.text else "button")
                methods.append(f"""
    def click_{text}(self) -> None:
        self.click(self.{const})""")
        
        return "\n".join(methods) if methods else "    pass"
    
    def save(self, content: str, file_path: str) -> None:
        """保存测试计划"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        logger.info(f"测试计划已保存: {file_path}")
