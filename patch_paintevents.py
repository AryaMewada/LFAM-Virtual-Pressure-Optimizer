import os
import re

files_to_patch = [
    "src/ui/widgets/layer_viewer_widget.py",
    "src/ui/widgets/results_panel.py",
    "src/ui/widgets/loading_overlay.py",
    "src/ui/widgets/analysis_panel.py",
    "src/ui/widgets/pressure_chart_widget.py",
    "src/ui/widgets/file_upload_widget.py",
]

for filepath in files_to_patch:
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the line with "def paintEvent(self, event):"
    match = re.search(r'([ \t]+)def paintEvent\(self, event\):', content)
    if not match:
        continue
        
    indent = match.group(1)
    
    # We replace "def paintEvent(self, event):" with:
    # def paintEvent(self, event):
    #     try:
    #         self._safe_paintEvent(event)
    #     except Exception as e:
    #         with open("paintevent_error.txt", "a") as errf:
    #             errf.write(f"Error in {filepath}: {str(e)}\n")
    #
    # def _safe_paintEvent(self, event):
    
    new_def = f"{indent}def paintEvent(self, event):\n{indent}    try:\n{indent}        self._safe_paintEvent(event)\n{indent}    except Exception as e:\n{indent}        import traceback\n{indent}        with open('paintevent_error.txt', 'a') as errf:\n{indent}            errf.write(f'Error in {filepath}: {{str(e)}}\\n{{traceback.format_exc()}}\\n')\n\n{indent}def _safe_paintEvent(self, event):"
    
    content = content.replace(f"{indent}def paintEvent(self, event):", new_def)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Patched {filepath}")
