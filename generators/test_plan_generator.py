# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Plan Generator
# ═══════════════════════════════════════════════════════════════
"""
测试计划生成器 - 根据页面分析结果生成 Markdown 测试计划
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
        """Page Object 骨架代码"""
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

```python
from core.base_page import BasePage

class {class_name}Page(BasePage):
    \"\"\"
    {page_name} 页面对象
    URL: {page_info.url}
    Type: {page_info.page_type}
    \"\"\"
    
    # SELECTORS
{selectors_code}
    
    page_loaded_indicator = "{indicator}"
    
    # NAVIGATION
    def navigate(self) -> None:
        self.goto("{page_info.url}")
    
    def is_loaded(self) -> bool:
        return self.is_visible(self.page_loaded_indicator)
    
    # ACTIONS
{methods}
```"""
    
    def _notes(self, page_info: PageInfo) -> str:
        """实施说明"""
        file_name = to_snake_case(get_page_name_from_url(page_info.url))
        auth = "No" if not requires_auth(page_info.page_type) else "Yes (likely)"
        
        return f"""## 6. Implementation Notes

### 6.1 File Locations
- **Page Object**: `pages/{file_name}_page.py`
- **Test File**: `tests/test_{file_name}.py`
- **Test Data**: `test-data/{file_name}_data.json`

### 6.2 Execution Commands
```bash
pytest tests/test_{file_name}.py -v
pytest tests/test_{file_name}.py -v -m P0
pytest tests/test_{file_name}.py --alluredir=allure-results
```

### 6.3 Dependencies
- Requires authentication: {auth}

---
*Generated by Playwright Test Scaffold*"""
    
    # ═══════════════════════════════════════════════════════════════
    # TEST CASE GENERATORS
    # ═══════════════════════════════════════════════════════════════
    
    def _p0_tests(self, page_info: PageInfo) -> List[str]:
        """P0 核心测试用例"""
        tests = []
        tc = get_tc_prefix_from_url(page_info.url)
        
        # 通用：页面加载测试
        tests.append(f"""
#### TC-{tc}-001: 页面加载验证

- **Priority**: P0
- **Type**: functional
- **Steps**:
  1. 导航到页面: `{page_info.url}`
  2. 等待页面加载完成
  3. 验证页面核心元素显示
- **Expected**:
  - [ ] 页面标题正确: "{page_info.title}"
  - [ ] 核心元素可见
  - [ ] 页面加载时间 < 3秒""")
        
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
        """P1 重要测试用例"""
        tests = []
        tc = get_tc_prefix_from_url(page_info.url)
        inputs = [e for e in page_info.elements if e.type == "input"]
        
        for i, elem in enumerate(inputs, 1):
            name = get_element_name(elem)
            tests.append(f"""
#### TC-{tc}-1{i:02d}: {name} 输入验证

- **Priority**: P1
- **Type**: validation
- **Element**: `{elem.selector}`
- **Test Data**:
  - 空值 / 正常值 / 边界值 / 特殊字符
- **Expected**:
  - [ ] 验证提示正确
  - [ ] 正常值可提交""")
        
        return tests
    
    def _p2_tests(self, page_info: PageInfo) -> List[str]:
        """P2 一般测试用例"""
        tc = get_tc_prefix_from_url(page_info.url)
        
        return [f"""
#### TC-{tc}-201: UI样式验证

- **Priority**: P2
- **Type**: ui
- **Expected**: 布局正确，响应式适配

#### TC-{tc}-202: 键盘导航测试

- **Priority**: P2
- **Type**: accessibility
- **Expected**: Tab顺序正确，焦点可见"""]
    
    # ═══════════════════════════════════════════════════════════════
    # PAGE TYPE SPECIFIC TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def _login_p0(self, tc: str) -> str:
        return f"""
#### TC-{tc}-002: 正常登录流程

- **Priority**: P0
- **Type**: functional
- **Steps**: 输入有效凭证 → 点击登录 → 验证跳转
- **Expected**: 成功跳转，Session 建立

#### TC-{tc}-003: 错误登录处理

- **Priority**: P0
- **Type**: exception
- **Steps**: 输入无效凭证 → 点击登录
- **Expected**: 显示错误提示，不跳转"""
    
    def _form_p0(self, tc: str) -> str:
        return f"""
#### TC-{tc}-002: 表单提交成功

- **Priority**: P0
- **Type**: functional
- **Steps**: 填写必填字段 → 提交
- **Expected**: 提交成功，数据保存

#### TC-{tc}-003: 必填字段验证

- **Priority**: P0
- **Type**: validation
- **Steps**: 不填必填字段 → 提交
- **Expected**: 显示错误，阻止提交"""
    
    def _list_p0(self, tc: str) -> str:
        return f"""
#### TC-{tc}-002: 列表数据加载

- **Priority**: P0
- **Type**: functional
- **Expected**: 数据正确显示，分页信息正确

#### TC-{tc}-003: 分页功能

- **Priority**: P0
- **Type**: functional
- **Expected**: 分页切换正确，URL 参数同步"""
    
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
