with open("src/ui/main_window.py", "r") as f:
    content = f.read()

bad_str = "self.setMinimumSize(1400, 1100)\\n        self.resize(1400, 1100)"
good_str = "self.setMinimumSize(1400, 1100)\n        self.resize(1400, 1100)"

if bad_str in content:
    content = content.replace(bad_str, good_str)
    with open("src/ui/main_window.py", "w") as f:
        f.write(content)
    print("Fixed syntax error!")
else:
    print("Could not find bad string.")
