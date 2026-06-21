## This code is provided for educational purposes only. Use with caution and at your own risk.
## This is most of your token budget, so consider carefully before adding more code or print statements!
"""
Computer-use agent loop for Claude.

Handles all three tools Claude can call in this setup:
  - computer        (mouse/keyboard/screenshot control via pyautogui + mss)
  - bash             (shell commands via subprocess)
  - str_replace_based_edit_tool  (file view/create/edit)

Run on a machine you're comfortable watching closely — this gives Claude
real control of your mouse, keyboard, and a shell.
"""

import anthropic
import base64
import io
import json
import os
import re
import subprocess
import time
from datetime import datetime

import pyautogui
import mss
from PIL import Image

URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+|(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s\"'<>]*)?")

pyautogui.FAILSAFE = True  # move mouse to a screen corner to abort


class ComputerTool:
    def __init__(self, display_width=1024, display_height=768, log_dir="run_logs"):
        self.client = anthropic.Anthropic()
        self.display_width = display_width
        self.display_height = display_height
        # Track real screen size so we can scale Claude's coordinates correctly
        self.real_width, self.real_height = pyautogui.size()

        # Tracing: every action gets recorded here, plus any URLs/sites detected in it
        self.action_log = []
        self.sites_visited = []
        self.log_dir = os.path.join(log_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(self.log_dir, exist_ok=True)

    def _extract_sites(self, tool_name: str, action: dict):
        """Pull out any URL/domain mentioned in a typed string or bash command."""
        found = []
        if tool_name == "computer" and action.get("action") == "type":
            found += URL_PATTERN.findall(action.get("text", ""))
        elif tool_name == "bash":
            found += URL_PATTERN.findall(action.get("command", ""))
        for site in found:
            if site not in self.sites_visited:
                self.sites_visited.append(site)
        return found

    # ---------- screenshotting ----------

    def _screenshot(self) -> dict:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        img = img.resize((self.display_width, self.display_height))

        # Save a copy for the audit trail
        ts = datetime.now().strftime("%H%M%S_%f")
        img.save(os.path.join(self.log_dir, f"screenshot_{ts}.png"))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        }

    def _scale_coord(self, coordinate):
        """Claude's coordinates are in the declared display_width/height space;
        scale them to the real screen resolution before acting."""
        x, y = coordinate
        sx = x * (self.real_width / self.display_width)
        sy = y * (self.real_height / self.display_height)
        return sx, sy

    # ---------- computer tool ----------

    def _run_computer_action(self, action: dict):
        act = action.get("action")
        text_result = None

        if act == "screenshot":
            pass

        elif act in ("left_click", "right_click", "double_click", "triple_click", "middle_click"):
            x, y = self._scale_coord(action["coordinate"])
            clicks = {"double_click": 2, "triple_click": 3}.get(act, 1)
            button = "right" if act == "right_click" else ("middle" if act == "middle_click" else "left")
            pyautogui.click(x, y, clicks=clicks, button=button)

        elif act == "left_mouse_down":
            x, y = self._scale_coord(action["coordinate"])
            pyautogui.moveTo(x, y)
            pyautogui.mouseDown()

        elif act == "left_mouse_up":
            pyautogui.mouseUp()

        elif act == "mouse_move":
            x, y = self._scale_coord(action["coordinate"])
            pyautogui.moveTo(x, y)

        elif act == "drag" or act == "left_click_drag":
            start = action.get("start_coordinate")
            end = action["coordinate"]
            if start:
                sx, sy = self._scale_coord(start)
                pyautogui.moveTo(sx, sy)
            ex, ey = self._scale_coord(end)
            pyautogui.dragTo(ex, ey, duration=0.3, button="left")

        elif act == "type":
            pyautogui.typewrite(action["text"], interval=0.02)

        elif act == "key":
            keys = action["text"].lower().split("+")
            pyautogui.hotkey(*keys) if len(keys) > 1 else pyautogui.press(keys[0])

        elif act == "hold_key":
            keys = action["text"].lower().split("+")
            duration = action.get("duration", 1)
            for k in keys:
                pyautogui.keyDown(k)
            time.sleep(duration)
            for k in keys:
                pyautogui.keyUp(k)

        elif act == "scroll":
            x, y = self._scale_coord(action.get("coordinate", (self.real_width // 2, self.real_height // 2)))
            amount = action.get("scroll_amount", 3)
            direction = action.get("scroll_direction", "down")
            pyautogui.moveTo(x, y)
            pyautogui.scroll(-amount if direction == "down" else amount)

        elif act == "wait":
            time.sleep(action.get("duration", 1))

        elif act == "cursor_position":
            x, y = pyautogui.position()
            text_result = f"Cursor at ({x}, {y})"

        elif act == "zoom":
            # Crop the declared region from a fresh full-res screenshot and return that
            region = action.get("region")
            with mss.mss() as sct:
                raw = sct.grab(sct.monitors[1])
                img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            if region:
                x1, y1, x2, y2 = region
                sx = self.real_width / self.display_width
                sy = self.real_height / self.display_height
                img = img.crop((x1 * sx, y1 * sy, x2 * sx, y2 * sy))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}}]

        # default: return a fresh screenshot so Claude can see the result
        content = [self._screenshot()]
        if text_result:
            content.insert(0, {"type": "text", "text": text_result})
        return content

    # ---------- bash tool ----------

    def _run_bash_action(self, action: dict):
        command = action.get("command", "")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            output = "Command timed out after 30s"
        except Exception as e:
            output = f"Error running command: {e}"
        return [{"type": "text", "text": output or "(no output)"}]

    # ---------- text editor tool ----------

    def _run_editor_action(self, action: dict):
        command = action.get("command")
        path = action.get("path")
        try:
            if command == "view":
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return [{"type": "text", "text": content}]

            elif command == "create":
                with open(path, "w", encoding="utf-8") as f:
                    f.write(action.get("file_text", ""))
                return [{"type": "text", "text": f"Created {path}"}]

            elif command == "str_replace":
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                old, new = action.get("old_str", ""), action.get("new_str", "")
                if content.count(old) != 1:
                    return [{"type": "text", "text": f"old_str not uniquely found in {path}"}]
                content = content.replace(old, new)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return [{"type": "text", "text": f"Edited {path}"}]

            else:
                return [{"type": "text", "text": f"Unsupported editor command: {command}"}]
        except Exception as e:
            return [{"type": "text", "text": f"Error: {e}"}]

    # ---------- dispatch + loop ----------

    def _execute(self, tool_name: str, action: dict):
        if tool_name == "computer":
            return self._run_computer_action(action)
        elif tool_name == "bash":
            return self._run_bash_action(action)
        elif tool_name == "str_replace_based_edit_tool":
            return self._run_editor_action(action)
        else:
            return [{"type": "text", "text": f"Unknown tool: {tool_name}"}]

    def run(self, instruction: str, max_iterations: int = 20, verbose: bool = True):
        messages = [{"role": "user", "content": instruction}]

        tools = [
            {
                "type": "computer_20251124",
                "name": "computer",
                "display_width_px": self.display_width,
                "display_height_px": self.display_height,
                "display_number": 1,
            },
            {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"},
            {"type": "bash_20250124", "name": "bash"},
        ]

        for i in range(max_iterations):
            response = self.client.beta.messages.create(
                model="claude-opus-4-8",
                max_tokens=1024,
                tools=tools,
                messages=messages,
                betas=["computer-use-2025-11-24"],
            )

            messages.append({"role": "assistant", "content": response.content})

            if verbose:
                for block in response.content:
                    if block.type == "text":
                        print(f"[{i}] Claude: {block.text}")

            if response.stop_reason != "tool_use":
                if verbose:
                    print(f"[{i}] Finished: {response.stop_reason}")
                break

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    sites = self._extract_sites(block.name, block.input)
                    self.action_log.append({
                        "iteration": i,
                        "tool": block.name,
                        "action": block.input,
                        "sites_detected": sites,
                        "timestamp": datetime.now().isoformat(),
                    })
                    if verbose:
                        extra = f"  <- site: {sites}" if sites else ""
                        print(f"[{i}] Action ({block.name}): {block.input}{extra}")
                    content = self._execute(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content,
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            if verbose:
                print("Hit max_iterations without finishing.")

        # Write the full trace so you can review what happened after the fact
        trace_path = os.path.join(self.log_dir, "trace.json")
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump({"actions": self.action_log, "sites_visited": self.sites_visited}, f, indent=2, default=str)

        if verbose:
            print(f"\nSites detected during this run: {self.sites_visited or 'none found'}")
            print(f"Full trace + screenshots saved to: {self.log_dir}")

        return messages


if __name__ == "__main__":
    tool = ComputerTool()
    tool.run("Save a picture of a cat to my desktop.")