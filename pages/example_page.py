# ═══════════════════════════════════════════════════════════════
# Example Page Object
# ═══════════════════════════════════════════════════════════════
"""
示例 Page Object
展示如何创建自定义的 Page Object
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ExamplePage(BasePage):
    """
    示例页面对象
    
    展示 Page Object 的标准结构和最佳实践
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS - 元素选择器
    # ═══════════════════════════════════════════════════════════════
    
    # 输入框
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    EMAIL_INPUT = "input[type='email']"
    
    # 按钮
    LOGIN_BUTTON = "button[type='submit']"
    CANCEL_BUTTON = "button:has-text('Cancel')"
    
    # 文本
    PAGE_TITLE = "h1"
    ERROR_MESSAGE = ".error-message"
    SUCCESS_MESSAGE = ".success-message"
    
    # 页面URL
    URL = "/example"
    
    # 页面加载指示器
    page_loaded_indicator = "h1"
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION - 导航方法
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到示例页面"""
        logger.info("导航到示例页面")
        self.goto(self.URL)
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        """
        检查页面是否加载完成
        
        Returns:
            bool: 页面是否已加载
        """
        try:
            return self.is_visible(self.PAGE_TITLE, timeout=5000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # INPUT ACTIONS - 输入操作
    # ═══════════════════════════════════════════════════════════════
    
    def fill_username(self, username: str) -> None:
        """
        填写用户名
        
        Args:
            username: 用户名
        """
        logger.info(f"填写用户名: {username}")
        self.fill(self.USERNAME_INPUT, username)
    
    def fill_password(self, password: str) -> None:
        """
        填写密码
        
        Args:
            password: 密码
        """
        logger.info("填写密码: ***")
        self.fill(self.PASSWORD_INPUT, password)
    
    def fill_email(self, email: str) -> None:
        """
        填写邮箱
        
        Args:
            email: 邮箱地址
        """
        logger.info(f"填写邮箱: {email}")
        self.fill(self.EMAIL_INPUT, email)
    
    # ═══════════════════════════════════════════════════════════════
    # BUTTON ACTIONS - 按钮操作
    # ═══════════════════════════════════════════════════════════════
    
    def click_login(self) -> None:
        """点击登录按钮"""
        logger.info("点击登录按钮")
        self.click(self.LOGIN_BUTTON)
    
    def click_cancel(self) -> None:
        """点击取消按钮"""
        logger.info("点击取消按钮")
        self.click(self.CANCEL_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # COMPOSITE ACTIONS - 组合操作
    # ═══════════════════════════════════════════════════════════════
    
    def login(self, username: str, password: str) -> None:
        """
        执行登录操作
        
        Args:
            username: 用户名
            password: 密码
        """
        logger.info(f"执行登录: {username}")
        self.fill_username(username)
        self.fill_password(password)
        self.click_login()
    
    # ═══════════════════════════════════════════════════════════════
    # GETTERS - 获取信息
    # ═══════════════════════════════════════════════════════════════
    
    def get_page_title(self) -> str:
        """
        获取页面标题
        
        Returns:
            str: 页面标题文本
        """
        return self.get_text(self.PAGE_TITLE)
    
    def get_error_message(self) -> str:
        """
        获取错误消息
        
        Returns:
            str: 错误消息文本
        """
        if self.is_visible(self.ERROR_MESSAGE, timeout=2000):
            return self.get_text(self.ERROR_MESSAGE)
        return ""
    
    def get_success_message(self) -> str:
        """
        获取成功消息
        
        Returns:
            str: 成功消息文本
        """
        if self.is_visible(self.SUCCESS_MESSAGE, timeout=2000):
            return self.get_text(self.SUCCESS_MESSAGE)
        return ""
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION - 验证方法
    # ═══════════════════════════════════════════════════════════════
    
    def is_error_displayed(self) -> bool:
        """
        检查是否显示错误消息
        
        Returns:
            bool: 是否显示错误
        """
        return self.is_visible(self.ERROR_MESSAGE, timeout=2000)
    
    def is_success_displayed(self) -> bool:
        """
        检查是否显示成功消息
        
        Returns:
            bool: 是否显示成功
        """
        return self.is_visible(self.SUCCESS_MESSAGE, timeout=2000)

