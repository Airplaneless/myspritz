import sys
import time
import numpy as np

from PyQt5 import QtCore, QtWidgets
from src.backend import Reader
from src.frontend.MainForm import Ui_MainWindow as MainForm
from src.frontend.ErrorForm import Ui_Dialog as ErrorForm


class ErrorWindow(QtWidgets.QDialog, ErrorForm):

    def __init__(self, msg):
        super().__init__()
        self.setupUi(self)
        self.label.setText(msg)
        self.exec_()
        self.show()


class PrintThread(QtCore.QThread):
    """
    Qt thread for handling printing words
        > signal - sends list of [str, int, float, int ,float] (see Reader.getFeatures)
        > tsignal - sends int for Qt.progressBar
        > errsignal - sends error string
    """
    signal = QtCore.pyqtSignal(list)
    tsignal = QtCore.pyqtSignal(int)
    errsignal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.fpath = ""
        self.settings = None
        self.reader = None
        self.words = None
        self.currpos = 0

    def moveCurrPos(self, value):
        """
        Move reader position in text
        :param value: int
            Step for moving
        """
        if self.currpos == 0:
            pass
        else:
            self.currpos += value

    def updateSettings(self, opt):
        """
        Update Reader settings
        :param opt: dict
            Dictionary of options for Reader
            "wpm" - word per minute
            "wpf" - word per frame

            "wpm" can be changed after creation of Reader
            instance, while "wpf" will be applied
            only after opening new file
        """
        if self.reader is not None:
            self.reader.wpm = opt["wpm"]
            self.reader.wpf = opt["wpf"]
        self.settings = {"wpm": opt["wpm"], "wpf": opt["wpf"]}

    def getWord(self, i):
        """
        Get word at position
        :param i: int
            Position in text
        :return: str
            Word at current position
        """
        if i >= len(self.words):
            return self.reader.getFeatures(self.words[-1])
        else:
            return self.reader.getFeatures(self.words[i])

    def run(self):
        try:
            self.reader = Reader(self.fpath, self.settings)
            self.words = self.reader.wordList()
            wordcount = len(self.words)
            while self.currpos < wordcount:
                w, pos, t = self.reader.getFeatures(self.words[self.currpos])
                self.signal.emit([w, pos, t, self.currpos, wordcount])
                for i, tq in enumerate([t/50]*50):
                    time.sleep(tq)
                    self.tsignal.emit(i)
                self.currpos += 1
        except Exception as err:
            self.errsignal.emit(str(err))


class MainWindow(QtWidgets.QMainWindow, MainForm):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.progressBar.setMaximum(50)

        self.pthread = PrintThread()
        self.pthread.signal.connect(self.refreshWords)
        self.pthread.signal.connect(self.updateProgress)
        self.pthread.errsignal.connect(self.showMessage)
        self.pthread.tsignal.connect(self.updateWordProgress)
        self.pthread.finished.connect(self.finishedReading)

        self.pthread.settings = {
                "wpm": self.horizontalSlider.value(),
                "wpf": self.horizontalSlider_2.value()}

        self.action.triggered.connect(self.openFile)
        self.pushButton.clicked.connect(self.readingStartStop)
        self.pushButton_4.clicked.connect(self.moveBack)
        self.pushButton_2.clicked.connect(self.moveForward)
        self.horizontalSlider.valueChanged.connect(self.updateSettings)
        self.horizontalSlider_2.valueChanged.connect(self.updateSettings)
        self.horizontalSlider_3.valueChanged.connect(self.setPos)

    def updateWordProgress(self, time):
        """
        Update progress bar while showing one word
        """
        self.progressBar.setValue(time)

    def keyPressEvent(self, event):
        """
        Keyboard handling
        """
        if event.key() == QtCore.Qt.Key_Up:
            self.pthread.reader.wpm += 50
            self.horizontalSlider.setValue(self.pthread.reader.wpm)
        if event.key() == QtCore.Qt.Key_Down:
            self.pthread.reader.wpm -= 50
            self.horizontalSlider.setValue(self.pthread.reader.wpm)
        if event.key() == QtCore.Qt.Key_Left:
            self.moveBack()
            self.horizontalSlider_3.setValue(self.pthread.currpos)
        if event.key() == QtCore.Qt.Key_Right:
            self.moveForward()
            self.horizontalSlider_3.setValue(self.pthread.currpos)
        if event.key() == QtCore.Qt.Key_Space:
            self.readingStartStop()

    def setPos(self):
        self.pthread.currpos = self.horizontalSlider_3.value()
        self.refreshWords(self.pthread.getWord(self.pthread.currpos))

    def moveBack(self):
        self.pthread.moveCurrPos(-1)
        self.refreshWords(self.pthread.getWord(self.pthread.currpos))

    def moveForward(self):
        self.pthread.moveCurrPos(1)
        self.refreshWords(self.pthread.getWord(self.pthread.currpos))

    def finishedReading(self):
        if self.pthread.currpos == self.horizontalSlider_3.maximum():
            self.pthread.currpos = 0
            self.horizontalSlider_3.setValue(0)
        self.pushButton.setText(">")

    def showMessage(self, msg):
        ErrorWindow(msg)

    def updateProgress(self, vec):
        self.horizontalSlider_3.setMaximum(vec[4])
        self.horizontalSlider_3.setValue(vec[3])

    def updateSettings(self):
        wpm = self.horizontalSlider.value()
        wpf = self.horizontalSlider_2.value()
        self.label_2.setText("wpm: {}".format(wpm))
        self.label_3.setText("wpf: {}".format(wpf))
        self.pthread.updateSettings({"wpm": wpm, "wpf": wpf})

    def openFile(self):
        self.pthread.fpath, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open text file")

    def refreshWords(self, vec):
        """
        Show words with colored specific char
        """
        pos = vec[1]
        word = vec[0]
        echar = word[pos]
        lchars = word[:pos]
        rchars = word[pos+1:]
        # Decrease font if text wouldn't fit
        if len(word) >= 9:
            fsize = int(0.9 * self.label.width() / len(word))
        else:
            fsize = 68
        self.label.setText("""
                <html><head/>
                <body><p align=\"center\">
                <span style=\" font-size:{3}pt;\">{0}</span>
                <span style=\" font-size:{3}pt; color:#aa0000;\">{1}</span>
                <span style=\" font-size:{3}pt;\">{2}</span>
                </p></body></html>""".format(lchars, echar, rchars, fsize))

    def readingStartStop(self):
        if self.pthread.isRunning():
            self.pthread.terminate()
            self.pushButton.setText(">")
        else:
            self.pthread.start()
            self.pushButton.setText("||")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
