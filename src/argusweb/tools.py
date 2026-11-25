from langchain.messages import ToolMessage
from playwright.async_api import async_playwright
from langchain_core.tools import tool, ToolException
import base64
from pydantic import HttpUrl

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from argusweb.core.dom_parser import snapshot_parser
import asyncio




_playwright = None 
_browser = None
_page = None
_context = None

async def get_page():
    global _playwright, _browser, _page, _context
    if _page is None:
        if _playwright is None:
            _playwright = await async_playwright().start()
        if _browser is None:
            _browser = await _playwright.chromium.launch(headless=False)
        if _context is None:
            _context = await _browser.new_context(viewport={"width": 1366, "height": 768},device_scale_factor=1.0)
            _context.set_default_timeout(10000)
        _page = await _context.new_page()
    return _page



# 1. Add this import at the top of your tools.py file
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

async def get_snapshot(query: str) -> str:
    """
    Cleans a cloned copy of the DOM, stamps data-argus-ids, calculates 0-indexed occurrences 
    for .nth() locator mapping, and returns a nested JSON tree without breaking the live page.
    """
    page = await get_page()
    
        
    snapshot = await page.aria_snapshot(mode="ai")
    
    if snapshot:
        snapshot = await asyncio.to_thread(snapshot_parser, snapshot) 

        
    return snapshot


async def get_screenshot()-> str:
    """
    Takes a screenshot of the current page and returns it as a base64-encoded string.
    Returns:
        str: A base64-encoded string representing the screenshot.
    """
    page = await get_page()
    screenshot_bytes = await page.screenshot(
        type="jpeg", quality=80, full_page=False
    )

    base64_screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")

    return base64_screenshot






@tool
async def navigate_to(url: HttpUrl):
    """
    Navigates to the specified URL in the browser.
    Args:
        url (str): The URL to navigate to.
    Returns:
        str: A message indicating that the navigation was successful.
    """
    try:
        page = await get_page()
        await page.goto(str(url))
        return{
                    "messages" : [{
                        "role" : "tool",
                        "content" : f"Navigated to {url}",
                        "status" : "success",
        }]}
    except:
        raise ToolException("Failed to navigate")

@tool
async def mouse_action(action:str, element_id:str, text:str | None = None):
    """
    Executes a specified action on a target element in the browser.
    Args:
        action (str): The action to perform (e.g., "click", "fill").
        element_id (str): The reference to the target element which is given in the aria snapshot.
        text (str, optional): The value to use for actions like "fill".
    Returns:
        str: A message indicating that the action was executed successfully.
    """
    try:
        page = await get_page()
        target = page.get_by_ref(element_id)
        action = action.lower()
        if action == "click":
            await target.click()
        elif action == "type":
            await target.fill(text)
        else:
            return {
                        "messages" : [{
                                    "role" : "tool",
                                    "content" : "Error: Tool is not supported",
                                    "status" : "error",
                            }]}
        return {
                                                "messages" : [{
                                                    "role" : "tool",
                                                    "content" : "Did the action mentioned as per the params",
                                                    "status" : "success",
                                    }]
                                    }         
    except:  
        raise ToolException("Failed to do executor action")



@tool
async def close_browser():
    """
    Closes the browser and cleans up resources.
    Returns:
        str: A message indicating that the browser was closed.
    """
    global _playwright, _browser, _page, _context
    if _page is not None:
        await _page.close()
        _page = None
    if _context is not None:
        await _context.close()
        _context = None
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None
    return "Browser closed"




from langchain_core.tools import tool, ToolException

@tool
async def mouse_click(x: int, y: int) -> str:
    """
    This tool takes the x and y coordinates on the screen to do a click.
    Args:
        x (int): x coordinate where to click.
        y (int): y coordinate where to click.
    """
    try:
        page = await get_page()
        # FIX 1: Pass x and y directly to mouse.click
        viewport = page.viewport_size    
        pixel_x = int((x / 1000) * viewport["width"])   # (766 / 1000) * 1280 = 980
        pixel_y = int((y / 1000) * viewport["height"])

        print(f"target pixel ({pixel_x}, {pixel_y})")
        await page.mouse.click(pixel_x, pixel_y) 
        
        # FIX 2: Return a simple string. ToolNode automatically wraps this in a ToolMessage.
        return {"messages": f"Clicked on x:{x} and y:{y}", "status" : "success"}
        
    except Exception as e:
        print(e)
        raise ToolException(f"Failed to click at {x},{y}: {str(e)}")