from codereview_agent import CodeReviewAgent

class CodeReviewTest:
    def test_code_review(self):
        # This is a placeholder for the actual test implementation
        agent = CodeReviewAgent(memory_path="./memories_code_review")
        agent.review_code(open("my_file.py").read(), "my_file.py")

        agent.review_code(open("my_file.py").read(), "my_file.py")

        