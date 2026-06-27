import re

# geometry_analyzer.py
with open("src/engine/analysis/geometry_analyzer.py", "r") as f:
    content = f.read()
content = content.replace("@dataclass\nclass AnalyzedMove:", "@dataclass(slots=True)\nclass AnalyzedMove:")
with open("src/engine/analysis/geometry_analyzer.py", "w") as f:
    f.write(content)

# pressure_optimizer.py
with open("src/engine/optimizer/pressure_optimizer.py", "r") as f:
    content = f.read()
content = content.replace("@dataclass\nclass Modification:", "@dataclass(slots=True)\nclass Modification:")
with open("src/engine/optimizer/pressure_optimizer.py", "w") as f:
    f.write(content)

print("Slots patched!")
