#!/usr/bin/env python
# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Command Line Interface
# ═══════════════════════════════════════════════════════════════
"""
CLI工具 - 提供命令行接口进行测试自动化操作

使用方式:
    # 分析页面
    python cli.py analyze --url https://example.com/
    
    # 生成测试代码
    python cli.py generate --url https://example.com/
    
    # 运行测试
    python cli.py run --tests tests/
    
    # 完整流程
    python cli.py full --url https://example.com/login
    
    # 查看Allure报告
    python cli.py report
"""

import click
import subprocess
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from generators.page_analyzer import PageAnalyzer
from generators.test_plan_generator import TestPlanGenerator
from generators.test_code_generator import TestCodeGenerator
from utils.config import ConfigManager

console = Console()
config = ConfigManager()


@click.group()
@click.version_option(version="1.0.0", prog_name="Playwright Test Scaffold")
def cli():
    """
    🎭 Playwright Test Scaffold - 自动化测试脚手架
    
    自动分析页面、生成测试计划、生成测试代码、运行测试、查看报告
    """
    pass


@cli.command()
@click.option("--url", "-u", required=True, help="要分析的页面URL")
@click.option("--output", "-o", default="analysis", help="输出目录")
@click.option("--auth", is_flag=True, help="页面是否需要认证")
def analyze(url: str, output: str, auth: bool):
    """
    📊 分析页面结构
    
    自动识别页面元素、表单、导航等信息
    """
    console.print(Panel.fit(
        f"[bold blue]分析页面[/bold blue]\n{url}",
        title="🔍 Page Analyzer"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("正在分析页面...", total=None)
        
        try:
            analyzer = PageAnalyzer()
            page_info = analyzer.analyze(url)
            
            progress.update(task, description="分析完成")
            
            # 保存结果
            output_dir = Path(output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            json_file = output_dir / "page_analysis.json"
            analyzer.to_json(page_info, str(json_file))
            
            # 显示结果
            _display_analysis_result(page_info)
            
            console.print(f"\n[green]✓ 分析结果已保存: {json_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]✗ 分析失败: {e}[/red]")
            raise click.Abort()


@cli.command()
@click.option("--url", "-u", required=True, help="要分析的页面URL")
@click.option("--output", "-o", default=".", help="输出目录")
def plan(url: str, output: str):
    """
    📝 生成测试计划
    
    根据页面分析结果生成Markdown格式的测试计划
    """
    console.print(Panel.fit(
        f"[bold blue]生成测试计划[/bold blue]\n{url}",
        title="📝 Test Plan Generator"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("正在分析页面...", total=None)
        
        try:
            # 分析页面
            analyzer = PageAnalyzer()
            page_info = analyzer.analyze(url)
            
            progress.update(task, description="正在生成测试计划...")
            
            # 生成测试计划
            generator = TestPlanGenerator()
            test_plan = generator.generate(page_info)
            
            # 保存测试计划
            output_dir = Path(output) / "docs" / "test-plans"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            page_name = url.split("/")[-1] or "home"
            plan_file = output_dir / f"{page_name.lower()}_test_plan.md"
            generator.save(test_plan, str(plan_file))
            
            progress.update(task, description="完成")
            
            console.print(f"\n[green]✓ 测试计划已生成: {plan_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]✗ 生成失败: {e}[/red]")
            raise click.Abort()


@cli.command()
@click.option("--url", "-u", required=True, help="要分析的页面URL")
@click.option("--output", "-o", default=".", help="输出目录")
def generate(url: str, output: str):
    """
    ⚡ 生成测试代码
    
    自动生成Page Object和测试用例代码
    """
    console.print(Panel.fit(
        f"[bold blue]生成测试代码[/bold blue]\n{url}",
        title="⚡ Code Generator"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("正在分析页面...", total=None)
        
        try:
            # 分析页面
            analyzer = PageAnalyzer()
            page_info = analyzer.analyze(url)
            
            progress.update(task, description="正在生成代码...")
            
            # 生成代码
            generator = TestCodeGenerator()
            files = generator.generate_all(page_info, output)
            
            progress.update(task, description="完成")
            
            # 显示生成的文件
            table = Table(title="生成的文件")
            table.add_column("类型", style="cyan")
            table.add_column("路径", style="green")
            
            for file_type, file_path in files.items():
                table.add_row(file_type, file_path)
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]✗ 生成失败: {e}[/red]")
            raise click.Abort()


@cli.command()
@click.option("--tests", "-t", default="tests/", help="测试目录或文件")
@click.option("--markers", "-m", default=None, help="pytest标记（如P0, P1）")
@click.option("--parallel", "-n", default=None, help="并行worker数量")
@click.option("--headed", is_flag=True, help="显示浏览器窗口")
@click.option("--slow", is_flag=True, help="慢速执行（便于观察）")
def run(tests: str, markers: str, parallel: str, headed: bool, slow: bool):
    """
    🚀 运行测试
    
    执行pytest测试并生成Allure报告
    """
    console.print(Panel.fit(
        f"[bold blue]运行测试[/bold blue]\n{tests}",
        title="🚀 Test Runner"
    ))
    
    # 构建pytest命令
    cmd = ["pytest", tests, "-v", "--alluredir=allure-results"]
    
    if markers:
        cmd.extend(["-m", markers])
    
    if parallel:
        cmd.extend(["-n", parallel])
    
    if headed:
        cmd.append("--headed")
    
    if slow:
        cmd.append("--slowmo=500")
    
    console.print(f"执行命令: [cyan]{' '.join(cmd)}[/cyan]\n")
    
    # 运行测试
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        console.print("\n[green]✓ 测试执行成功[/green]")
        console.print("\n[yellow]提示: 运行 'python cli.py report' 查看详细报告[/yellow]")
    else:
        console.print(f"\n[red]✗ 测试执行失败 (exit code: {result.returncode})[/red]")


@cli.command()
@click.option("--port", "-p", default=None, help="Allure服务端口")
def report(port: str):
    """
    📊 查看Allure报告
    
    启动Allure服务器查看测试报告
    """
    console.print(Panel.fit(
        "[bold blue]启动Allure报告服务[/bold blue]",
        title="📊 Allure Report"
    ))
    
    if not Path("allure-results").exists():
        console.print("[red]✗ 未找到allure-results目录，请先运行测试[/red]")
        raise click.Abort()
    
    cmd = ["allure", "serve", "allure-results"]
    if port:
        cmd.extend(["-p", port])
    
    console.print(f"执行命令: [cyan]{' '.join(cmd)}[/cyan]\n")
    console.print("[yellow]按 Ctrl+C 停止服务[/yellow]\n")
    
    subprocess.run(cmd)


@cli.command()
@click.option("--url", "-u", required=True, help="要测试的页面URL")
@click.option("--output", "-o", default=".", help="输出目录")
@click.option("--run-tests", is_flag=True, help="生成后立即运行测试")
def full(url: str, output: str, run_tests: bool):
    """
    🎯 完整流程
    
    一键执行: 分析页面 → 生成测试计划 → 生成测试代码 → 运行测试
    """
    console.print(Panel.fit(
        f"[bold blue]完整自动化流程[/bold blue]\n{url}",
        title="🎯 Full Automation"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # 步骤1: 分析页面
        task1 = progress.add_task("步骤1: 分析页面...", total=None)
        analyzer = PageAnalyzer()
        page_info = analyzer.analyze(url)
        progress.update(task1, description="步骤1: 分析页面 ✓")
        
        # 步骤2: 生成测试计划
        task2 = progress.add_task("步骤2: 生成测试计划...", total=None)
        plan_generator = TestPlanGenerator()
        test_plan = plan_generator.generate(page_info)
        
        output_dir = Path(output)
        plan_dir = output_dir / "docs" / "test-plans"
        plan_dir.mkdir(parents=True, exist_ok=True)
        
        page_name = url.split("/")[-1] or "home"
        plan_file = plan_dir / f"{page_name.lower()}_test_plan.md"
        plan_generator.save(test_plan, str(plan_file))
        progress.update(task2, description="步骤2: 生成测试计划 ✓")
        
        # 步骤3: 生成测试代码
        task3 = progress.add_task("步骤3: 生成测试代码...", total=None)
        code_generator = TestCodeGenerator()
        files = code_generator.generate_all(page_info, str(output_dir))
        progress.update(task3, description="步骤3: 生成测试代码 ✓")
    
    # 显示生成的文件
    table = Table(title="生成的文件")
    table.add_column("类型", style="cyan")
    table.add_column("路径", style="green")
    
    table.add_row("测试计划", str(plan_file))
    for file_type, file_path in files.items():
        table.add_row(file_type, file_path)
    
    console.print(table)
    
    # 运行测试
    if run_tests:
        console.print("\n[bold]步骤4: 运行测试[/bold]\n")
        test_file = files.get("test_cases", "tests/")
        cmd = ["pytest", test_file, "-v", "--alluredir=allure-results"]
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            console.print("\n[green]✓ 完整流程执行成功[/green]")
        else:
            console.print(f"\n[yellow]⚠ 测试执行完成，部分用例失败[/yellow]")
    else:
        console.print("\n[green]✓ 代码生成完成[/green]")
        console.print("\n[yellow]提示: 添加 --run-tests 参数可立即运行测试[/yellow]")
        console.print(f"[yellow]或手动运行: pytest {files.get('test_cases', 'tests/')} -v[/yellow]")


@cli.command()
def init():
    """
    🔧 初始化项目
    
    安装依赖并配置环境
    """
    console.print(Panel.fit(
        "[bold blue]初始化项目[/bold blue]",
        title="🔧 Project Init"
    ))
    
    steps = [
        ("安装Python依赖", ["pip", "install", "-r", "requirements.txt"]),
        ("安装Playwright浏览器", ["playwright", "install", "chromium"]),
    ]
    
    for step_name, cmd in steps:
        console.print(f"\n[cyan]{step_name}...[/cyan]")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print(f"[green]✓ {step_name} 完成[/green]")
        else:
            console.print(f"[red]✗ {step_name} 失败[/red]")
            console.print(result.stderr)
            raise click.Abort()
    
    console.print("\n[green]✓ 项目初始化完成[/green]")
    console.print("\n[yellow]下一步:[/yellow]")
    console.print("  1. 编辑 config/project.yaml 配置项目信息")
    console.print("  2. 运行 python cli.py full --url <your-page-url> 开始测试")


def _display_analysis_result(page_info):
    """显示分析结果"""
    # 基本信息
    info_table = Table(title="页面信息")
    info_table.add_column("属性", style="cyan")
    info_table.add_column("值", style="green")
    
    info_table.add_row("URL", page_info.url)
    info_table.add_row("标题", page_info.title)
    info_table.add_row("类型", page_info.page_type)
    info_table.add_row("元素数量", str(len(page_info.elements)))
    info_table.add_row("表单数量", str(len(page_info.forms)))
    
    console.print(info_table)
    
    # 元素列表
    if page_info.elements:
        elem_table = Table(title="页面元素")
        elem_table.add_column("#", style="dim")
        elem_table.add_column("类型", style="cyan")
        elem_table.add_column("选择器", style="green")
        elem_table.add_column("名称/文本", style="yellow")
        
        for i, elem in enumerate(page_info.elements[:20], 1):  # 只显示前20个
            name = elem.name or elem.text[:30] if elem.text else "-"
            elem_table.add_row(str(i), elem.type, elem.selector, name)
        
        if len(page_info.elements) > 20:
            elem_table.add_row("...", f"还有 {len(page_info.elements) - 20} 个元素", "", "")
        
        console.print(elem_table)


if __name__ == "__main__":
    cli()

