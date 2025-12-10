import asyncio
import os
import re
from dotenv import load_dotenv
from src.browser import BrowserEngine
from src.vision import VisionEngine
from src.agent import TaskPlanner

# Load environment variables from .env file
load_dotenv()

# Ensure assets folder exists
os.makedirs("assets", exist_ok=True)

async def execute_step(step_type, step_data, browser, vision, max_retries=3):
    """Execute a single step from the plan with retry logic"""
    if step_type == 'navigate':
        url = step_data
        if not url.startswith('http'):
            url = f"https://www.{url}" if not url.startswith('www.') else f"https://{url}"
        print(f"🌐 Navigating to {url}...")
        try:
            await browser.navigate(url)
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    elif step_type == 'scroll':
        direction = step_data.lower()
        try:
            if direction == 'down':
                await browser.scroll_down()
            elif direction == 'up':
                await browser.scroll_up()
            elif direction == 'bottom':
                await browser.scroll_to_bottom()
            return True
        except Exception as e:
            print(f"❌ Scroll failed: {e}")
            return False
        
    elif step_type == 'click':
        target = step_data
        print(f"🔍 Looking for: {target}")
        
        # Try multiple times with scrolling
        for attempt in range(max_retries):
            if attempt > 0:
                print(f"🔄 Retry attempt {attempt + 1}/{max_retries}")
            
            # Take screenshot
            image, element_map = await browser.get_som_screenshot()
            
            # Better prompts based on target type
            if "search" in target.lower():
                prompt = f"Look at this webpage. Find the MAIN SEARCH INPUT BOX (usually at the top center with placeholder text like 'Search'). Each element has a RED BOX with a WHITE NUMBER inside. What is the NUMBER of the search input box? Reply with ONLY that number, nothing else."
            elif "quantity" in target.lower() or "increase" in target.lower():
                prompt = f"Find the '+' or 'increase quantity' button. Each element has a red box with a number ID. Which number is the + button to increase quantity? Reply with ONLY the number."
            elif "add to cart" in target.lower() or "add" in target.lower():
                prompt = f"Find the 'Add to Cart' or 'Add' button. Each element has a red box with a number ID. Which number is the add to cart button? Reply with ONLY the number."
            else:
                prompt = f"Find the element: '{target}'. Each UI element has a red box with an ID number inside. Which ID number is '{target}'? Reply with ONLY the number."
            
            response = vision.analyze_screen(image, prompt)
            print(f"🤖 Found ID: {response}")
            
            # Extract and click
            match = re.search(r'\d+', response)
            if match:
                element_id = int(match.group())
                if element_id in element_map:
                    print(f"⚡ Clicking ID {element_id}...")
                    success = await browser.click_element(element_map, element_id)
                    if success:
                        await asyncio.sleep(2)
                        return True
                    else:
                        print(f"⚠️ Click failed, retrying...")
                else:
                    print(f"❌ ID {element_id} not in map. Element might be off-screen.")
                    if attempt < max_retries - 1:
                        print("📜 Scrolling down to find element...")
                        await browser.scroll_down()
                        await asyncio.sleep(1)
            else:
                print("❌ Could not parse element ID from response")
                if attempt < max_retries - 1:
                    await browser.scroll_down()
        
        print(f"❌ Failed to click '{target}' after {max_retries} attempts")
        return False
            
    elif step_type == 'type':
        text = step_data
        print(f"⌨️ Typing: {text}")
        try:
            await browser.page.keyboard.type(text)
            await browser.page.keyboard.press("Enter")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Typing failed: {e}")
            return False
    
    return False

