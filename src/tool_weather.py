import anthropic

class WeatherTool:
    client = anthropic.Anthropic()
    def __init__(self):
        self.weather_tool = {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City and state"},
                },
                "required": ["location"],
            },
        }

    def execute_tool(self, name, tool_input):
        """Execute a tool and return the result."""
        return f"Weather in {tool_input.get('location', 'unknown')}: 72°F"
    
    def run(self):
        response = self.client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        tools=[self.weather_tool],
        messages=[{"role": "user", "content": "What is the weather at Minneapolis, MN?"}],
        )
        if response.stop_reason == "tool_use":
        # Extract and execute the tool
            for block in response.content:
                if block.type == "tool_use":
                    result = self.execute_tool(block.name, block.input)
                    print(result)
                    # Return result to Claude for final response
