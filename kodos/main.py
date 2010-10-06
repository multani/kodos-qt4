import sys

from PyQt4.QtGui import QApplication, QMainWindow

from kodos import widgets
from kodos.ui.ui_main import Ui_MainWindow



class KodosMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(KodosMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.connectActions()

        # Trigger the textChanged signal
        for widget in [self.regexText, self.searchText, self.replaceText]:
            widget.setPlainText('')

    def setupUi(self, *args, **kwargs):
        super(KodosMainWindow, self).setupUi(*args, **kwargs)
        self.statusbar = widgets.StatusBar(self._statusbar)

    def connectActions(self):
        # Connect input widgets to update the GUI when their text change
        for widget in [self.regexText, self.searchText, self.replaceText]:
            widget.textChanged.connect(self.on_compute_regex)

    def on_compute_regex(self):
        regex = self.regexText.toPlainText()
        search = self.searchText.toPlainText()
        replace = self.replaceText.toPlainText()

        if regex == "" or search == "":
            self.statusbar.showMessage(
                "Enter a regular expression and a string to match against")
            self.statusbar.setIndicator('warning')
        else:
            self.statusbar.showMessage("")
            self.statusbar.setIndicator('ok')


def run(args=None):
    """Main entry point of the application."""

    app = QApplication(sys.argv)
    kodos = KodosMainWindow()
    kodos.show()
    app.exec_()