async def main():
    # 1. Initialize Engines (Only once!)
    vision = VisionEngine()
    browser = BrowserEngine(headless=False)
    planner = TaskPlanner()
    
    await browser.start()
    
    # 2. Go to Google to start
    await browser.navigate("https://www.google.com")
    
    print("\n" + "="*40)
    print("🤖 OCULAR AGENT READY (with Auto-Planning)")
    print("Type 'exit' to quit.")
    print("Type 'test vision' to test what the AI sees")
    print("Examples: 'search for football shoes on amazon'")
    print("          'find laptops on flipkart'")
    print("="*40 + "\n")

    # 3. The Infinite Loop
    while True:
        try:
            # A. Get User Command
            user_command = input("👉 Goal: ").strip()
            if user_command.lower() == "exit":
                break
            
            # Test vision mode
            if user_command.lower() == "test vision":
                print("\n🔍 Testing vision capabilities...\n")
                image, element_map = await browser.get_som_screenshot()
                
                # Ask it various questions
                questions = [
                    "What website is this?",
                    "Describe what you see on this page in detail.",
                    "What are the main interactive elements visible?",
                    "Is there a search box? If yes, describe where it is.",
                ]
                
                for q in questions:
                    print(f"❓ {q}")
                    answer = vision.analyze_screen(image, q)
                    print(f"💬 {answer}\n")
                
                print(f"📊 Total elements detected: {len(element_map)}")
                continue

            # Ask for mode
            mode = input("Mode? [1] Pre-planned [2] Reactive [3] Adaptive (default=3): ").strip()
            if not mode:
                mode = "3"
            
            if mode == "3":
                # NEW: Adaptive execution - plan + feedback loop
                print(f"\n🧠 Creating initial plan for: '{user_command}'...")
                plan = planner.create_plan(user_command)
                
                if not plan:
                    print("❌ Could not create a plan. Try being more specific.")
                    continue
                
                print(f"📋 Initial plan ({len(plan)} steps):")
                for i, (step_type, step_data) in enumerate(plan, 1):
                    print(f"   {i}. {step_type.upper()}: {step_data}")
                
                print("\n🚀 Starting adaptive execution...\n")
                completed_steps = []
                max_iterations = 20
                
                for iteration in range(max_iterations):
                    if not plan:
                        print("\n✅ All steps completed!\n")
                        break
                    
                    # Get next step from plan
                    step_type, step_data = plan[0]
                    plan = plan[1:]  # Remove from plan
                    
                    print(f"[Step {iteration + 1}] 🎯 {step_type.upper()}: {step_data}")
                    
                    # Execute the step
                    await execute_step(step_type, step_data, browser, vision)
                    last_action = f"{step_type.upper()}: {step_data}"
                    completed_steps.append(last_action)
                    
                    # Verify and get feedback
                    print("🔍 Verifying action...")
                    image, element_map = await browser.get_som_screenshot()
                    describe_prompt = "Describe what you see on this webpage in one sentence."
                    screen_description = vision.analyze_screen(image, describe_prompt)
                    print(f"👁️ Screen: {screen_description}")
                    
                    # Check if we need to replan
                    success, new_plan = planner.verify_and_replan(
                        user_command, plan, completed_steps, screen_description, last_action
                    )
                    
                    if not success and new_plan:
                        print("⚠️ Action failed! Replanning...")
                        print(f"📋 New plan ({len(new_plan)} steps):")
                        for i, (st, sd) in enumerate(new_plan, 1):
                            print(f"   {i}. {st.upper()}: {sd}")
                        plan = new_plan
                    elif success:
                        print("✅ Action verified\n")
                    
                    await asyncio.sleep(1)
                
                if iteration >= max_iterations - 1:
                    print("\n⚠️ Reached maximum iterations\n")
                    
            elif mode == "1":
                # OLD WAY: Pre-planned execution
                print(f"\n🧠 Planning steps for: '{user_command}'...")
                steps = planner.create_plan(user_command)
                
                if not steps:
                    print("❌ Could not create a plan. Try being more specific.")
                    continue
                
                print(f"📋 Plan created with {len(steps)} steps:")
                for i, (step_type, step_data) in enumerate(steps, 1):
                    print(f"   {i}. {step_type.upper()}: {step_data}")
                
                print("\n🚀 Executing plan...\n")
                for i, (step_type, step_data) in enumerate(steps, 1):
                    print(f"[Step {i}/{len(steps)}]", end=" ")
                    await execute_step(step_type, step_data, browser, vision)
                
                print("\n✅ Plan completed!\n")
            else:
                # NEW WAY: Reactive execution with feedback loop
                print(f"\n🔄 Starting reactive execution for: '{user_command}'...\n")
                completed_steps = []
                max_steps = 20  # Safety limit
                
                for step_num in range(1, max_steps + 1):
                    # Get current screen state
                    image, element_map = await browser.get_som_screenshot()
                    
                    # Ask vision model to describe what's on screen
                    describe_prompt = "Describe what you see on this webpage in one sentence. What are the main elements visible?"
                    screen_description = vision.analyze_screen(image, describe_prompt)
                    print(f"👁️ Screen: {screen_description}")
                    
                    # Ask planner what to do next
                    next_action = planner.get_next_action(user_command, completed_steps, screen_description)
                    
                    if next_action is None:
                        print("\n✅ Goal achieved!\n")
                        break
                    
                    step_type, step_data = next_action
                    print(f"[Step {step_num}] 🎯 Next: {step_type.upper()} - {step_data}")
                    
                    # Execute the action
                    await execute_step(step_type, step_data, browser, vision)
                    
                    # Record what we did
                    completed_steps.append(f"{step_type.upper()}: {step_data}")
                    
                    # Small delay between steps
                    await asyncio.sleep(1)
                
                if step_num >= max_steps:
                    print("\n⚠️ Reached maximum steps limit\n")

        except Exception as e:
            print(f"⚠️ Error in loop: {e}")

    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())