import re

with open("src/engine/parser/move.py", "r") as f:
    content = f.read()

content = content.replace("@dataclass\nclass Point2D:", "@dataclass(slots=True)\nclass Point2D:")
content = content.replace("@dataclass\nclass Point3D:", "@dataclass(slots=True)\nclass Point3D:")
content = content.replace("@dataclass\nclass Move:", "@dataclass(slots=True)\nclass Move:")

with open("src/engine/parser/move.py", "w") as f:
    f.write(content)

print("move.py patched!")
