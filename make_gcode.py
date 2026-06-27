with open("test.gcode", "w") as f:
    f.write("; FLAVOR:Marlin\n")
    f.write("; LAYER_COUNT:100\n")
    for layer in range(100):
        f.write(f"; LAYER:{layer}\n")
        f.write(f"G0 X{layer} Y{layer} Z{layer * 0.2}\n")
        for i in range(1000):
            f.write(f"G1 X{layer + i/1000.0} Y{layer + i/1000.0} E{0.05} F1200\n")
print("test.gcode created (100,000+ lines)")
