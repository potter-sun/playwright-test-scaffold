# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Page Analyzer
# ═══════════════════════════════════════════════════════════════
"""
页面分析器 - 自动分析页面结构和元素
使用Playwright获取页面快照，识别可交互元素
"""

from playwright.sync_api import sync_playwright, Page
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from utils.logger import get_logger
from utils.config import ConfigManager
import json
import re

logger = get_logger(__name__)


@dataclass
class PageElement:
    """页面元素"""
    selector: str
    tag: str
    type: str  # input, button, link, select, etc.
    text: str = ""
    placeholder: str = ""
    name: str = ""
    id: str = ""
    role: str = ""
    required: bool = False
    disabled: bool = False
    attributes: Dict[str, str] = field(default_factory=dict)


@dataclass
class PageInfo:
    """页面信息"""
    url: str
    title: str
    page_type: str  # LOGIN, FORM, LIST, DETAIL, DASHBOARD, SETTINGS
    elements: List[PageElement] = field(default_factory=list)
    forms: List[Dict] = field(default_factory=list)
    navigation: List[Dict] = field(default_factory=list)


class PageAnalyzer:
    """
    页面分析器
    
    自动分析页面结构，识别：
    - 输入框（text, email, password, number等）
    - 按钮（submit, button, link-button）
    - 链接（导航、操作）
    - 表单结构
    - 页面类型
    
    使用方式:
        analyzer = PageAnalyzer()
        page_info = analyzer.analyze("https://example.com/login")
        print(page_info.page_type)  # LOGIN
        print(page_info.elements)   # [PageElement(...), ...]
    """
    
    # 页面类型识别规则
    PAGE_TYPE_RULES = {
        "LOGIN": {
            "url_patterns": [r"/login", r"/signin", r"/auth"],
            "element_patterns": ["input[type='password']", "button:has-text('Login')", "button:has-text('Sign in')"],
        },
        "REGISTER": {
            "url_patterns": [r"/register", r"/signup", r"/join"],
            "element_patterns": ["input[type='password']", "button:has-text('Register')", "button:has-text('Sign up')"],
        },
        "FORM": {
            "url_patterns": [r"/edit", r"/create", r"/new", r"/add"],
            "element_patterns": ["form", "input", "textarea", "select"],
        },
        "LIST": {
            "url_patterns": [r"/list", r"/index", r"/all"],
            "element_patterns": ["table", "[role='grid']", ".pagination", ".list-item"],
        },
        "DETAIL": {
            "url_patterns": [r"/view", r"/detail", r"/show", r"/\d+$"],
            "element_patterns": [".detail", ".view", "button:has-text('Edit')"],
        },
        "DASHBOARD": {
            "url_patterns": [r"/dashboard", r"/home", r"/overview"],
            "element_patterns": [".card", ".widget", ".chart", ".stats"],
        },
        "SETTINGS": {
            "url_patterns": [r"/settings", r"/profile", r"/preferences", r"/config"],
            "element_patterns": ["input", "select", "button:has-text('Save')"],
        },
    }
    
    def __init__(self):
        """初始化分析器"""
        self.config = ConfigManager()
    
    def analyze(self, url: str, auth_callback: callable = None) -> PageInfo:
        """
        分析页面
        
        Args:
            url: 页面URL
            auth_callback: 认证回调函数（如果页面需要登录）
            
        Returns:
            PageInfo: 页面信息
        """
        logger.info(f"开始分析页面: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True
            )
            page = context.new_page()
            
            try:
                # 如果需要认证
                if auth_callback:
                    auth_callback(page)
                
                # 导航到页面
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
                
                # 分析页面
                page_info = self._analyze_page(page, url)
                
                logger.info(f"页面分析完成: {page_info.page_type}")
                return page_info
                
            finally:
                browser.close()
    
    def _analyze_page(self, page: Page, url: str) -> PageInfo:
        """
        分析页面内容
        
        Args:
            page: Playwright页面对象
            url: 页面URL
            
        Returns:
            PageInfo: 页面信息
        """
        title = page.title()
        
        # 识别页面类型
        page_type = self._detect_page_type(page, url)
        
        # 获取元素
        elements = self._get_elements(page)
        
        # 获取表单信息
        forms = self._get_forms(page)
        
        # 获取导航信息
        navigation = self._get_navigation(page)
        
        return PageInfo(
            url=url,
            title=title,
            page_type=page_type,
            elements=elements,
            forms=forms,
            navigation=navigation
        )
    
    def _detect_page_type(self, page: Page, url: str) -> str:
        """
        识别页面类型
        
        Args:
            page: Playwright页面对象
            url: 页面URL
            
        Returns:
            str: 页面类型
        """
        scores = {page_type: 0 for page_type in self.PAGE_TYPE_RULES}
        
        for page_type, rules in self.PAGE_TYPE_RULES.items():
            # URL匹配
            for pattern in rules["url_patterns"]:
                if re.search(pattern, url, re.IGNORECASE):
                    scores[page_type] += 2
            
            # 元素匹配
            for selector in rules["element_patterns"]:
                try:
                    if page.locator(selector).count() > 0:
                        scores[page_type] += 1
                except:
                    pass
        
        # 返回得分最高的类型
        best_type = max(scores, key=scores.get)
        return best_type if scores[best_type] > 0 else "FORM"
    
    def _get_elements(self, page: Page) -> List[PageElement]:
        """
        获取页面元素
        
        Args:
            page: Playwright页面对象
            
        Returns:
            List[PageElement]: 元素列表
        """
        elements = []
        
        # 获取输入框
        inputs = self._get_inputs(page)
        elements.extend(inputs)
        
        # 获取按钮
        buttons = self._get_buttons(page)
        elements.extend(buttons)
        
        # 获取链接
        links = self._get_links(page)
        elements.extend(links)
        
        # 获取下拉框
        selects = self._get_selects(page)
        elements.extend(selects)
        
        return elements
    
    def _get_inputs(self, page: Page) -> List[PageElement]:
        """获取输入框元素"""
        elements = []
        
        # 各种输入类型
        input_types = [
            "input[type='text']",
            "input[type='email']",
            "input[type='password']",
            "input[type='number']",
            "input[type='tel']",
            "input[type='url']",
            "input[type='search']",
            "input:not([type])",
            "textarea",
        ]
        
        for selector in input_types:
            try:
                locators = page.locator(selector).all()
                for i, loc in enumerate(locators):
                    try:
                        element = self._extract_element_info(loc, "input")
                        if element:
                            elements.append(element)
                    except:
                        pass
            except:
                pass
        
        return elements
    
    def _get_buttons(self, page: Page) -> List[PageElement]:
        """获取按钮元素"""
        elements = []
        
        button_selectors = [
            "button",
            "input[type='submit']",
            "input[type='button']",
            "[role='button']",
        ]
        
        for selector in button_selectors:
            try:
                locators = page.locator(selector).all()
                for loc in locators:
                    try:
                        element = self._extract_element_info(loc, "button")
                        if element:
                            elements.append(element)
                    except:
                        pass
            except:
                pass
        
        return elements
    
    def _get_links(self, page: Page) -> List[PageElement]:
        """获取链接元素"""
        elements = []
        
        try:
            locators = page.locator("a[href]").all()
            for loc in locators:
                try:
                    element = self._extract_element_info(loc, "link")
                    if element:
                        elements.append(element)
                except:
                    pass
        except:
            pass
        
        return elements
    
    def _get_selects(self, page: Page) -> List[PageElement]:
        """获取下拉框元素"""
        elements = []
        
        try:
            locators = page.locator("select").all()
            for loc in locators:
                try:
                    element = self._extract_element_info(loc, "select")
                    if element:
                        elements.append(element)
                except:
                    pass
        except:
            pass
        
        return elements
    
    def _extract_element_info(self, locator, element_type: str) -> Optional[PageElement]:
        """
        提取元素信息
        
        Args:
            locator: Playwright定位器
            element_type: 元素类型
            
        Returns:
            PageElement: 元素信息
        """
        try:
            tag = locator.evaluate("el => el.tagName.toLowerCase()")
            
            # 获取选择器
            element_id = locator.get_attribute("id") or ""
            element_name = locator.get_attribute("name") or ""
            element_class = locator.get_attribute("class") or ""
            
            # 构建选择器
            if element_id:
                selector = f"#{element_id}"
            elif element_name:
                selector = f"[name='{element_name}']"
            elif element_class:
                first_class = element_class.split()[0] if element_class else ""
                selector = f"{tag}.{first_class}" if first_class else tag
            else:
                selector = tag
            
            return PageElement(
                selector=selector,
                tag=tag,
                type=element_type,
                text=locator.text_content() or "",
                placeholder=locator.get_attribute("placeholder") or "",
                name=element_name,
                id=element_id,
                role=locator.get_attribute("role") or "",
                required=locator.get_attribute("required") is not None,
                disabled=locator.get_attribute("disabled") is not None,
                attributes={
                    "type": locator.get_attribute("type") or "",
                    "maxlength": locator.get_attribute("maxlength") or "",
                    "pattern": locator.get_attribute("pattern") or "",
                }
            )
        except Exception as e:
            logger.debug(f"提取元素信息失败: {e}")
            return None
    
    def _get_forms(self, page: Page) -> List[Dict]:
        """获取表单信息"""
        forms = []
        
        try:
            form_locators = page.locator("form").all()
            for form_loc in form_locators:
                try:
                    form_info = {
                        "id": form_loc.get_attribute("id") or "",
                        "action": form_loc.get_attribute("action") or "",
                        "method": form_loc.get_attribute("method") or "GET",
                        "inputs": [],
                    }
                    
                    # 获取表单内的输入框
                    inputs = form_loc.locator("input, textarea, select").all()
                    for inp in inputs:
                        form_info["inputs"].append({
                            "name": inp.get_attribute("name") or "",
                            "type": inp.get_attribute("type") or "text",
                            "required": inp.get_attribute("required") is not None,
                        })
                    
                    forms.append(form_info)
                except:
                    pass
        except:
            pass
        
        return forms
    
    def _get_navigation(self, page: Page) -> List[Dict]:
        """获取导航信息"""
        navigation = []
        
        nav_selectors = ["nav a", "header a", ".navbar a", ".menu a", ".nav a"]
        
        for selector in nav_selectors:
            try:
                links = page.locator(selector).all()
                for link in links:
                    try:
                        nav_item = {
                            "text": link.text_content() or "",
                            "href": link.get_attribute("href") or "",
                        }
                        if nav_item["text"] and nav_item["href"]:
                            navigation.append(nav_item)
                    except:
                        pass
            except:
                pass
        
        return navigation
    
    def to_dict(self, page_info: PageInfo) -> Dict:
        """转换为字典"""
        return {
            "url": page_info.url,
            "title": page_info.title,
            "page_type": page_info.page_type,
            "elements": [asdict(e) for e in page_info.elements],
            "forms": page_info.forms,
            "navigation": page_info.navigation,
        }
    
    def to_json(self, page_info: PageInfo, file_path: str = None) -> str:
        """
        转换为JSON
        
        Args:
            page_info: 页面信息
            file_path: 保存路径（可选）
            
        Returns:
            str: JSON字符串
        """
        data = self.to_dict(page_info)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"页面分析结果已保存: {file_path}")
        
        return json_str

