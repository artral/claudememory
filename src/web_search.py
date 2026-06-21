import anthropic

class WebSearchTool:
    def __init__(self):
        self.web_search_tool = {
            "type": "web_search_20250305",
            "name": "web_search",
            "description": "Search the web for information",
        }
    def run(self):
        # Placeholder for actual web search implementation
        client = anthropic.Anthropic()
        response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=20000,
        #tools=[{"type": "web_search_20250305", "name": "web_search"}],
        #tool_choice={"type": "tool", "name": "web_search"},
        messages=[
        {"role": "user", "content": "Large input that uses most of context window..."}
        ],

        #messages=[{"role": "user", "content": "Search for latest AI news"}],
        )
        print(response)

        if response.stop_reason == "pause_turn":
            # Continue the conversation by sending the response back
            messages = [
                {"role": "user", "content": "Search for latest AI news"},
                {"role": "assistant", "content": response.content},
            ]
            continuation = client.messages.create(
                model="claude-opus-4-8",
                max_tokens=1024,
                messages=messages,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
            )
            print(continuation)