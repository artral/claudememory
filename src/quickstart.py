import anthropic

class Quickstart:
    def run(self):
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": "Explain quantum physics",
                },
                

            ],
        )
        print(message)