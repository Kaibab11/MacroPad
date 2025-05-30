import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

def create_app():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Macro Pad Configurator")
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())


