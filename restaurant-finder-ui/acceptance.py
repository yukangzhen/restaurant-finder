"""Sequential, fail-closed Playwright CLI driver for the approved demo acceptance.

This module is operational tooling. Importing it starts no browser or service.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid
from urllib.parse import urlsplit

QUESTIONS = (
    "According to Harbor Pasta Lab's menu, what is the mushroom pasta price?",
    "According to Harbor Pasta Lab's policy, how much notice must I give to cancel without charge, and what is charged if I cancel too late?",
    "And what about its cancellation fee?",
    "According to Harbor Pasta Lab's documents, is valet parking available?",
    "Compare mushroom pasta prices at Harbor Pasta Lab and Sakura Table Lab. Show the sources.",
    "Which is cheaper?",
    "What about both restaurants' prices and cancellation policies?",
)
MATRIX_HASH = hashlib.sha256(json.dumps(QUESTIONS).encode()).hexdigest()
TEXTBOX = "Type your message here..."


class AcceptanceError(RuntimeError):
    """Fixed-message operational failure, without provider or credential payloads."""


def redact(value):
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if not isinstance(value, str):
        return value
    value = re.sub(r"https?://[^\s\"<>]+", "[URL_REDACTED]", value)
    value = re.sub(r"/project/file/[^\s\"<>]+", "[SOURCE_URL_REDACTED]", value)
    return re.sub(r"(?i)((?:session_?id|token|signature|authorization)=)[^\s&\"<>]+",
                  r"\1[REDACTED]", value)


def write_json(path, value):
    """Atomically replace a receipt; fsync before rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".receipt-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def child_path(root, name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", name) or ".." in name:
        raise AcceptanceError("Invalid owned filename")
    result = Path(root) / name
    if result.resolve().parent != Path(root).resolve() or result.is_symlink():
        raise AcceptanceError("Owned path escaped")
    return result


def validate_origin(url, mode):
    parsed = urlsplit(url)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in ("", "/") or parsed.port is None):
        raise AcceptanceError("Unapproved browser origin")
    if mode not in ("local", "live") or (mode == "local" and parsed.port == 8010):
        raise AcceptanceError("Fixture cannot use live UI")
    if mode == "live" and parsed.port != 8010:
        raise AcceptanceError("Live UI origin differs")
    return f"http://127.0.0.1:{parsed.port}"


def function(body):
    return "async (page) => {\n" + body + "\n}"


def validate_function_shape(code):
    if not re.fullmatch(r"async \(page\) => \{\n[\s\S]*\n\}", code):
        raise AcceptanceError("Action must be a complete page function")


def cli_result(process):
    if process.returncode:
        raise AcceptanceError("CLI process failed")
    try:
        result = json.loads(process.stdout)
    except (ValueError, TypeError):
        raise AcceptanceError("CLI result is not structured JSON") from None

    def failed(value):
        if isinstance(value, dict):
            return (value.get("isError") is True or bool(value.get("error"))
                    or any(failed(v) for v in value.values()))
        if isinstance(value, list):
            return any(failed(v) for v in value)
        return isinstance(value, str) and bool(re.search(r"(?m)^### Error\b", value))
    if failed(result):
        raise AcceptanceError("CLI reported a semantic error")
    return result


def action_result(value):
    """Find only our explicit return envelope, not arbitrary UI text."""
    found = []

    def visit(item):
        if isinstance(item, dict):
            if "acceptance_result" in item:
                found.append(item["acceptance_result"])
            else:
                for key, content in item.items():
                    if isinstance(content, (dict, list)):
                        visit(content)
                    elif key in ("result", "text") and isinstance(content, str):
                        try:
                            visit(json.loads(content))
                        except ValueError:
                            pass
        elif isinstance(item, list):
            for content in item:
                visit(content)
    visit(value)
    if len(found) != 1 or not isinstance(found[0], dict):
        raise AcceptanceError("Missing unique action result")
    return found[0]


