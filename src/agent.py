import os
import re
from openai import OpenAI

class TaskPlanner:
    def __init__(self):
        """Initialize with OpenAI-compatible API (works with DeepSeek, OpenAI, or local LLMs)"""
        # Check for DeepSeek first, then fall back to OpenAI
        if os.getenv("DEEPSEEK_API_KEY"):
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = "https://api.deepseek.com/v1"
            self.model = "deepseek-chat"
        else:
            api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def create_plan(self, user_goal):
        """
        Takes a high-level goal like 'search for football shoes on amazon'
        and breaks it into atomic steps
        """
        prompt = f"""You are a web automation planner. Break down the user's goal into simple, atomic steps.

User Goal: {user_goal}

Rules:
1. Each step should be ONE action: either navigate to a URL, click something, or type something
2. Use these formats:
   - NAVIGATE: <url> (e.g., NAVIGATE: amazon.in)
   - CLICK: <description> (e.g., CLICK: search box)
   - TYPE: <text> (e.g., TYPE: football shoes)
3. Be specific and sequential
4. Keep it minimal - only necessary steps

Example:
User Goal: search for laptops on flipkart
Steps:
1. NAVIGATE: flipkart.com
2. CLICK: search box
3. TYPE: laptops

Now create steps for the user's goal. Reply with ONLY the numbered steps, nothing else."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        plan_text = response.choices[0].message.content.strip()
        return self.parse_plan(plan_text)
    
    def get_next_action(self, user_goal, completed_steps, current_screen_description):
        """
        Reactive planning: decide next action based on current state
        """
        completed_str = "\n".join([f"- {s}" for s in completed_steps]) if completed_steps else "None yet"
        
        prompt = f"""You are a web automation agent. Based on the current screen and goal, decide the NEXT action.

User Goal: {user_goal}

Completed Steps:
{completed_str}

Current Screen: {current_screen_description}

What should be the NEXT action? Choose ONE:
- NAVIGATE: <url> (if need to go to a website)
- CLICK: <description> (if need to click something)
- TYPE: <text> (if need to type)
- DONE (if goal is achieved)

Reply with ONLY the action in the format above, nothing else."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )
        
        action_text = response.choices[0].message.content.strip()
        
        if action_text.upper() == "DONE":
            return None
        
        # Parse single action
        if action_text.startswith('NAVIGATE:'):
            url = action_text.replace('NAVIGATE:', '').strip()
            return ('navigate', url)
        elif action_text.startswith('CLICK:'):
            target = action_text.replace('CLICK:', '').strip()
            return ('click', target)
        elif action_text.startswith('TYPE:'):
            text = action_text.replace('TYPE:', '').strip()
            return ('type', text)
        
        return None
    
    def verify_and_replan(self, user_goal, original_plan, completed_steps, current_screen_description, last_action):
        """
        Verify if last action succeeded and replan if needed
        Returns: (success: bool, new_plan: list or None)
        """
        completed_str = "\n".join([f"- {s}" for s in completed_steps]) if completed_steps else "None yet"
        remaining_plan = "\n".join([f"- {step[0].upper()}: {step[1]}" for step in original_plan])
        
        prompt = f"""You are verifying a web automation task.

User Goal: {user_goal}

Original Remaining Plan:
{remaining_plan}

Completed Steps:
{completed_str}

Last Action: {last_action}

Current Screen: {current_screen_description}

Did the last action succeed? Is the plan still valid?

Reply in this format:
STATUS: [SUCCESS/FAILED]
REASON: [brief explanation]
NEXT_PLAN: [if failed, provide new steps in NAVIGATE/CLICK/TYPE format, one per line. If success, write CONTINUE]"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse response
        success = "SUCCESS" in result.split('\n')[0].upper()
        
        # Extract new plan if failed
        if not success and "NEXT_PLAN:" in result:
            plan_section = result.split("NEXT_PLAN:")[1].strip()
            if plan_section.upper() != "CONTINUE":
                new_plan = self.parse_plan(plan_section)
                return False, new_plan
        
        return success, None
    
    def parse_plan(self, plan_text):
        """Parse the LLM response into structured steps"""
        steps = []
        lines = plan_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Remove numbering like "1. " or "Step 1:"
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            line = re.sub(r'^Step\s+\d+:\s*', '', line, flags=re.IGNORECASE)
            
            if line.startswith('NAVIGATE:'):
                url = line.replace('NAVIGATE:', '').strip()
                steps.append(('navigate', url))
            elif line.startswith('CLICK:'):
                target = line.replace('CLICK:', '').strip()
                steps.append(('click', target))
            elif line.startswith('TYPE:'):
                text = line.replace('TYPE:', '').strip()
                steps.append(('type', text))
        
        return steps
