import anthropic

class MemoryTool:
    client = anthropic.Anthropic()
    def __init__(self):
        {

        }

    def execute_tool(self, name, tool_input):
        """Execute a tool and return the result."""
        return f"Weather in {tool_input.get('location', 'unknown')}: 72°F"
    
    def run(self):
        message = self.client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "I'm working on a Python web scraper that keeps crashing with a timeout error. Here's the problematic function:\n\n```python\ndef fetch_page(url, retries=3):\n    for i in range(retries):\n        try:\n            response = requests.get(url, timeout=5)\n            return response.text\n        except requests.exceptions.Timeout:\n            if i == retries - 1:\n                raise\n            time.sleep(1)\n```\n\nPlease help me debug this.",
            }
        ],
        tools=[{"type": "memory_20250818", "name": "memory"}],
        )
        print(message)