class Ledger:
    def __init__(self, path, mode="local"):
        self.path, self.mode = Path(path), mode
        if mode not in ("local", "live"):
            raise AcceptanceError("Invalid mode")
        if not self.path.exists():
            if mode == "live":
                raise AcceptanceError("Live approval ledger required")
            write_json(self.path, {"mode": mode, "matrix_hash": MATRIX_HASH,
                                  "slots": {f"L{i}": "UNUSED" for i in range(1, 8)},
                                  "attempts": 0, "source_opens": 0, "downloads": 0,
                                  "screenshots": 0, "chat": None})
        self.load()
        if mode == "live":
            helper_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            if not (self.data.get("live_allowed") is True
                    and self.data.get("preflight_verified") is True
                    and self.data.get("helper_sha256") == helper_hash):
                raise AcceptanceError("Live gate or frozen helper not verified")

    def load(self):
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        if self.data.get("mode") != self.mode or self.data.get("matrix_hash") != MATRIX_HASH:
            raise AcceptanceError("Ledger matrix or mode mismatch")
        return self.data

    def save(self):
        write_json(self.path, self.data)

    def check(self, slot):
        self.load()
        if slot not in self.data["slots"] or self.data["slots"][slot] != "UNUSED":
            raise AcceptanceError("Slot unavailable")
        index = int(slot[1:])
        if any(self.data["slots"][f"L{i}"] != "PASS" for i in range(1, index)):
            raise AcceptanceError("Previous seed or turn not accepted")
        if self.data["chat"] != ("A" if index <= 4 else "B"):
            raise AcceptanceError("Wrong conversation")
        return QUESTIONS[index - 1]

    def reserve(self, slot):
        # An exclusive lock prevents two controllers from both reserving a slot.
        lock = self.path.with_suffix(".lock")
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise AcceptanceError("Ledger writer already active") from None
        try:
            os.close(fd)
            self.check(slot)
            self.data["slots"][slot] = "DISPATCH_RESERVED"
            self.data["attempts"] += 1
            self.save()
        finally:
            lock.unlink()

    def state(self, slot, state):
        self.load()
        if state not in ("SUBMITTED", "UNCERTAIN", "PASS", "FAIL"):
            raise AcceptanceError("Invalid transition")
        old = self.data["slots"].get(slot)
        if ((state in ("SUBMITTED", "UNCERTAIN") and old != "DISPATCH_RESERVED")
                or (state in ("PASS", "FAIL") and old != "SUBMITTED")):
            raise AcceptanceError("Invalid slot transition")
        self.data["slots"][slot] = state
        self.save()

    def counter(self, name):
        self.load()
        limit = {"source_opens": 18, "downloads": 4, "screenshots": 18}.get(name)
        if limit is None or self.data[name] >= limit:
            raise AcceptanceError("Action limit exhausted")
        self.data[name] += 1
        self.save()


