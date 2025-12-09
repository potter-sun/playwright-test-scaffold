# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Pytest Fixtures
# ═══════════════════════════════════════════════════════════════
"""
通用测试fixtures - 提供测试所需的各种资源
"""

import pytest
import os
from pathlib import Path
from playwright.sync_api import Page, BrowserContext
from utils.config import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)
config = ConfigManager()


# ═══════════════════════════════════════════════════════════════
# BROWSER CONFIGURATION
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    配置浏览器上下文参数
    从config/project.yaml读取配置
    """
    browser_config = config.get_browser_config()
    
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "viewport": {
            "width": browser_config.get("viewport_width", 1920),
            "height": browser_config.get("viewport_height", 1080)
        },
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """
    配置浏览器启动参数
    从config/project.yaml读取配置
    """
    browser_config = config.get_browser_config()
    args = config.get("browser.args", [])
    
    return {
        **browser_type_launch_args,
        "headless": browser_config.get("headless", True),
        "slow_mo": browser_config.get("slow_mo", 0),
        "timeout": 60000,
        "args": args if args else [
            "--disable-web-security",
            "--ignore-certificate-errors",
            "--allow-insecure-localhost",
            "--disable-gpu",
            "--no-sandbox",
        ],
    }


# ═══════════════════════════════════════════════════════════════
# PAGE FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def test_page(page: Page) -> Page:
    """
    测试页面fixture - 每个测试独立的页面实例
    
    使用方式:
        def test_example(test_page):
            test_page.goto("https://example.com")
            assert test_page.title() == "Example"
    """
    logger.info(f"创建测试页面")
    
    yield page
    
    logger.info(f"关闭测试页面")


@pytest.fixture(scope="class")
def shared_page(browser) -> Page:
    """
    共享页面fixture - 测试类内共享的页面实例
    适用于需要保持状态的测试类
    
    使用方式:
        class TestLogin:
            def test_step1(self, shared_page):
                shared_page.goto("/login")
            
            def test_step2(self, shared_page):
                # 使用同一个页面实例
                pass
    """
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    
    logger.info("创建共享页面")
    
    yield page
    
    logger.info("关闭共享页面")
    context.close()


# ═══════════════════════════════════════════════════════════════
# TEST DATA FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def test_config():
    """
    测试配置fixture - 提供项目配置
    
    使用方式:
        def test_example(test_config):
            base_url = test_config.get_base_url()
    """
    return config


@pytest.fixture(scope="session")
def test_account():
    """
    测试账号fixture - 提供默认测试账号
    
    使用方式:
        def test_login(test_account):
            username = test_account["username"]
            password = test_account["password"]
    """
    return config.get("test_accounts.default", {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!"
    })


# ═══════════════════════════════════════════════════════════════
# ENVIRONMENT SETUP
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    设置测试环境 - session级别，只运行一次
    """
    # 创建必要的目录
    directories = [
        "reports",
        "screenshots",
        "allure-results",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("🚀 测试环境初始化完成")
    logger.info(f"   环境: {config.get_environment()}")
    logger.info(f"   Base URL: {config.get_base_url()}")
    logger.info("=" * 60)
    
    yield
    
    logger.info("=" * 60)
    logger.info("🏁 测试执行完成")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════
# TEST LOGGING
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function", autouse=True)
def log_test_info(request):
    """
    自动记录测试信息
    """
    test_name = request.node.name
    test_file = request.node.fspath.basename if hasattr(request.node, 'fspath') else ""
    
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"▶️  开始测试: {test_file}::{test_name}")
    logger.info("=" * 60)
    
    yield
    
    logger.info(f"⏹️  结束测试: {test_name}")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════
# SCREENSHOT ON FAILURE
# ═══════════════════════════════════════════════════════════════

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试报告钩子 - 失败时自动截图
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="function")
def screenshot_on_failure(request, page: Page):
    """
    失败时自动截图fixture
    
    使用方式:
        def test_example(page, screenshot_on_failure):
            # 测试失败时自动截图
            pass
    """
    yield
    
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        
        test_name = request.node.nodeid.replace("/", "_").replace("::", "_")
        screenshot_path = screenshot_dir / f"{test_name}_failure.png"
        
        try:
            page.screenshot(path=str(screenshot_path))
            logger.info(f"📸 失败截图已保存: {screenshot_path}")
        except Exception as e:
            logger.error(f"截图失败: {e}")

