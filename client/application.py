import http.server
import socketserver
import os

from PyQt5.QtCore import pyqtSlot, Qt, QEvent, QThread, QUrl, QObject, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QMainWindow)
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings


class Server(QThread):
    def run(self):
        web_dir = "html"
        os.chdir(web_dir)

        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("127.0.0.1", 8090), Handler)
        httpd.serve_forever()

class HelloWorldHtmlApp(QWebEngineView):
    def __init__(self):
        super().__init__()

        #QWebEngineSettings.globalSettings().setAttribute(
        # QWebEngineSettings.ShowScrollBars, False)

        self.setUrl(QUrl("http://127.0.0.1:8090"))

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
    def foo(self, param):
        print('test', param)

    @pyqtSlot()
    def closeWindow(self):
        self.window().close()

    @pyqtSlot(bool)
    def pageLoaded(self, status):
        self.window().show()

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseMove:
            if self.movePos:
                delta = event.globalPos() - self.movePos
                self.window().move(self.window().x()+delta.x(), self.window().y()+delta.y())
                self.movePos = event.globalPos()
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
                frameGm = self.window().frameGeometry()
                frameGm.moveCenter(QApplication.desktop().screenGeometry(QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())).center())
                self.window().move(frameGm.topLeft())

        return False

class MainWindow(QMainWindow):
    def __init__(self, title="WebView"):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.setWindowTitle(title)
        self.resize(1900,1000)
        frameGm = self.frameGeometry()
        frameGm = self.window().frameGeometry()
        frameGm.moveCenter(QApplication.desktop().screenGeometry(
            QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())).center())
        self.move(frameGm.topLeft())

        self.server = Server()
        self.server.start()

        view = HelloWorldHtmlApp()
        self.setCentralWidget(view)


if __name__ == "__main__":
    app = QApplication(['--disable-web-security'])
    win = MainWindow()
    app.exec_()