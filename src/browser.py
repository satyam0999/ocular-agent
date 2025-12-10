import asyncio
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
import io

class BrowserEngine:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--start-maximized']
        )
        # Create context with no viewport to use full window size
        context = await self.browser.new_context(no_viewport=True)
        self.page = await context.new_page()

    async def navigate(self, url):
        await self.page.goto(url, timeout=60000)  # 60 second timeout
        # Use 'domcontentloaded' instead of 'networkidle' for faster loading
        await self.page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)  # Give it extra time for dynamic content
        
        # Try to dismiss common popups/modals
        try:
            # Look for close buttons, "Not now", "Maybe later", etc.
            close_selectors = [
                'button:has-text("Close")',
                'button:has-text("Not now")',
                'button:has-text("Maybe later")',
                '[aria-label="Close"]',
                '.close-button',
                '[class*="close"]'
            ]
            for selector in close_selectors:
                try:
                    await self.page.click(selector, timeout=2000)
                    print("✅ Dismissed popup")
                    break
                except:
                    pass
        except:
            pass

    async def get_som_screenshot(self):
        """
        The Secret Sauce: 
        1. Inject JS to find interactive elements.
        2. Take a screenshot.
        3. Draw bounding boxes with IDs on the image.
        """
        # 1. Javascript Injection to find elements
        # We look for buttons, links, inputs, and textareas
        interactive_elements = await self.page.evaluate('''() => {
            const elements = document.querySelectorAll('button, a, input, textarea, [role="button"]');
            const items = [];
            let id = 0;
            elements.forEach((el) => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).visibility !== 'hidden') {
                    items.push({
                        id: id++,
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        tagName: el.tagName
                    });
                }
            });
            return items;
        }''')

        # 2. Take raw screenshot
        screenshot_bytes = await self.page.screenshot()
        image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        draw = ImageDraw.Draw(image)

        # 3. Draw the SoM (Set-of-Mark) Bounding Boxes
        # Use a default font. On Windows, this might need tuning.
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        element_map = {}

        for item in interactive_elements:
            x, y, w, h = item['x'], item['y'], item['width'], item['height']
            eid = item['id']
            
            # Save to map so we can click it later
            element_map[eid] = item

            # Draw Box (Red)
            draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
            
            # Draw ID Tag (White text on Red background)
            text = str(eid)
            # Draw background for text
            text_bbox = draw.textbbox((x, y), text, font=font)
            draw.rectangle([text_bbox[0], text_bbox[1], text_bbox[2], text_bbox[3]], fill="red")
            draw.text((x, y), text, fill="white", font=font)

        # Save for debugging
        image.save("assets/debug_som.png")
        return image, element_map

    async def click_element(self, element_map, element_id):
        if element_id not in element_map:
            print(f"❌ Error: ID {element_id} not found in current view.")
            return False
        
        item = element_map[element_id]
        # Click the center of the element
        click_x = item['x'] + (item['width'] / 2)
        click_y = item['y'] + (item['height'] / 2)
        
        try:
            await self.page.mouse.click(click_x, click_y)
            print(f"✅ Clicked element ID {element_id} at ({click_x}, {click_y})")
            await asyncio.sleep(2) # Wait for UI to update
            return True
        except Exception as e:
            print(f"❌ Click failed: {e}")
            return False
    
    async def scroll_down(self):
        """Scroll down one page"""
        await self.page.keyboard.press("PageDown")
        await asyncio.sleep(1)
        print("📜 Scrolled down")
    
    async def scroll_up(self):
        """Scroll up one page"""
        await self.page.keyboard.press("PageUp")
        await asyncio.sleep(1)
        print("📜 Scrolled up")
    
    async def scroll_to_bottom(self):
        """Scroll to bottom of page"""
        await self.page.keyboard.press("End")
        await asyncio.sleep(1)
        print("📜 Scrolled to bottom")

    async def stop(self):
        await self.browser.close()
        await self.playwright.stop()