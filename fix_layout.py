def replace_in_file(filepath, old, new):
    with open(filepath, "r") as f:
        content = f.read()
    with open(filepath, "w") as f:
        f.write(content.replace(old, new))

# Fix FileUploadWidget size policy
replace_in_file("src/ui/widgets/file_upload_widget.py", 
                "self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)", 
                "self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)")
replace_in_file("src/ui/widgets/file_upload_widget.py", 
                "self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)", 
                "self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)")

# Fix ProfileSelectorWidget size policy
replace_in_file("src/ui/widgets/profile_selector_widget.py", 
                "self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)", 
                "self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)")

# Remove QComboBox::down-arrow hack
down_arrow_hack = """    QComboBox::down-arrow {
        image: none;
        border: none;
        width: 0;
        height: 0;
    }"""
replace_in_file("src/ui/widgets/profile_selector_widget.py", down_arrow_hack, "")

# Fix OptimizationControls size policy & emojis
replace_in_file("src/ui/widgets/optimization_controls.py", 
                "self.setObjectName('OptimizationControls')", 
                "self.setObjectName('OptimizationControls')\n        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)")
replace_in_file("src/ui/widgets/optimization_controls.py", "⚡ OPTIMIZE", "OPTIMIZE")
replace_in_file("src/ui/widgets/optimization_controls.py", "💾 EXPORT G-CODE", "EXPORT G-CODE")

print("Fixed")
