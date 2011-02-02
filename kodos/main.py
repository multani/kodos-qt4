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

        # Read-only mapping to explain what each flags do
        self.flagsRelationships = {
            self.dotAllFlag     : re.DOTALL,
            self.ignoreCaseFlag : re.IGNORECASE,
            self.localeFlag     : re.LOCALE,
            self.multiLineFlag  : re.MULTILINE,
            self.unicodeFlag    : re.UNICODE,
            self.verboseFlag    : re.VERBOSE,
        }

        self.connectActions()

    def setupUi(self, *args, **kwargs):
        super(KodosMainWindow, self).setupUi(*args, **kwargs)

        # Trigger the textChanged signal
        for widget in [self.regexText, self.searchText, self.replaceText]:
            widget.setPlainText('')

        self.statusbar = widgets.StatusBar(self._statusbar)
        self.labelReplace.hide()
        self.replaceNumberBox.hide()
        self.replaceNumberBox.setRange(0 ,0)

    def connectActions(self):

        self.validRegex.connect(self.onValidRegex)
        self.invalidRegex.connect(self.onInvalidRegex)

        # Connect input widgets to update the GUI when their text change
        for widget in [self.regexText, self.searchText, self.replaceText]:
            widget.textChanged.connect(self.onComputeRegex)

        for widget in self.flagsRelationships:
            widget.stateChanged.connect(self.onComputeRegex)

        self.replaceText.textChanged.connect(self.onReplaceChange)

        self.matchNumberBox.valueChanged.connect(self.onMatchNumberChange)
        self.replaceNumberBox.valueChanged.connect(self.onReplaceNumberChange)

    def getSearchText(self):
        """Shortcut to retrieve the search text"""

        return str(self.searchText.toPlainText().toUtf8())

    def getReplaceText(self):
        """Shortcut to retrieve the replace text"""

        return str(self.replaceText.toPlainText().toUtf8())

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
        self.replaceResultText.setPlainText("")
        self.matchNumberBox.setEnabled(False)
        self.replaceNumberBox.setEnabled(False)

        self.statusbar.showMessage(message)
        self.statusbar.setIndicator(indicator)

    def onValidRegex(self):
        search  = self.getSearchText()

        self.matchText.setPlainText(search)
        self.matchAllText.setPlainText(search)
        self.matchNumberBox.setEnabled(True)
        self.replaceNumberBox.setEnabled(True)

        # Compute results in the various result panels
        for i, match in enumerate(self.regex.finditer(search)):
            self.formatMatchedText(self.matchAllText.document(), match)

        nbMatches = i + 1
        self.matchNumberBox.setRange(1, nbMatches)
        self.matchNumberBox.valueChanged.emit(self.matchNumberBox.value())

        # 0 means replace everything
        self.replaceNumberBox.setRange(0, nbMatches)
        self.replaceNumberBox.valueChanged.emit(self.replaceNumberBox.value())

        self.statusbar.setIndicator('ok')
        self.statusbar.showMessage(
            "Pattern matches (found %d match)" % nbMatches)

        self.populateSampleCode()

    def getRegexFlags(self):
        """Return the flags set for the regex"""

        flags = 0
        for flag, value in self.flagsRelationships.iteritems():
            if flag.isChecked():
                flags |= value

        return flags

    def onComputeRegex(self):
        regex   = str(self.regexText.toPlainText().toUtf8())
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

    def onReplaceChange(self):
        replace = str(self.replaceText.toPlainText().toUtf8())

        if replace:
            self.labelReplace.show()
            self.replaceNumberBox.show()
            self.replaceResultText.setEnabled(True)
        else:
            self.labelReplace.hide()
            self.replaceNumberBox.hide()
            self.replaceResultText.setPlainText("")
            self.replaceResultText.setEnabled(False)

    def onReplaceNumberChange(self, replaceNumber):
        text = self.regex.sub(
            self.getReplaceText(),
            self.getSearchText(),
            replaceNumber)
        self.replaceResultText.setPlainText(text)

    def populateSampleCode(self):

        flagsValues = {
            self.dotAllFlag     : ('re.DOTALL', 's'),
            self.ignoreCaseFlag : ('re.IGNORECASE', 'i'),
            self.localeFlag     : ('re.LOCALE', 'L'),
            self.multiLineFlag  : ('re.MULTILINE', 'm'),
            self.unicodeFlag    : ('re.UNICODE', 'u'),
            self.verboseFlag    : ('re.VERBOSE', 'x'),
        }

        code = []
        code += ["import re", "", "# common variables", ""]
        code.append('rawstr = r"""%s"""' % self.regex.pattern)
        code.append('embedded_rawstr = r"""%s"""' % XX)
matchstr = """foo bar"""

# method 1: using a compile object
compile_obj = re.compile(rawstr)
match_obj = compile_obj.search(matchstr)

# method 2: using search function (w/ external flags)
match_obj = re.search(rawstr, matchstr)

# method 3: using search function (w/ embedded flags)
match_obj = re.search(embedded_rawstr, matchstr)

# Replace string
newstr = compile_obj.subn('f', 1)


def run(args=None):
    """Main entry point of the application."""

    app = QApplication(sys.argv)
    kodos = KodosMainWindow()
    kodos.show()
    app.exec_()
