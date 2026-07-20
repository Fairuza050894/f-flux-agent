from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(f"dashboard.html.backup_before_force_template_mode_setup_{timestamp}")
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text()

force_js = r'''
    window.addEventListener("DOMContentLoaded", function () {
      setTimeout(function () {
        try {
          if (typeof setupCustomTemplateModes === "function") {
            setupCustomTemplateModes();
          }
        } catch (error) {
          console.error("Failed to setup template mode UI:", error);
        }
      }, 500);
    });

    window.addEventListener("load", function () {
      setTimeout(function () {
        try {
          if (typeof setupCustomTemplateModes === "function") {
            setupCustomTemplateModes();
          }
        } catch (error) {
          console.error("Failed to setup template mode UI on window load:", error);
        }
      }, 1000);
    });

'''

if "Failed to setup template mode UI" not in text:
    text = text.replace("</script>", force_js + "\n  </script>", 1)
    HTML_PATH.write_text(text)
    print("Inserted forced setupCustomTemplateModes trigger")
else:
    print("Forced setupCustomTemplateModes trigger already exists")

print(f"Backup created: {backup_path}")