class CLI:
    def __init__(self, node, cli, root, session, expected_cli_hash, runner=subprocess.run):
        self.node, self.cli = str(Path(node).resolve()), Path(cli).resolve()
        self.root, self.runner = Path(root).resolve(), runner
        if not re.fullmatch(r"hybrid-[a-z0-9-]{1,55}", session):
            raise AcceptanceError("Invalid owned session")
        self.session = session
        package = self.cli.parent / "package.json"
        if (self.node != str(Path(shutil.which("node") or "").resolve())
                or self.cli.name != "playwright-cli.js" or not package.is_file()
                or json.loads(package.read_text())["name"] != "@playwright/cli"
                or hashlib.sha256(self.cli.read_bytes()).hexdigest() != expected_cli_hash):
            raise AcceptanceError("Installed executable identity mismatch")
        self.root.mkdir(parents=True, exist_ok=True)

    def call(self, *args):
        env = os.environ.copy()
        env["NO_UPDATE_NOTIFIER"] = "1"
        try:
            process = self.runner([self.node, str(self.cli), "--json",
                                   "-s=" + self.session, *map(str, args)],
                                  cwd=self.root, env=env, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=45)
        except (subprocess.TimeoutExpired, OSError):
            raise AcceptanceError("CLI outcome uncertain") from None
        # Persist only redacted output, including error cases.
        write_json(child_path(self.root, "cli-" + uuid.uuid4().hex + ".json"),
                   {"returncode": process.returncode, "stdout": redact(process.stdout),
                    "stderr": redact(process.stderr)})
        return cli_result(process)

    def prepare(self, code):
        validate_function_shape(code)
        path = child_path(self.root, "action-" + uuid.uuid4().hex + ".js")
        path.write_text(code, encoding="utf-8")
        compiler = ("const fs=require('fs'),vm=require('vm');"
                    "const c=fs.readFileSync(process.argv[1],'utf8');"
                    "const f=new vm.Script('('+c+'\\n)').runInNewContext({}, {timeout:1000});"
                    "if(typeof f!=='function')process.exit(3);")
        try:
            result = self.runner([self.node, "-e", compiler, str(path)],
                                 capture_output=True, text=True, timeout=10)
            if result.returncode:
                raise AcceptanceError("Action function compilation failed")
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return path

    def execute(self, path):
        try:
            return action_result(self.call("run-code", "--filename", str(path)))
        finally:
            path.unlink(missing_ok=True)

    def run(self, code):
        return self.execute(self.prepare(code))

    def snapshot(self):
        result = self.call("snapshot")
        write_json(child_path(self.root, "latest-snapshot.json"), redact(result))
        return json.dumps(result, ensure_ascii=False)


