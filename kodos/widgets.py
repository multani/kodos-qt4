import os.path

from PyQt4.QtGui import QPixmap, QLabel


HERE = os.path.abspath(os.path.dirname(__file__))


class StatusBar(object):
    """Simple wrapper around the Status bar to ease Kodos messages handling"""

    def __init__(self, statusbar):
        images = os.path.join(HERE, 'images')
        self.indicators = {
            'ok'      : QPixmap(os.path.join(images, 'green.png')),
            'warning' : QPixmap(os.path.join(images, 'yellow.png')),
            'error'   : QPixmap(os.path.join(images, 'red.png')),
        }

        self.image_indicator = QLabel()
        self.msg_indicator   = QLabel()

        statusbar.addWidget(self.image_indicator)
        statusbar.addWidget(self.msg_indicator)

    def showMessage(self, msg):
        """Display a message in the status bar"""

        self.msg_indicator.setText(msg)

    def setIndicator(self, tag):
        """Set the status icon in the status bar.

        The indicator can be one of: ok, warning or error
        """

        if tag not in self.indicators:
            raise ValueError("Unknow status bar tag: %s" % tag)

        self.image_indicator.setPixmap(self.indicators[tag])
