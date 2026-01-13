# Browser-Use设计文档

## 1. 核心目标

**为Agent提供浏览器自动化能力，实现网页交互、数据抓取、截图等功能**

## 2. 技术选型：Playwright

```python
# 使用Playwright而非Selenium
# 优势：更快、更稳定、支持现代浏览器API
```

## 3. 核心实现

```python
# packages/browser/playwright_browser.py

from playwright.async_api import async_playwright, Browser, Page

class BrowserAutomation:
    """浏览器自动化"""
    
    async def create_browser(self, headless: bool = True):
        """创建浏览器实例"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        return self.browser
    
    async def navigate_and_extract(self, url: str) -> dict:
        """导航并提取内容"""
        page = await self.browser.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 提取内容
            title = await page.title()
            content = await page.content()
            text = await page.evaluate("() => document.body.innerText")
            
            # 截图
            screenshot_path = f"/workspace/screenshots/{uuid4().hex}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            
            return {
                "url": url,
                "title": title,
                "html": content,
                "text": text,
                "screenshot": screenshot_path
            }
        finally:
            await page.close()
    
    async def fill_form(self, url: str, form_data: dict):
        """填写表单"""
        page = await self.browser.new_page()
        await page.goto(url)
        
        for selector, value in form_data.items():
            await page.fill(selector, value)
        
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")
        
        return await page.content()
```

## 4. 与Deep Research集成

```python
# Deep Research场景：网页内容提取

@tool_registry.register
class ReadURLTool(BaseTool):
    """读取网页内容工具"""
    
    async def execute(self, url: str) -> ToolResult:
        browser = BrowserAutomation()
        await browser.create_browser(headless=True)
        
        result = await browser.navigate_and_extract(url)
        
        # 清理HTML，只保留文本
        from readability import Document
        doc = Document(result["html"])
        clean_text = doc.summary()
        
        # 如果文本过长，存文件系统
        if len(clean_text) > 10000:
            file_path = f"research/pages/{hashlib.md5(url.encode()).hexdigest()}.md"
            await fs.write(file_path, clean_text)
            
            return ToolResult(
                status="success",
                summary=f"网页内容已存储至{file_path}",
                data={"file_path": file_path, "preview": clean_text[:500]}
            )
        
        return ToolResult(status="success", data={"text": clean_text})
```

## 5. 安全限制

```python
# 限制访问的域名白名单
ALLOWED_DOMAINS = [
    "wikipedia.org",
    "github.com",
    "arxiv.org",
    # ... 可配置
]

async def validate_url(url: str) -> bool:
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return any(allowed in domain for allowed in ALLOWED_DOMAINS)
```

## 6. 总结

- Playwright提供现代浏览器自动化
- 网页内容清理（Readability）
- 与文件系统集成（大内容存文件）
- Deep Research的核心工具