class Controller:
    def __init__(self, cli, ledger, origin, send_selector):
        self.cli, self.ledger = cli, ledger
        self.origin = validate_origin(origin, ledger.mode)
        if not isinstance(send_selector, str) or not 1 <= len(send_selector) <= 128:
            raise AcceptanceError("Observed send selector required")
        self.selector = send_selector

    def code(self, body):
        return function("if(new URL(page.url()).origin !== " + json.dumps(self.origin)
                        + ") throw new Error('Unapproved origin');\n" + body)

    def inspect(self):
        self.cli.snapshot()
        return self.cli.run(self.code("""
return {acceptance_result: await page.evaluate(() => ({
 text: document.body.innerText,
 articles:[...document.querySelectorAll('article,[role="article"]')].map(a=>({text:a.innerText,
  parent:a.parentElement.className,grandparent:a.parentElement.parentElement.className})),
 buttons: [...document.querySelectorAll('button')].map(b => ({
  id:b.id, name:b.getAttribute('aria-label'), title:b.title,
  text:b.textContent, type:b.type, disabled:b.disabled
 })),
 links:[...document.querySelectorAll('a')].map(a => ({text:a.textContent,role:a.getAttribute('role')})),
 iframes:[...document.querySelectorAll('iframe')].map(f => ({title:f.title})),
 textboxCount:document.querySelectorAll('textarea').length
}))};
"""))

    def set_chat(self, chat):
        self.ledger.load()
        if chat not in ("A", "B"):
            raise AcceptanceError("Invalid conversation")
        if chat == "A" and any(v != "UNUSED" for v in self.ledger.data["slots"].values()):
            raise AcceptanceError("Cannot reset an active conversation")
        if chat == "B" and (self.ledger.data["slots"]["L4"] != "PASS"
                            or self.ledger.data["slots"]["L5"] != "UNUSED"):
            raise AcceptanceError("Conversation B seed is unavailable")
        self.ledger.data["chat"] = chat
        self.ledger.save()

    def new_chat(self, chat):
        # The DOM id is inspected on this page before it is used as a selector.
        observed = self.inspect()
        if not any(b.get("id") == "new-chat-button" for b in observed.get("buttons", [])):
            raise AcceptanceError("New-chat control not observed")
        self.ledger.load()
        if chat == "B" and (self.ledger.data["slots"]["L4"] != "PASS"
                            or self.ledger.data["slots"]["L5"] != "UNUSED"):
            raise AcceptanceError("Conversation A not accepted")
        if chat == "A" and any(s != "UNUSED" for s in self.ledger.data["slots"].values()):
            raise AcceptanceError("Cannot reset an active conversation")
        if chat not in ("A", "B"):
            raise AcceptanceError("Invalid conversation")
        if chat == "B":
            if "Create New Chat" not in observed.get("text", ""):
                self.cli.run(self.code("await page.locator('#new-chat-button').click();"
                                      "return {acceptance_result:{newChatClicked:true}};"))
            dialog_snapshot = self.cli.snapshot()
            if "Create New Chat" not in dialog_snapshot or "Confirm" not in dialog_snapshot:
                raise AcceptanceError("New-chat confirmation not observed")
            self.cli.run(self.code("const dialog=page.getByRole('dialog');"
                "await dialog.getByRole('heading',{name:'Create New Chat',exact:true}).waitFor();"
                "await dialog.getByRole('button',{name:'Confirm',exact:true}).click();"
                "return {acceptance_result:{confirmed:true}};"))
        result = self.cli.run(self.code("await page.getByRole('textbox',{name:"
            + json.dumps(TEXTBOX) + ",exact:true}).waitFor();"
            "const deadline=Date.now()+15000;while(Date.now()<deadline){"
            "const text=await page.locator('body').innerText();"
            "if(text.includes('Welcome, Guest!') && !"
            + json.dumps(list(QUESTIONS)) + ".some(q=>text.includes(q)))"
            "return {acceptance_result:{fresh:true}};await page.waitForTimeout(250);}"
            "return {acceptance_result:{fresh:false}};"))
        if result.get("fresh") is not True:
            raise AcceptanceError("Fresh conversation not established")
        self.set_chat(chat)
        return {"chat":chat,"fresh":True}

    def submit(self, slot):
        question = self.ledger.check(slot)
        snapshot = self.cli.snapshot()
        if TEXTBOX not in snapshot:
            raise AcceptanceError("Textbox not observed")
        common = ("const box=page.getByRole('textbox',{name:"
                  + json.dumps(TEXTBOX) + ",exact:true});\n"
                  "if(await box.count()!==1)throw new Error('Ambiguous textbox');\n")
        fill = self.cli.run(self.code(common + "await box.fill(" + json.dumps(question)
                                      + ");return {acceptance_result:{filled:true}};"))
        if fill.get("filled") is not True:
            raise AcceptanceError("Fill not confirmed")
        read = self.cli.run(self.code(common + "const send=page.locator("
            + json.dumps(self.selector) + ");\n"
            "return {acceptance_result:{value:await box.inputValue(),"
            "boxes:await box.count(),sends:await send.count(),"
            "enabled:await send.count()===1 && await send.isEnabled(),"
            "pending:await page.getByText('Working on your request…',{exact:true}).count()>0}};"))
        if (read.get("value") != question or read.get("boxes") != 1
                or read.get("sends") != 1 or read.get("enabled") is not True
                or read.get("pending") is not False):
            raise AcceptanceError("Exact ready input not verified")
        # Compile Enter BEFORE reservation; no fill/compiler failure can fall through.
        action = self.cli.prepare(self.code(common
            + "if(await box.inputValue()!==" + json.dumps(question)
            + ")throw new Error('Input changed');\n"
            "await box.press('Enter');return {acceptance_result:{dispatched:true}};"))
        try:
            self.ledger.reserve(slot)
        except Exception:
            action.unlink(missing_ok=True)
            raise
        try:
            result = self.cli.execute(action)
            if result.get("dispatched") is not True:
                raise AcceptanceError("Submission uncertain")
        except Exception:
            self.ledger.state(slot, "UNCERTAIN")
            raise
        self.ledger.state(slot, "SUBMITTED")
        return result

    def read_source(self, name, required):
        """Wait for inspected source text without clicking or consuming another open.

        A viewer heading can appear before PDF text finishes loading. Callers pass
        independently verified record fragments; a heading alone is not evidence.
        """
        if (not isinstance(name, str) or not name or not isinstance(required, list)
                or not required or any(not isinstance(t, str) or not t for t in required)):
            raise AcceptanceError("Expected source record fragments required")
        return self.cli.run(self.code(
            "const panel=page.getByRole('complementary');"
            "await panel.getByText(" + json.dumps(name) + ",{exact:true}).waitFor({state:'visible'});"
            "const required=" + json.dumps(required) + ";"
            "const deadline=Date.now()+10000;"
            "while(Date.now()<deadline){const text=await panel.innerText();"
            "if(required.every(t=>text.includes(t)))"
            "return {acceptance_result:{verified:true,panelText:text}};"
            "await page.waitForTimeout(250);}"
            "throw new Error('Expected source content did not finish loading');"))

    def source_action(self, role, name, filename=None):
        if role not in ("button", "link") or not isinstance(name, str) or not name:
            raise AcceptanceError("Observed source control required")
        snapshot = self.cli.snapshot()
        if name not in snapshot:
            raise AcceptanceError("Source control not observed")
        target = "page.getByRole(" + json.dumps(role) + ",{name:" + json.dumps(name) + ",exact:true})"
        prepare = self.cli.run(self.code("const control=" + target
            + ";return {acceptance_result:{count:await control.count()}};"))
        if prepare.get("count") != 1:
            raise AcceptanceError("Ambiguous source control")
        if filename is None:
            body = ("await " + target + ".click();"
                    "const panel=page.getByRole('complementary');"
                    "await panel.getByText(" + json.dumps(name) + ",{exact:true}).waitFor({state:'visible'});"
                    "return {acceptance_result:{opened:true,panelText:await panel.innerText()}};")
        else:
            dest = child_path(self.cli.root, filename)
            if dest.exists():
                raise AcceptanceError("Download destination already exists")
            body = ("const waiting=page.waitForEvent('download',{timeout:15000});"
                    "await " + target + ".click();const download=await waiting;"
                    "await download.saveAs(" + json.dumps(str(dest)) + ");"
                    "return {acceptance_result:{downloaded:true}};")
        action = self.cli.prepare(self.code(body))
        try:
            self.ledger.counter("source_opens" if filename is None else "downloads")
        except Exception:
            action.unlink(missing_ok=True)
            raise
        return self.cli.execute(action)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--cli-sha256", required=True)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--session", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--mode", choices=["local", "live"], default="local")
    parser.add_argument("--send-selector", default="#chat-submit")
    parser.add_argument("command", choices=["open", "snapshot", "inspect", "send", "pass", "chat", "source", "download", "close"])
    parser.add_argument("arguments", nargs="*")
    args = parser.parse_args(argv)
    origin = validate_origin(args.base_url, args.mode)
    ledger = Ledger(args.root / "attempts.json", args.mode)
    cli = CLI(shutil.which("node"), args.cli, args.root, args.session, args.cli_sha256)
    driver = Controller(cli, ledger, origin, args.send_selector)
    if args.command == "open":
        config = {"browser":{"browserName":"chromium","isolated":True,
                             "launchOptions":{"channel":"msedge","headless":True},
                             "contextOptions":{"acceptDownloads":True,"viewport":{"width":1440,"height":1100}}},
                  "outputDir":str(cli.root), "outputMode":"stdout", "console":{"level":"error"},
                  "network":{"allowedOrigins":[origin]},
                  "timeouts":{"action":10000,"navigation":20000}}
        write_json(cli.root / "browser-config.json", config)
        result = cli.call("open", origin + "/", "--config", str(cli.root / "browser-config.json"))
    elif args.command == "snapshot":
        result = json.loads(cli.snapshot())
    elif args.command == "inspect":
        result = driver.inspect()
    elif args.command == "send":
        result = driver.submit(args.arguments[0])
    elif args.command == "pass":
        ledger.state(args.arguments[0], "PASS")
        result = {"state":"PASS"}
    elif args.command == "chat":
        result = driver.new_chat(args.arguments[0])
    elif args.command in ("source", "download"):
        result = driver.source_action(*args.arguments)
    else:
        result = cli.call("close")
    print(json.dumps(redact(result), ensure_ascii=True))


if __name__ == "__main__":
    main()
