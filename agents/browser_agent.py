"""
Autonomous Browser Agent
Role: Navigate the web, find job postings, and interact with job boards autonomously.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, Page, Browser
from utils.deepseek_client import DeepSeekClient

class BrowserAgent:
    """
    An agent capable of autonomous web navigation using Playwright and DeepSeek.
    """

    def __init__(self, client: DeepSeekClient):
        self.client = client
        self.browser: Optional[Browser] = None
        self.context: Any = None
        self.system_instruction = """
        You are an Autonomous Browser Agent. Your goal is to navigate websites based on user instructions.
        You can see a simplified version of the page content.
        You must decide the next action from these options:
        1. CLICK: "selector"
        2. TYPE: "selector", "text"
        3. NAVIGATE: "url"
        4. EXTRACT: "Description of what to extract"
        5. FINISH: "Final result or summary"

        Respond ONLY with a valid JSON action:
        {"action": "CLICK", "selector": "button.apply"}
        """

    async def start(self):
        """Initialize browser session."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    async def stop(self):
        """Close browser session."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def _get_page_summary(self, page: Page) -> str:
        """Extract a simplified version of the page for the LLM."""
        # Get all interactive elements
        elements = await page.evaluate('''() => {
            const items = Array.from(document.querySelectorAll('a, button, input, h1, h2, [role="button"]'));
            return items.map(el => ({
                tag: el.tagName,
                text: el.innerText.substring(0, 50).trim(),
                id: el.id,
                className: el.className,
                type: el.type
            })).filter(item => item.text || item.id);
        }''')
        
        summary = f"URL: {page.url}\nContent Summary:\n"
        for i, el in enumerate(elements[:50]): # Limit to first 50 elements
            summary += f"[{i}] {el['tag']} - '{el['text']}' (Select via: {el['tag'].lower()}:has-text('{el['text']}'))\n"
        
        return summary

    async def navigate_and_extract(self, url: str, goal: str) -> str:
        """Navigate to a URL and attempt to achieve a goal autonomously."""
        page = await self.context.new_page()
        await page.goto(url)
        
        history = []
        for step in range(5): # Limit to 5 steps for safety
            summary = await self._get_page_summary(page)
            
            prompt = f"""
            GOAL: {goal}
            CURRENT PAGE STATE:
            {summary}
            
            PREVIOUS ACTIONS:
            {history}
            
            What is your next action?
            """
            
            response = self.client.generate_json(prompt, system_instruction=self.system_instruction)
            action = response.get("action")
            
            print(f"🤖 Browser Agent Step {step+1}: {action}...")
            history.append(response)
            
            if action == "NAVIGATE":
                await page.goto(response.get("url"))
            elif action == "CLICK":
                await page.click(response.get("selector"))
                await page.wait_for_load_state("networkidle")
            elif action == "TYPE":
                await page.fill(response.get("selector"), response.get("text"))
            elif action == "EXTRACT":
                content = await page.content()
                history.append({"extracted": "Content captured"})
            elif action == "FINISH":
                return response.get("summary", "Goal achieved.")
            
            await asyncio.sleep(2) # Human-like delay
            
        await page.close()
        return "Task timed out."

async def main_test():
    # Quick test if run directly
    from utils.deepseek_client import DeepSeekClient
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    client = DeepSeekClient(api_key=api_key)
    agent = BrowserAgent(client)
    
    await agent.start()
    result = await agent.navigate_and_extract("https://news.ycombinator.com", "Find the title of the first post.")
    print(f"RESULT: {result}")
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main_test())
