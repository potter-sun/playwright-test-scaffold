# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Code Generator
# ═══════════════════════════════════════════════════════════════
"""
测试代码生成器 - 根据页面分析结果生成可执行的测试代码

生成物：
- Page Object 类（带 Allure 步骤截图）
- 测试用例类（带描述/步骤/预期目标）
- 测试数据文件

Allure 报告增强：
- @allure.description() - 测试描述
- with allure.step() - 关键步骤（自动前后截图）
- allure.attach() - 预期目标附件
"""

from typing import Dict
from pathlib import Path
from datetime import datetime
import json

from generators.page_analyzer import PageInfo, PageElement
from generators.utils import (
    to_snake_case,
    to_class_name,
    get_page_name_from_url,
    get_file_name_from_url,
    get_tc_prefix_from_url,
    extract_url_path,
    get_element_constant_name,
    get_element_comment,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class TestCodeGenerator:
    """
    测试代码生成器
    
    使用方式:
        generator = TestCodeGenerator()
        generator.generate_all(page_info, output_dir=".")
    """
    
    def generate_all(self, page_info: PageInfo, output_dir: str = ".") -> Dict[str, str]:
        """生成所有文件"""
        output = Path(output_dir)
        files = {}
        file_name = get_file_name_from_url(page_info.url)
        
        # Page Object
        page_code = self.generate_page_object(page_info)
        page_file = output / "pages" / f"{file_name}_page.py"
        self._save(page_file, page_code)
        files["page_object"] = str(page_file)
        
        # Test Cases
        test_code = self.generate_test_cases(page_info)
        test_file = output / "tests" / f"test_{file_name}.py"
        self._save(test_file, test_code)
        files["test_cases"] = str(test_file)
        
        # Test Data
        test_data = self.generate_test_data(page_info)
        data_file = output / "test-data" / f"{file_name}_data.json"
        self._save(data_file, json.dumps(test_data, indent=2, ensure_ascii=False))
        files["test_data"] = str(data_file)
        
        logger.info(f"代码生成完成: {len(files)} 个文件")
        return files
    
    # ═══════════════════════════════════════════════════════════════
    # PAGE OBJECT GENERATOR
    # ═══════════════════════════════════════════════════════════════
    
    def generate_page_object(self, page_info: PageInfo) -> str:
        """生成 Page Object 代码"""
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        url_path = extract_url_path(page_info.url)
        indicator = page_info.elements[0].selector if page_info.elements else "body"
        
        selectors = self._gen_selectors(page_info)
        methods = self._gen_methods(page_info)
        
        return f'''# ═══════════════════════════════════════════════════════════════
# {class_name} Page Object
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════
"""
{class_name} 页面对象
URL: {page_info.url}
Type: {page_info.page_type}
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class {class_name}Page(BasePage):
    """
    {class_name} 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
{selectors}
    
    URL = "{url_path}"
    page_loaded_indicator = "{indicator}"
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 {class_name} 页面")
        self.goto(self.URL)
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=5000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════
{methods}
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
'''
    
    # ═══════════════════════════════════════════════════════════════
    # TEST CASES GENERATOR
    # ═══════════════════════════════════════════════════════════════
    
    def generate_test_cases(self, page_info: PageInfo) -> str:
        """生成测试用例代码 - 集成 Allure 报告增强"""
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        file_name = get_file_name_from_url(page_info.url)
        tc = get_tc_prefix_from_url(page_info.url)
        
        # 类型特定测试
        type_tests = self._gen_type_tests(page_info, tc, file_name)
        
        return f'''# ═══════════════════════════════════════════════════════════════
# {class_name} Test Cases
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════
"""
{class_name} 页面测试用例

Allure 报告增强:
- 测试描述: @allure.description()
- 步骤追踪: with allure.step() + 关键步骤前后截图
- 预期目标: allure.attach() 附件

运行命令:
    pytest tests/test_{file_name}.py -v
    pytest tests/test_{file_name}.py -v -m P0
    pytest tests/test_{file_name}.py --alluredir=allure-results && allure serve allure-results
"""

import pytest
import allure
from playwright.sync_api import Page
from pages.{file_name}_page import {class_name}Page
from utils.logger import TestLogger

logger = TestLogger("test_{file_name}")


# ═══════════════════════════════════════════════════════════════
# ALLURE REPORT HELPERS
# ═══════════════════════════════════════════════════════════════

def attach_expected(expectations: list[str]) -> None:
    \"\"\"附加预期目标到 Allure 报告\"\"\"
    content = "\\n".join(f"✓ {{exp}}" for exp in expectations)
    allure.attach(content, name="预期目标", attachment_type=allure.attachment_type.TEXT)


@allure.feature("{class_name}")
class Test{class_name}:
    \"\"\"
    {class_name} 页面测试类
    
    测试覆盖:
    - P0: 核心功能 (页面加载、主流程)
    - P1: 输入验证 (边界值、特殊字符)
    - P2: UI验证 (样式、布局)
    \"\"\"
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        \"\"\"测试 setup\"\"\"
        self.page = page
        self.{file_name}_page = {class_name}Page(page)
    
    # ═══════════════════════════════════════════════════════════════
    # P0 TESTS - 核心功能
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P0
    @pytest.mark.functional
    @allure.story("页面加载")
    @allure.title("TC-{tc}-001: 页面加载验证")
    @allure.description(\"\"\"
    **测试目的**: 验证页面能正常加载，核心元素正确显示
    
    **前置条件**: 
    - 系统正常运行
    - 网络连接正常
    
    **测试步骤**:
    1. 导航到 {class_name} 页面
    2. 等待页面加载完成
    3. 验证页面标题和核心元素
    \"\"\")
    def test_p0_page_load(self):
        \"\"\"TC-{tc}-001: 页面加载验证\"\"\"
        logger.start()
        
        # 附加预期目标
        attach_expected([
            "页面在 3 秒内加载完成",
            "页面标题正确显示",
            "核心元素可见"
        ])
        
        with allure.step("Step 1: 导航到页面"):
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_001_before_navigate")
            self.{file_name}_page.navigate()
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_001_after_navigate")
        
        with allure.step("Step 2: 验证页面加载状态"):
            is_loaded = self.{file_name}_page.is_loaded()
            logger.checkpoint("页面加载完成", is_loaded)
            assert is_loaded, "页面未能正常加载"
        
        with allure.step("Step 3: 验证页面标题"):
            title = self.{file_name}_page.get_title()
            logger.checkpoint(f"页面标题: {{title}}", bool(title))
            assert title, "页面标题为空"
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_001_loaded")
        
        logger.end(success=True)
{type_tests}
    # ═══════════════════════════════════════════════════════════════
    # P1 TESTS - 输入验证
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P1
    @pytest.mark.validation
    @allure.story("输入验证")
    @allure.title("TC-{tc}-101: 边界值测试")
    @allure.description(\"\"\"
    **测试目的**: 验证输入字段的边界值处理
    
    **测试数据**:
    - 最小长度值
    - 最大长度值
    - 空值
    \"\"\")
    def test_p1_boundary_values(self):
        \"\"\"TC-{tc}-101: 边界值测试\"\"\"
        logger.start()
        
        attach_expected([
            "最小长度输入被接受",
            "最大长度输入被接受",
            "空值显示验证错误"
        ])
        
        with allure.step("Step 1: 导航到页面"):
            self.{file_name}_page.navigate()
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_101_initial")
        
        with allure.step("Step 2: 测试边界值"):
            # TODO: 实现边界值测试
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_101_boundary")
        
        logger.end(success=True)
    
    @pytest.mark.P1
    @pytest.mark.validation
    @allure.story("输入验证")
    @allure.title("TC-{tc}-102: 特殊字符测试")
    @allure.description(\"\"\"
    **测试目的**: 验证输入字段对特殊字符的处理
    
    **测试数据**:
    - SQL 注入字符: ' OR 1=1 --
    - XSS 字符: <script>alert(1)</script>
    - Unicode 字符: 中文、emoji
    \"\"\")
    def test_p1_special_characters(self):
        \"\"\"TC-{tc}-102: 特殊字符测试\"\"\"
        logger.start()
        
        attach_expected([
            "特殊字符被正确转义",
            "不触发 XSS/SQL 注入",
            "Unicode 字符正常显示"
        ])
        
        with allure.step("Step 1: 导航到页面"):
            self.{file_name}_page.navigate()
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_102_initial")
        
        with allure.step("Step 2: 测试特殊字符"):
            # TODO: 实现特殊字符测试
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_102_special")
        
        logger.end(success=True)
    
    # ═══════════════════════════════════════════════════════════════
    # P2 TESTS - UI验证
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P2
    @pytest.mark.ui
    @allure.story("UI验证")
    @allure.title("TC-{tc}-201: UI样式验证")
    @allure.description(\"\"\"
    **测试目的**: 验证页面 UI 样式和布局
    
    **检查项**:
    - 元素对齐和间距
    - 颜色和字体
    - 响应式布局
    \"\"\")
    def test_p2_ui_styling(self):
        \"\"\"TC-{tc}-201: UI样式验证\"\"\"
        logger.start()
        
        attach_expected([
            "布局正确，元素对齐",
            "样式符合设计规范",
            "响应式适配正常"
        ])
        
        with allure.step("Step 1: 导航到页面"):
            self.{file_name}_page.navigate()
        
        with allure.step("Step 2: 截取全页截图"):
            self.{file_name}_page.take_screenshot("tc_{tc.lower()}_201_fullpage", full_page=True)
        
        logger.end(success=True)
'''
    
    # ═══════════════════════════════════════════════════════════════
    # TEST DATA GENERATOR
    # ═══════════════════════════════════════════════════════════════
    
    def generate_test_data(self, page_info: PageInfo) -> Dict:
        """生成测试数据"""
        data = {
            "page_info": {"url": page_info.url, "type": page_info.page_type},
            "valid_data": {},
            "invalid_data": {},
            "boundary_data": {},
        }
        
        for elem in page_info.elements:
            if elem.type != "input":
                continue
            
            field = elem.name or elem.id or "field"
            input_type = elem.attributes.get("type", "text")
            
            type_data = {
                "email": {
                    "valid": "test@example.com",
                    "invalid": "invalid-email",
                    "boundary": {"min": "a@b.c", "max": "a" * 50 + "@example.com"},
                },
                "password": {
                    "valid": "ValidPass123!",
                    "invalid": "123",
                    "boundary": {"min": "a", "max": "a" * 100},
                },
                "tel": {
                    "valid": "13800138000",
                    "invalid": "abc",
                    "boundary": {"min": "1", "max": "1" * 20},
                },
                "number": {
                    "valid": "100",
                    "invalid": "abc",
                    "boundary": {"min": "0", "max": "999999999", "negative": "-1"},
                },
            }
            
            default = {
                "valid": "test_value",
                "invalid": "",
                "boundary": {"empty": "", "min": "a", "max": "x" * 256, "special": "@#$%^&*()"},
            }
            
            field_data = type_data.get(input_type, default)
            data["valid_data"][field] = field_data["valid"]
            data["invalid_data"][field] = field_data["invalid"]
            data["boundary_data"][field] = field_data["boundary"]
        
        return data
    
    # ═══════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _gen_selectors(self, page_info: PageInfo) -> str:
        """生成选择器代码"""
        lines = []
        for elem in page_info.elements:
            const = get_element_constant_name(elem)
            comment = get_element_comment(elem)
            lines.append(f"    # {comment}")
            lines.append(f'    {const} = "{elem.selector}"')
            lines.append("")
        return "\n".join(lines) if lines else "    pass"
    
    def _gen_methods(self, page_info: PageInfo) -> str:
        """生成操作方法代码"""
        methods = []
        
        for elem in page_info.elements:
            const = get_element_constant_name(elem)
            
            if elem.type == "input":
                methods.append(self._input_method(elem, const))
            elif elem.type == "button":
                methods.append(self._button_method(elem, const))
            elif elem.type == "select":
                methods.append(self._select_method(elem, const))
        
        return "\n".join(methods) if methods else "\n    pass"
    
    def _input_method(self, elem: PageElement, const: str) -> str:
        name = to_snake_case(elem.name or elem.id or "input")
        desc = elem.placeholder or elem.name or "input"
        return f'''
    def fill_{name}(self, value: str) -> None:
        """填写 {desc}"""
        logger.info(f"填写 {desc}: {{value}}")
        self.fill(self.{const}, value)
    
    def get_{name}_value(self) -> str:
        """获取 {desc} 的值"""
        return self.get_input_value(self.{const})'''
    
    def _button_method(self, elem: PageElement, const: str) -> str:
        text = (elem.text or "button").strip()
        name = to_snake_case(text)
        return f'''
    def click_{name}(self) -> None:
        """点击 {text} 按钮"""
        logger.info("点击 {text} 按钮")
        self.click(self.{const})'''
    
    def _select_method(self, elem: PageElement, const: str) -> str:
        name = to_snake_case(elem.name or elem.id or "option")
        desc = elem.name or "option"
        return f'''
    def select_{name}(self, value: str) -> None:
        """选择 {desc}"""
        logger.info(f"选择 {desc}: {{value}}")
        self.select_option(self.{const}, value)'''
    
    def _gen_type_tests(self, page_info: PageInfo, tc: str, file_name: str) -> str:
        """生成页面类型特定测试"""
        if page_info.page_type == "LOGIN":
            return self._login_tests(tc, file_name)
        elif page_info.page_type == "FORM":
            return self._form_tests(tc, file_name)
        return ""
    
    def _login_tests(self, tc: str, fn: str) -> str:
        return f'''
    @pytest.mark.P0
    @pytest.mark.functional
    @allure.story("登录功能")
    @allure.title("TC-{tc}-002: 正常登录流程")
    @allure.description(\"\"\"
    **测试目的**: 验证使用有效凭证能成功登录
    
    **前置条件**:
    - 有效的测试账号
    - 账号状态正常
    
    **测试步骤**:
    1. 导航到登录页面
    2. 输入有效用户名和密码
    3. 点击登录按钮
    4. 验证登录成功跳转
    \"\"\")
    def test_p0_successful_login(self, test_account):
        \"\"\"TC-{tc}-002: 正常登录流程\"\"\"
        logger.start()
        
        attach_expected([
            "登录表单正确显示",
            "输入凭证后点击登录",
            "成功跳转到目标页面",
            "Session 正确建立"
        ])
        
        with allure.step("Step 1: 导航到登录页面"):
            self.{fn}_page.navigate()
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_002_initial")
        
        with allure.step("Step 2: 填写登录凭证"):
            # TODO: 实现登录凭证填写
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_002_filled")
        
        with allure.step("Step 3: 点击登录按钮"):
            # TODO: 实现点击登录
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_002_after_click")
        
        with allure.step("Step 4: 验证登录结果"):
            # TODO: 验证跳转和 Session
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_002_result")
        
        logger.end(success=True)
    
    @pytest.mark.P0
    @pytest.mark.exception
    @allure.story("登录功能")
    @allure.title("TC-{tc}-003: 错误登录处理")
    @allure.description(\"\"\"
    **测试目的**: 验证使用无效凭证登录时的错误处理
    
    **测试场景**:
    - 错误密码
    - 不存在的用户名
    - 账号被锁定
    
    **测试步骤**:
    1. 导航到登录页面
    2. 输入无效凭证
    3. 点击登录按钮
    4. 验证错误提示
    \"\"\")
    def test_p0_invalid_login(self):
        \"\"\"TC-{tc}-003: 错误登录处理\"\"\"
        logger.start()
        
        attach_expected([
            "显示错误提示信息",
            "不跳转到登录后页面",
            "允许重新输入"
        ])
        
        with allure.step("Step 1: 导航到登录页面"):
            self.{fn}_page.navigate()
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_003_initial")
        
        with allure.step("Step 2: 输入无效凭证"):
            # TODO: 实现无效凭证输入
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_003_invalid_input")
        
        with allure.step("Step 3: 点击登录并验证错误"):
            # TODO: 点击登录，验证错误提示
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_003_error_shown")
        
        logger.end(success=True)
'''
    
    def _form_tests(self, tc: str, fn: str) -> str:
        return f'''
    @pytest.mark.P0
    @pytest.mark.functional
    @allure.story("表单提交")
    @allure.title("TC-{tc}-002: 表单提交成功")
    @allure.description(\"\"\"
    **测试目的**: 验证填写有效数据后表单能成功提交
    
    **前置条件**:
    - 页面正常加载
    - 有效的测试数据
    
    **测试步骤**:
    1. 导航到表单页面
    2. 填写所有必填字段
    3. 点击提交按钮
    4. 验证提交结果
    \"\"\")
    def test_p0_form_submit_success(self):
        \"\"\"TC-{tc}-002: 表单提交成功\"\"\"
        logger.start()
        
        attach_expected([
            "表单正确显示所有字段",
            "填写数据后无验证错误",
            "提交成功，数据保存",
            "显示成功提示或跳转"
        ])
        
        with allure.step("Step 1: 导航到表单页面"):
            self.{fn}_page.navigate()
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_002_initial")
        
        with allure.step("Step 2: 填写表单字段"):
            # TODO: 实现表单填写
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_002_filled")
        
        with allure.step("Step 3: 提交表单"):
            # TODO: 实现表单提交
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_002_before_submit")
        
        with allure.step("Step 4: 验证提交结果"):
            # TODO: 验证提交成功
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_002_result")
        
        logger.end(success=True)
    
    @pytest.mark.P0
    @pytest.mark.validation
    @allure.story("表单验证")
    @allure.title("TC-{tc}-003: 必填字段验证")
    @allure.description(\"\"\"
    **测试目的**: 验证未填必填字段时的验证提示
    
    **测试场景**:
    - 所有字段为空直接提交
    - 部分必填字段为空
    
    **测试步骤**:
    1. 导航到表单页面
    2. 不填写任何内容直接提交
    3. 验证错误提示显示
    \"\"\")
    def test_p0_required_field_validation(self):
        \"\"\"TC-{tc}-003: 必填字段验证\"\"\"
        logger.start()
        
        attach_expected([
            "必填字段显示验证错误",
            "阻止表单提交",
            "错误提示清晰可读"
        ])
        
        with allure.step("Step 1: 导航到表单页面"):
            self.{fn}_page.navigate()
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_003_initial")
        
        with allure.step("Step 2: 直接提交空表单"):
            # TODO: 点击提交按钮
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_003_before_submit")
        
        with allure.step("Step 3: 验证错误提示"):
            has_error = self.{fn}_page.has_validation_error()
            logger.checkpoint("显示验证错误", has_error)
            self.{fn}_page.take_screenshot("tc_{tc.lower()}_003_error_shown")
            assert has_error, "未显示验证错误"
        
        logger.end(success=True)
'''
    
    def _save(self, file_path: Path, content: str) -> None:
        """保存文件"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"文件已生成: {file_path}")
