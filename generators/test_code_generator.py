# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Code Generator
# ═══════════════════════════════════════════════════════════════
"""
测试代码生成器 - 根据页面分析结果生成可执行的测试代码

生成物：
- Page Object 类
- 测试用例类
- 测试数据文件
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
        """生成测试用例代码"""
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

运行命令:
    pytest tests/test_{file_name}.py -v
    pytest tests/test_{file_name}.py -v -m P0
"""

import pytest
import allure
from playwright.sync_api import Page
from pages.{file_name}_page import {class_name}Page
from utils.logger import TestLogger

logger = TestLogger("test_{file_name}")


@allure.feature("{class_name}")
class Test{class_name}:
    """
    {class_name} 页面测试类
    """
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """测试 setup"""
        self.page = page
        self.{file_name}_page = {class_name}Page(page)
    
    # ═══════════════════════════════════════════════════════════════
    # P0 TESTS - 核心功能
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P0
    @pytest.mark.functional
    @allure.story("页面加载")
    @allure.title("TC-{tc}-001: 页面加载验证")
    def test_p0_page_load(self):
        """TC-{tc}-001: 页面加载验证"""
        logger.start()
        
        logger.step("导航到页面", "Navigation")
        self.{file_name}_page.navigate()
        self.{file_name}_page.take_screenshot("tc_{tc.lower()}_001_initial")
        
        logger.step("验证页面加载", "Verification")
        is_loaded = self.{file_name}_page.is_loaded()
        logger.checkpoint("页面加载完成", is_loaded)
        assert is_loaded, "页面未能正常加载"
        
        title = self.{file_name}_page.get_title()
        logger.checkpoint(f"页面标题: {{title}}", bool(title))
        
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
    def test_p1_boundary_values(self):
        """TC-{tc}-101: 边界值测试"""
        logger.start()
        self.{file_name}_page.navigate()
        # TODO: 测试边界值
        logger.end(success=True)
    
    @pytest.mark.P1
    @pytest.mark.validation
    @allure.story("输入验证")
    @allure.title("TC-{tc}-102: 特殊字符测试")
    def test_p1_special_characters(self):
        """TC-{tc}-102: 特殊字符测试"""
        logger.start()
        self.{file_name}_page.navigate()
        # TODO: 测试特殊字符
        logger.end(success=True)
    
    # ═══════════════════════════════════════════════════════════════
    # P2 TESTS - UI验证
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P2
    @pytest.mark.ui
    @allure.story("UI验证")
    @allure.title("TC-{tc}-201: UI样式验证")
    def test_p2_ui_styling(self):
        """TC-{tc}-201: UI样式验证"""
        logger.start()
        self.{file_name}_page.navigate()
        self.{file_name}_page.take_screenshot("tc_{tc.lower()}_201_ui", full_page=True)
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
    def test_p0_successful_login(self, test_account):
        """TC-{tc}-002: 正常登录流程"""
        logger.start()
        self.{fn}_page.navigate()
        # TODO: 填写凭证并登录
        logger.end(success=True)
    
    @pytest.mark.P0
    @pytest.mark.exception
    @allure.story("登录功能")
    @allure.title("TC-{tc}-003: 错误登录处理")
    def test_p0_invalid_login(self):
        """TC-{tc}-003: 错误登录处理"""
        logger.start()
        self.{fn}_page.navigate()
        # TODO: 测试无效凭证
        logger.end(success=True)
'''
    
    def _form_tests(self, tc: str, fn: str) -> str:
        return f'''
    @pytest.mark.P0
    @pytest.mark.functional
    @allure.story("表单提交")
    @allure.title("TC-{tc}-002: 表单提交成功")
    def test_p0_form_submit_success(self):
        """TC-{tc}-002: 表单提交成功"""
        logger.start()
        self.{fn}_page.navigate()
        # TODO: 填写表单并提交
        logger.end(success=True)
    
    @pytest.mark.P0
    @pytest.mark.validation
    @allure.story("表单验证")
    @allure.title("TC-{tc}-003: 必填字段验证")
    def test_p0_required_field_validation(self):
        """TC-{tc}-003: 必填字段验证"""
        logger.start()
        self.{fn}_page.navigate()
        has_error = self.{fn}_page.has_validation_error()
        logger.checkpoint("显示验证错误", has_error)
        logger.end(success=True)
'''
    
    def _save(self, file_path: Path, content: str) -> None:
        """保存文件"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"文件已生成: {file_path}")
