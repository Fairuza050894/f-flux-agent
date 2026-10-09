from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(f"dashboard.html.backup_before_fix_template_autoload_{timestamp}")
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text()

old_exact = """    async function init() {
      await loadHealth();
      await loadFeatures();
      await loadHistory();
    }"""

new_exact = """    async function init() {
      await loadHealth();
      await loadFeatures();
      await loadHistory();
      await loadTemplates();
    }"""

if old_exact in text:
    text = text.replace(old_exact, new_exact, 1)
    print("Patched init exact block: added loadTemplates()")
else:
    pattern = r"(async function init\(\) \{(?P<body>.*?)\n    \})"
    match = re.search(pattern, text, flags=re.S)

    if not match:
        raise RuntimeError("init() function not found in dashboard.html")

    block = match.group(1)

    if "await loadTemplates();" in block:
        print("init() already contains loadTemplates()")
    else:
        if "await loadHistory();" in block:
            patched_block = block.replace(
                "await loadHistory();",
                "await loadHistory();\n      await loadTemplates();",
                1,
            )
        else:
            patched_block = block.replace(
                "\n    }",
                "\n      await loadTemplates();\n    }",
                1,
            )

        text = text.replace(block, patched_block, 1)
        print("Patched init regex block: added loadTemplates()")

HTML_PATH.write_text(text)

print(f"Backup created: {backup_path}")
