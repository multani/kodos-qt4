import re
import sys

from PyQt4 import QtCore
from PyQt4.QtGui import QApplication, QMainWindow
from PyQt4.QtGui import QTextCursor, QTextCharFormat, QColor

from kodos import widgets, model
from kodos.ui.ui_main import Ui_MainWindow



class KodosMainWindow(QMainWindow, Ui_MainWindow):

    validRegex = QtCore.pyqtSignal()
    invalidRegex = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(KodosMainWindow, self).__init__(parent)
        self.setupUi(self)

        # This is the current regex object
        self.regex = None
        self.matchFormat = QTextCharFormat()
        self.matchFormat.setForeground(QColor('blue'))
        self.groupsView.setModel(
            model.SimpleTableModel(["Group Name", "Match"]))

        self.connectActions()

        # Trigger the textChanged signal
        for widget in [self.regexText, self.searchText, self.replaceText]:
            widget.setPlainText('')

    def setupUi(self, *args, **kwargs):
        super(KodosMainWindow, self).setupUi(*args, **kwargs)
        self.statusbar = widgets.StatusBar(self._statusbar)

    def connectActions(self):

        self.validRegex.connect(self.onValidRegex)
        self.invalidRegex.connect(self.onInvalidRegex)

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

    def onInvalidRegex(self, message, indicator):
        self.groupsView.model().clear()
        self.matchText.setPlainText("")
        self.matchAllText.setPlainText("")
        self.matchNumberBox.setDisabled(True)

        self.statusbar.showMessage(message)
        self.statusbar.setIndicator(indicator)

    def onValidRegex(self):
        search  = self.getSearchText()

        self.matchText.setPlainText(search)
        self.matchAllText.setPlainText(search)
        self.matchNumberBox.setEnabled(True)

        # Compute results in the various result panels
        for i, match in enumerate(self.regex.finditer(search)):
            # Update the matchAll text widget
            self.formatMatchedText(self.matchAllText.document(), match)

        self.matchNumberBox.setRange(1, i + 1)
        self.matchNumberBox.valueChanged.emit(self.matchNumberBox.value())

        self.statusbar.setIndicator('ok')
        self.statusbar.showMessage("Pattern matches (found %d match)" % (i + 1))

    def onComputeRegex(self):
        regex   = str(self.regexText.toPlainText().toUtf8())
        search  = self.getSearchText()
        replace = str(self.replaceText.toPlainText().toUtf8())

        if regex == "" or search == "":
            return self.invalidRegex.emit(
                "Enter a regular expression and a string to match against",
                'warning')

        try:
            self.regex = re.compile(regex)
        except (re.error, IndexError), e:
            # IndexError occured if the regex is "(?P<>)"
            return self.invalidRegex.emit(e.args[0], 'error')

        match = self.regex.search(search)
        if match is None:
            return self.invalidRegex.emit("Pattern does not match", 'error')

        # The regex matches the input!
        self.validRegex.emit()


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
                break
        else:
            assert False, ("We didn't find a match?! (RE=%r, text=%r" %
                           (self.regex.pattern, search))

        self.formatMatchedText(document, match)

        model = self.groupsView.model()
        model.clear()

        # Create a reversed self.regex.groupindex dictionnary
        groupsIndexes = dict((v, k)
                             for (k, v) in self.regex.groupindex.iteritems())

        for i in range(1, self.regex.groups + 1):
            groupName = groupsIndexes.get(i, "")
            groupValue = match.group(i)
            model.append((groupName, groupValue))


def run(args=None):
    """Main entry point of the application."""

    app = QApplication(sys.argv)
    kodos = KodosMainWindow()
    kodos.show()
    app.exec_()
