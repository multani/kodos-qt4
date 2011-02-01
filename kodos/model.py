from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant
from PyQt4.QtCore import Qt


class SimpleTableModel(QAbstractTableModel):
    """Implement a simple table model around a list.

    AFAIK, PyQt4 doesn't provide an easy way to have a table model, so here it
    is.
    It's a very basic, non-performant, really limited version of a table model,
    but really sufficient for the needs of Kodos.

    The first part of the class implements the QAbstractTableModel API that
    needs to be implemented, whereas the second part implements a sane API.

    This is adapted from the Qt4's documentation's example "Address Book
    Example", which can be found online at
    http://doc.qt.nokia.com/4.6/itemviews-addressbook.html (thanks a lot, I
    couldn't have done anything without this...).

    """

    def __init__(self, headers, *args, **kwargs):
        """Create a table model with the specified columns names"""

        super(self.__class__, self).__init__(*args, **kwargs)

        self._headers = headers
        self._data = []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            # Per Qt4 doc.
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            # Per Qt4 doc.
            return 0
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            # The caller wants to display the name of the column specified
            return self._headers[section]
        return QVariant()

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # Return the data at the specified (x,y) location
            row = self._data[index.row()]
            return row[index.column()]

        return QVariant()

    def setData(self, index, value, role):
        if index.isValid() and role == Qt.EditRole:
            row = index.row()
            column = index.column()
            # value is a QVariant
            value = value.toString()
            self._data[row][column] = value
            self.dataChanged.emit(index, index)
            return True
        else:
            return False

    def insertRows(self, position, rows, index):
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)

        for row in range(0, rows):
            self._data.insert(position, [None] * len(self._headers))

        self.endInsertRows()

    def removeRows(self, position, rows, index):
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)

        for row in range(0, rows):
            self._data.pop(position)

        self.endRemoveRows()

    # OK, this is a much simpler API, with only the functionalities I need right
    # now.
    def clear(self):
        """Clear the whole model, and remove everything it contained before"""

        self.removeRows(0, self.rowCount(), QModelIndex())
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def append(self, row):
        """Append a a row in the model.

        The row must have the same number of values as the number of colums
        defined at the model creation.
        """

        if len(row) != len(self._headers):
            msg = "Not enough values in a row (expected %d, got %d" % (
                len(self._headers), len(row))
            raise ValueError(msg)

        position = self.rowCount()
        self.insertRows(position, 1, QModelIndex())

        # FIXME: not very optimal but adapted from the addEntry() code at
        # http://doc.qt.nokia.com/4.6/itemviews-addressbook.html
        for i, value in enumerate(row):
            index = self.index(position, i, QModelIndex())
            self.setData(index, QVariant(value), Qt.EditRole)
            self.dataChanged.emit(index, index)
