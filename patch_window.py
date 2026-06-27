with open("src/ui/main_window.py", "r") as f:
    content = f.read()

old_size = "self.setMinimumSize(1280, 850)"
new_size = "self.setMinimumSize(1400, 1100)\\n        self.resize(1400, 1100)"

if old_size in content:
    content = content.replace(old_size, new_size)
    with open("src/ui/main_window.py", "w") as f:
        f.write(content)
    print("Patched window size")
else:
    print("Could not find old window size")
