# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Core Module
# ═══════════════════════════════════════════════════════════════
"""
Core framework module - DO NOT MODIFY
Contains base classes and utilities for test automation
"""

from core.base_page import BasePage, BaseDialog
from core.page_utils import PageUtils
from core.fixtures import *

__all__ = ['BasePage', 'BaseDialog', 'PageUtils']

