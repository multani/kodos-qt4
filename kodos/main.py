import re
import sys

from PyQt4 import QtCore
from PyQt4 import uic
from PyQt4.QtGui import QApplication, QMainWindow
from PyQt4.QtGui import QTextCursor, QTextCharFormat, QColor

from kodos import model
from kodos import widgets


class KodosMainWindow(QtCore.QObject):

    validRegex = QtCore.pyqtSignal()
    invalidRegex = QtCore.pyqtSignal(str, str)

    def __init__(self):
        super(KodosMainWindow, self).__init__()
        self.ui = uic.loadUi('main.ui')
        self.setupUi()

        # This is the current regex object
        self.regex = None
        self.matchFormat = QTextCharFormat()
        self.matchFormat.setForeground(QColor('blue'))
        self.ui.groupsView.setModel(
            model.SimpleTableModel(["Group Name", "Match"]))

        # Read-only mapping to explain what each flags do
        self.flagsRelationships = {
            self.ui.dotAllFlag     : re.DOTALL,
            self.ui.ignoreCaseFlag : re.IGNORECASE,
            self.ui.localeFlag     : re.LOCALE,
            self.ui.multiLineFlag  : re.MULTILINE,
            self.ui.unicodeFlag    : re.UNICODE,
            self.ui.verboseFlag    : re.VERBOSE,
        }

        self.connectActions()

    def show(self):
        self.ui.show()

    def setupUi(self, *args, **kwargs):
        # Trigger the textChanged signal
        for widget in [self.ui.regexText, self.ui.searchText, self.ui.replaceText]:
            widget.setPlainText('')

        self.statusbar = widgets.StatusBar(self.ui._statusbar)
        self.ui.labelReplace.hide()
        self.ui.replaceNumberBox.hide()
        self.ui.replaceNumberBox.setRange(0 ,0)

    def connectActions(self):

        self.validRegex.connect(self.onValidRegex)
        self.invalidRegex.connect(self.onInvalidRegex)

        # Connect input widgets to update the GUI when their text change
        for widget in [self.ui.regexText, self.ui.searchText, self.ui.replaceText]:
            widget.textChanged.connect(self.onComputeRegex)

        for widget in self.flagsRelationships:
            widget.stateChanged.connect(self.onComputeRegex)

        self.ui.replaceText.textChanged.connect(self.onReplaceChange)

        self.ui.matchNumberBox.valueChanged.connect(self.onMatchNumberChange)
        self.ui.replaceNumberBox.valueChanged.connect(self.onReplaceNumberChange)

    def getSearchText(self):
        """Shortcut to retrieve the search text"""

        return str(self.ui.searchText.toPlainText().toUtf8())

    def getReplaceText(self):
        """Shortcut to retrieve the replace text"""

        return str(self.ui.replaceText.toPlainText().toUtf8())

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
        self.ui.groupsView.model().clear()
        self.ui.matchText.setPlainText("")
        self.ui.matchAllText.setPlainText("")
        self.ui.replaceResultText.setPlainText("")
        self.ui.matchNumberBox.setEnabled(False)
        self.ui.replaceNumberBox.setEnabled(False)

        self.statusbar.showMessage(message)
        self.statusbar.setIndicator(indicator)

    def onValidRegex(self):
        search  = self.getSearchText()

        self.ui.matchText.setPlainText(search)
        self.ui.matchAllText.setPlainText(search)
        self.ui.matchNumberBox.setEnabled(True)
        self.ui.replaceNumberBox.setEnabled(True)

        # Compute results in the various result panels
        for i, match in enumerate(self.regex.finditer(search)):
            self.formatMatchedText(self.ui.matchAllText.document(), match)

        nbMatches = i + 1
        self.ui.matchNumberBox.setRange(1, nbMatches)
        self.ui.matchNumberBox.valueChanged.emit(self.ui.matchNumberBox.value())

        # 0 means replace everything
        self.ui.replaceNumberBox.setRange(0, nbMatches)
        self.ui.replaceNumberBox.valueChanged.emit(self.ui.replaceNumberBox.value())

        self.statusbar.setIndicator('ok')
        self.statusbar.showMessage(
            "Pattern matches (found %d match)" % nbMatches)

    def getRegexFlags(self):
        """Return the flags set for the regex"""

        flags = 0
        for flag, value in self.flagsRelationships.iteritems():
            if flag.isChecked():
                flags |= value

        return flags

    def onComputeRegex(self):
        regex   = str(self.ui.regexText.toPlainText().toUtf8())
        search  = self.getSearchText()

        if regex == "" or search == "":
            return self.invalidRegex.emit(
                "Enter a regular expression and a string to match against",
                'warning')

        flags = self.getRegexFlags()

        try:
            self.regex = re.compile(regex, flags)
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
        document = self.ui.matchText.document()
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

        model = self.ui.groupsView.model()
        model.clear()

        # Create a reversed self.regex.groupindex dictionnary
        groupsIndexes = dict((v, k)
                             for (k, v) in self.regex.groupindex.iteritems())

        for i in range(1, self.regex.groups + 1):
            groupName = groupsIndexes.get(i, "")
            groupValue = match.group(i)
            model.append((groupName, groupValue))

    def onReplaceChange(self):
        replace = str(self.ui.replaceText.toPlainText().toUtf8())

        if replace:
            self.ui.labelReplace.show()
            self.ui.replaceNumberBox.show()
            self.ui.replaceResultText.setEnabled(True)
        else:
            self.ui.labelReplace.hide()
            self.ui.replaceNumberBox.hide()
            self.ui.replaceResultText.setPlainText("")
            self.ui.replaceResultText.setEnabled(False)

    def onReplaceNumberChange(self, replaceNumber):
        text = self.regex.sub(
            self.getReplaceText(),
            self.getSearchText(),
            replaceNumber)
        self.ui.replaceResultText.setPlainText(text)


def run(args=None):
    """Main entry point of the application."""

    app = QApplication(sys.argv)
    kodos = KodosMainWindow()
    kodos.show()
    app.exec_()
