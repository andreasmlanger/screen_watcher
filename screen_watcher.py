"""
Sends screenshots by email in a defined interval
"""

from dotenv import load_dotenv
import pyautogui
from PyQt6.QtCore import QThread
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QComboBox, QLabel, QMainWindow
import sendgrid
from sendgrid.helpers.mail import Attachment, Content, ContentId, Disposition, FileContent, FileName, FileType, Mail
import base64
import datetime
import os
import sys
import time


def resource_path(relative_path):
    return str(os.path.join(os.path.dirname(__file__), relative_path))


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = os.environ.get('FROM_EMAIL')
TO_EMAIL = os.environ.get('TO_EMAIL')
SCREENSHOT = 'Screenshot.png'


def get_geometry(*args):
    return tuple(map(int, [e * Window.s for e in list(args)]))


class Window(QMainWindow):
    app = QApplication([])
    s = app.screens()[0].logicalDotsPerInch() / 96
    app.quit()

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(*get_geometry(200, 200, 260, 115))
        self.setFixedSize(self.size())
        self.setWindowTitle('screenWatcher')
        self.setWindowIcon(QIcon(resource_path('data/screen.png')))

        self.start = QAction('Start', self)
        self.start.triggered.connect(self.start_watching)

        self.stop = QAction('Start', self)
        self.stop.triggered.connect(self.stop_watching)

        close = QAction('Quit', self)
        close.setShortcut('Ctrl+Q')
        close.triggered.connect(self.close_application)

        menu = self.menuBar()

        file = menu.addMenu('File')
        file.addAction(close)

        self.startIcon = QAction(QIcon(resource_path('data/start.png')), 'Start', self)
        self.startIcon.triggered.connect(self.start_watching)

        self.stopIcon = QAction(QIcon(resource_path('data/stop.png')), 'Stop', self)
        self.stopIcon.triggered.connect(self.stop_watching)
        self.stopIcon.setEnabled(False)

        self.toolBar = self.addToolBar('toolbar')
        self.toolBar.addAction(self.startIcon)
        self.toolBar.addAction(self.stopIcon)

        self.label = QLabel(self)
        self.label.setGeometry(*get_geometry(20, 70, 100, 30))
        self.label.setText('Interval:')

        self.interval = QComboBox(self)
        self.interval.setGeometry(*get_geometry(140, 70, 100, 30))
        self.interval.addItem('5 min')
        self.interval.addItem('30 min')
        self.interval.addItem('60 min')
        self.interval.addItem('120 min')

        self.thread = QThread()

        self.show()

    def start_watching(self):
        interval_time = int(self.interval.currentText().split(' min')[0]) * 60

        self.interval.setEnabled(False)
        self.startIcon.setEnabled(False)
        self.stopIcon.setEnabled(True)

        self.thread = Thread(interval_time, self)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()
        print('Start')

    def on_finished(self):
        self.interval.setEnabled(True)
        self.startIcon.setEnabled(True)
        self.stopIcon.setEnabled(False)

        if os.path.isfile(SCREENSHOT):
            os.remove(SCREENSHOT)

        print('Stop')

    def stop_watching(self):
        if self.thread.isRunning():
            self.thread.terminate()

    @staticmethod
    def close_application():
        if os.path.isfile(SCREENSHOT):
            os.remove(SCREENSHOT)
        sys.exit()


class Thread(QThread):
    def __init__(self, interval_time, parent=None):
        QThread.__init__(self, parent)
        self.interval_time = interval_time

    def run(self):
        while True:
            pyautogui.screenshot(SCREENSHOT)
            attachment = self.screenshot2attachment(SCREENSHOT)
            self.send_email(attachment)
            os.remove(SCREENSHOT)
            time.sleep(self.interval_time)

    @staticmethod
    def screenshot2attachment(im):
        with open(im, 'rb') as file:
            file = base64.b64encode(file.read()).decode()
            a = Attachment(FileContent(file),
                           FileName(im),
                           FileType('image/png'),
                           Disposition('inline'),
                           ContentId('Screenshot'))
            return a

    @staticmethod
    def send_email(attachment):
        try:
            sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
            txt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            subject = 'screenWatcher'
            content = Content('text/html', txt)
            mail = Mail(FROM_EMAIL, TO_EMAIL, subject, content)
            mail.attachment = attachment
            mail_json = mail.get()  # JSON-ready representation of the Mail object
            sg.client.mail.send.post(request_body=mail_json)  # send an HTTP POST request to /mail/send
            print(f'Email sent to {TO_EMAIL}')
        except Exception as ex:
            print(ex)


if __name__ == '__main__':

    app = QApplication([])
    Gui = Window()
    sys.exit(app.exec())
