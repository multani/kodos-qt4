import re
import sys

from PyQt4.QtGui import QApplication, QMainWindow
from PyQt4.QtGui import QTextCursor, QTextCharFormat, QColor

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

        self.matchNumberBox.valueChanged.connect(self.on_match_number_change)

    def on_compute_regex(self):
        regex   = str(self.regexText.toPlainText().toUtf8())
        search  = str(self.searchText.toPlainText().toUtf8())
        replace = str(self.replaceText.toPlainText().toUtf8())

        if regex == "" or search == "":
            self.statusbar.showMessage(
                "Enter a regular expression and a string to match against")
            self.statusbar.setIndicator('warning')
            return

        # We can compile the regex
        # TODO: check the error at compilation
        r = re.compile(regex)
        match = r.search(search)
        if match is None:
            self.statusbar.showMessage("Pattern does not match")
            self.statusbar.setIndicator('error')
            return

        # The regex match the input!
        self.matchNumberBox.setMinimum(1)
        self.matchText.setPlainText(search)
        self.matchAllText.setPlainText(search)


        # Compute results in the various result panels
        for i, match in enumerate(r.finditer(search)):
            # Update the select match number widget
            self.matchNumberBox.setMaximum(i + 1)

            # Update the matchAll text widget
            format = QTextCharFormat()
            format.setForeground(QColor('blue'))

            cursor = QTextCursor(self.matchAllText.document())
            cursor.setPosition(match.start())
            cursor.movePosition(
                QTextCursor.NextCharacter,
                QTextCursor.KeepAnchor,
                match.end() - match.start())
            cursor.setCharFormat(format)


        self.statusbar.setIndicator('ok')
        self.statusbar.showMessage("Pattern matches (found %d match)" % (i + 1))

    def on_match_number_change(self, match_number):
        # Set default format on the whole text before highlighting the selected
        # match.
        cursor = QTextCursor(self.matchText.document())
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.setCharFormat(QTextCharFormat())


        # TODO: this needs to be refactored with the on_compute_regex() method
        # to avoid duplication.
        regex   = str(self.regexText.toPlainText().toUtf8())
        search  = str(self.searchText.toPlainText().toUtf8())
        r = re.compile(regex)
        for i, match in enumerate(r.finditer(search)):
            if i+1 != match_number:
                continue

            format = QTextCharFormat()
            format.setForeground(QColor('blue'))

            cursor = QTextCursor(self.matchText.document())
            cursor.setPosition(match.start())
            cursor.movePosition(
                QTextCursor.NextCharacter,
                QTextCursor.KeepAnchor,
                match.end() - match.start())
            cursor.setCharFormat(format)

            break


def run(args=None):
    """Main entry point of the application."""

    app = QApplication(sys.argv)
    kodos = KodosMainWindow()
    kodos.show()
    app.exec_()
