import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# 1. Add axis widget init
init_old = """            self._grid_item.setColor((grid_c.redF(), grid_c.greenF(), grid_c.blueF(), 0.3))
            self.addItem(self._grid_item)
            
            self._sim_time_sec = -1.0"""
init_new = """            self._grid_item.setColor((grid_c.redF(), grid_c.greenF(), grid_c.blueF(), 0.3))
            self.addItem(self._grid_item)
            
            # Setup mini axis widget in corner
            self._axis_widget = gl.GLViewWidget(self)
            self._axis_widget.setFixedSize(80, 80)
            self._axis_widget.setBackgroundColor(QColor(0,0,0,0)) # Transparent
            self._axis_item = gl.GLAxisItem()
            self._axis_item.setSize(x=5, y=5, z=5)
            self._axis_widget.addItem(self._axis_item)
            self._axis_widget.opts['distance'] = 15
            self._axis_widget.opts['center'] = pg.Vector(0,0,0)
            self._axis_widget.setMouseTracking(False)
            self._axis_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._axis_widget.show()
            
            self._sim_time_sec = -1.0"""
content = content.replace(init_old, init_new)

# 2. Add resizeEvent and update intercept
methods = """
        def resizeEvent(self, ev):
            super().resizeEvent(ev)
            # Position axis widget in bottom-right corner
            self._axis_widget.move(self.width() - 90, self.height() - 90)

        def update(self):
            super().update()
            if hasattr(self, '_axis_widget'):
                self._axis_widget.opts['azimuth'] = self.opts['azimuth']
                self._axis_widget.opts['elevation'] = self.opts['elevation']
                self._axis_widget.update()
"""
# insert before mouseMoveEvent
content = content.replace("        def mouseMoveEvent(self, ev):", methods + "\n        def mouseMoveEvent(self, ev):")

# 3. Fix orbit inverted up/down as requested ("invert the up and down")
# Currently it is: self.orbit(-diff.x(), -diff.y())
# User wants up and down inverted from what it is right now. So it should be `diff.y()`.
content = content.replace("self.orbit(-diff.x(), -diff.y())", "self.orbit(-diff.x(), diff.y())")

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)

print("Applied changes")
