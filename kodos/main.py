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

        # This is the current regex object
        self.regex = None
        self.matchFormat = QTextCharFormat()
        self.matchFormat.setForeground(QColor('blue'))

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
            widget.textChanged.connect(self.onComputeRegex)

        self.matchNumberBox.valueChanged.connect(self.onMatchNumberChange)

    def getSearchText(self):
        """Shortcut to retrieve the serach text"""

        return str(self.searchText.toPlainText().toUtf8())

    def formatMatchedText(self, document, match):
        """Format the matched text in a document"""

        cursor = QTextCursor(document)
        cursor.setPosition(match.start())
        cursor.movePosition(
            QTextCursor.NextCharacter,
            QTextCursor.KeepAnchor,
            match.end() - match.start())
        cursor.setCharFormat(self.matchFormat)

    def onComputeRegex(self):
        regex   = str(self.regexText.toPlainText().toUtf8())
        search  = self.getSearchText()
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
            self.regex = None
            self.statusbar.showMessage("Pattern does not match")
            self.statusbar.setIndicator('error')
            return

        self.regex = r

        # The regex match the input!
        self.matchText.setPlainText(search)
        self.matchAllText.setPlainText(search)

        # Compute results in the various result panels
        for i, match in enumerate(r.finditer(search)):
            # Update the select match number widget

            # Update the matchAll text widget
            self.formatMatchedText(self.matchAllText.document(), match)

        self.matchNumberBox.setRange(1, i + 1)
        self.matchNumberBox.valueChanged.emit(self.matchNumberBox.value())

        self.statusbar.setIndicator('ok')
        self.statusbar.showMessage("Pattern matches (found %d match)" % (i + 1))

    def onMatchNumberChange(self, matchNumber):
        # Set default format on the whole text before highlighting the selected
        # match.
        document = self.matchText.document()
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.setCharFormat(QTextCharFormat())

        search = self.getSearchText()
        for i, match in enumerate(self.regex.finditer(search)):
            if i + 1 == matchNumber:
                self.formatMatchedText(document, match)
                break


def run(args=None):
    """Main entry point of the application."""

    app = QApplication(sys.argv)
    kodos = KodosMainWindow()
    kodos.show()
    app.exec_()
