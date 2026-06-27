import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
import pyqtgraph.opengl as gl

app = QApplication(sys.argv)

main_view = gl.GLViewWidget()
main_view.resize(800, 600)
main_view.show()

axis_view = gl.GLViewWidget(main_view)
axis_view.resize(100, 100)
axis_item = gl.GLAxisItem(glOptions='opaque')
axis_item.setSize(x=10, y=10, z=10)
axis_view.addItem(axis_item)
axis_view.opts['distance'] = 25
axis_view.opts['center'] = gl.pg.Vector(0,0,0)
axis_view.move(10, 600 - 110)
axis_view.show()
# No background
axis_view.setStyleSheet("background: transparent;")

def sync_cameras():
    axis_view.opts['azimuth'] = main_view.opts['azimuth']
    axis_view.opts['elevation'] = main_view.opts['elevation']
    axis_view.update()

# override main view's update to sync
old_update = main_view.update
def new_update(*args, **kwargs):
    sync_cameras()
    old_update(*args, **kwargs)
main_view.update = new_update

