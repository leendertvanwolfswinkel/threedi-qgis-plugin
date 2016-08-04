from qgis.core import QgsMessageLog
from qgis.gui import QgsMessageBar

from PyQt4.QtGui import QMessageBox, QProgressBar
from PyQt4.QtCore import Qt

try:
    from qgis.utils import iface
except:
    iface = None


def log(msg, level='INFO'):
    """Shortcut for QgsMessageLog.logMessage function."""
    if level not in ['INFO', 'CRITICAL', 'WARNING']:
        level = 'INFO'
    loglevel = getattr(QgsMessageLog, level)
    QgsMessageLog.logMessage(msg, level=loglevel)
    if iface is None:
        print msg


def pop_up_info(msg='', title='Information', parent=None):
    """Display an info message via Qt box"""
    QMessageBox.information(parent, title, '%s' % msg)


def statusbar_message(msg=''):
    """Display message in status bar """
    if iface is not None:
        iface.mainWindow().statusBar().showMessage(msg)


def messagebar_message(title, msg, level=QgsMessageBar.INFO, duration=0):
    """ Show message in the message bar (just above the map)
    args:
        title: (str) title of messages, showed bold in the start of the message
        msg: (str) message
        level: (int) INFO = 0, WARNING = 1, CRITICAL = 2, SUCCESS = 3. It is
            possible to use QgsMessage.INFO, etc
        duration: (int) how long this the message displays in seconds
    """
    if iface is not None:
        iface.messageBar().pushMessage(title, msg, level, duration)


def pop_up_question(msg='', title='', parent=None):
    """Message box question (Yes or No).

    Returns:
        True if 'Yes' was clicked, or False if 'No' was clicked.
    """
    reply = QMessageBox.question(
        parent, title, msg,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No)

    return (reply == QMessageBox.Yes)


class StatusProgressBar(object):

    def __init__(self, maximum=100, message_title=''):

        self.maximum = maximum
        self.message_bar = iface.messageBar().createMessage(message_title, '')

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.message_bar.layout().addWidget(self.progress_bar)
        if iface is not None:
            iface.messageBar().pushWidget(self.message_bar, iface.messageBar().INFO)

        self.step_size = 1
        self.progress = 0

    def set_step_size(self, step_size):

        self.step_size = step_size

    def increase_progress(self, steps=1, message=None):

        self.progress += steps * self.step_size
        self.progress_bar.setValue(self.progress)
        if message:
            self.message_bar.setText(message)

    def __del__(self):
        if iface is not None:
            iface.messageBar().clearWidgets()
