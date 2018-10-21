import http.server
import socketserver
import time
import os
from threading import Thread
import subprocess

import requests
from PyQt5.QtCore import pyqtSlot, Qt, QEvent, QThread, QUrl, QObject, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QMainWindow)
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings


VNC_EXECUTABLE_PATH = '/Users/rbuzu/projects/turbovnc/build/java/VncViewer.jar'
HTML_PATH = '/Users/rbuzu/projects/mercari_hackathon/client/html'
SERVER_IP_WITH_PROTOCOL = 'http://10.42.0.1'
SERVER_IP = '10.42.0.1'
SERVER_PORT = 8000
SERVER_URL = '{}:{}'.format(SERVER_IP_WITH_PROTOCOL, SERVER_PORT)


def threaded_function(param):
    resp = requests.get('{}/{}'.format(SERVER_URL, param))
    time.sleep(2)
    process = subprocess.Popen([
        'java',
        '-jar',
        VNC_EXECUTABLE_PATH,
        'Server={}'.format(SERVER_IP),
        'FullScreen=1',
        'RecvClipboard=0',
        'SendClipboard=0',
        'Shared=0',
        'Colors=65536',
        'LocalCursor=0',
        'CursorShape=0',
        'CompressLevel=0',
        'Encoding=Tight',
        'Subsampling=4X',
        'SecurityTypes=None',
        'Quality=50'
    ], stdin=None, stdout=None, stderr=None, close_fds=True
    )


class Server(QThread):
    def run(self):
        os.chdir(HTML_PATH)

        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("127.0.0.1", 8099), Handler)
        httpd.serve_forever()


server = Server()


class HelloWorldHtmlApp(QWebEngineView):
    def __init__(self):
        super().__init__()

        #QWebEngineSettings.globalSettings().setAttribute(
        # QWebEngineSettings.ShowScrollBars, False)

        self.setUrl(QUrl("http://127.0.0.1:8099"))

        self.channel = QWebChannel()
        self.channel.registerObject('backend', self)
        self.page().profile().clearHttpCache()
        self.page().setWebChannel(self.channel)
        self.setMouseTracking(True)
        app.installEventFilter(self)
        self.page().windowCloseRequested.connect(self.closeWindow)
        self.page().loadFinished.connect(self.pageLoaded)

        self.movePos = None

    @pyqtSlot(str)
    def connect_to_server(self, param):
        thread = Thread(target = threaded_function, args=[param])
        thread.start()
        print('input was:', param)

    @pyqtSlot()
    def closeWindow(self):
        self.window().close()

    @pyqtSlot(bool)
    def pageLoaded(self, status):
        self.window().show()
        self.page().runJavaScript('window.scrollTo(0, 0);')

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseMove:
            if self.movePos:
                delta = event.globalPos() - self.movePos
                #self.window().move(self.window().x()+delta.x(), self.window(
                # ).y()+delta.y())
                #self.movePos = event.globalPos()
        elif event.type() == QEvent.MouseButtonDblClick:
            if event.button() == Qt.LeftButton:
                self.movePos = event.globalPos()
        elif event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                self.movePos = None
        elif event.type() == QEvent.KeyRelease and source.parent() == self and event.modifiers() == Qt.ControlModifier:
            if event.key() in (ord('f'), ord('F')):
                if self.window().isFullScreen():
                    self.window().showNormal()
                else:
                    self.window().showFullScreen()
            elif event.key() in (ord('q'), ord('Q')):
                self.window().close()
            elif event.key() in (ord('c'), ord('C')):
                pass
                #frameGm = self.window().frameGeometry()
                #frameGm.moveCenter(QApplication.desktop().screenGeometry(
                # QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())).center())
                #self.window().move(frameGm.topLeft())

        return False

class MainWindow(QMainWindow):
    def __init__(self, title="WebView"):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.setWindowTitle(title)
        self.resize(1200, 700)
        frameGm = self.frameGeometry()
        frameGm = self.window().frameGeometry()
        frameGm.moveCenter(QApplication.desktop().screenGeometry(
            QApplication.desktop().screenNumber(QApplication.desktop(
         ).cursor().pos())).center())
        self.move(frameGm.topLeft())

        server.start()

        view = HelloWorldHtmlApp()
        self.setCentralWidget(view)


if __name__ == "__main__":
    app = QApplication(['--disable-web-security'])
    win = MainWindow()
    app.exec_()
