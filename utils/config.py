# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Configuration Manager
# ═══════════════════════════════════════════════════════════════
"""
配置管理器 - 统一管理项目配置
支持 YAML 配置文件和环境变量
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ConfigManager:
    """
    配置管理器
    
    配置优先级（从高到低）:
    1. 环境变量
    2. config/project.yaml
    3. 默认值
    
    使用方式:
        config = ConfigManager()
        base_url = config.get_base_url()
        timeout = config.get("browser.timeout", 30000)
    """
    
    _instance = None
    _config_data = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: str = "config/project.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        if ConfigManager._config_data is None:
            ConfigManager._config_data = self._load_config(config_file)
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            dict: 配置数据
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            print(f"⚠️ 配置文件不存在: {config_file}，使用默认配置")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "project": {
                "name": "Test Project",
                "version": "1.0.0"
            },
            "environments": {
                "default": "dev",
                "dev": {
                    "base_url": "http://localhost:3000",
                    "api_url": "http://localhost:8080/api"
                }
            },
            "browser": {
                "headless": True,
                "slow_mo": 0,
                "timeout": 30000,
                "viewport": {"width": 1920, "height": 1080},
                "type": "chromium"
            },
            "test": {
                "retry_count": 2,
                "implicit_wait": 10,
                "screenshot_on_failure": True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        支持点号分隔的嵌套键：config.get("browser.timeout")
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        # 首先尝试从环境变量获取
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_value(env_value)
        
        # 从配置文件获取
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def _convert_value(self, value: str) -> Any:
        """转换字符串值为适当的类型"""
        if value.lower() in ['true', 'yes', '1']:
            return True
        elif value.lower() in ['false', 'no', '0']:
            return False
        elif value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value
    
    # ═══════════════════════════════════════════════════════════════
    # CONVENIENCE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_environment(self) -> str:
        """获取当前环境名称"""
        return os.getenv("TEST_ENV", self.get("environments.default", "dev"))
    
    def get_base_url(self) -> str:
        """获取当前环境的基础URL"""
        env = self.get_environment()
        return os.getenv("BASE_URL", self.get(f"environments.{env}.base_url", "http://localhost:3000"))
    
    def get_api_url(self) -> str:
        """获取当前环境的API URL"""
        env = self.get_environment()
        return os.getenv("API_URL", self.get(f"environments.{env}.api_url", "http://localhost:8080/api"))
    
    def get_browser_config(self) -> Dict[str, Any]:
        """获取浏览器配置"""
        return {
            "headless": self.get("browser.headless", True),
            "slow_mo": self.get("browser.slow_mo", 0),
            "timeout": self.get("browser.timeout", 30000),
            "viewport_width": self.get("browser.viewport.width", 1920),
            "viewport_height": self.get("browser.viewport.height", 1080),
            "type": self.get("browser.type", "chromium"),
        }
    
    def get_test_config(self) -> Dict[str, Any]:
        """获取测试配置"""
        return {
            "retry_count": self.get("test.retry_count", 2),
            "implicit_wait": self.get("test.implicit_wait", 10),
            "screenshot_on_failure": self.get("test.screenshot_on_failure", True),
            "video_recording": self.get("test.video_recording", False),
        }
    
    def get_test_account(self, account_type: str = "default") -> Dict[str, str]:
        """
        获取测试账号
        
        Args:
            account_type: 账号类型（default, admin等）
            
        Returns:
            dict: 包含username, email, password的字典
        """
        return self.get(f"test_accounts.{account_type}", {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!"
        })

