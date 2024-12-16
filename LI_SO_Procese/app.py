from PyQt5 import QtCore, QtWidgets
import sys
import os
import signal
import psutil
from PyQt5.QtGui import QPalette, QColor
from time import sleep

class ProcessThread(QtCore.QThread):
    change_value = QtCore.pyqtSignal(list)

    def run(self):
        while True:
            all_procs = []
            total_cpu = 0
            total_memory = 0

            psutil.cpu_percent(interval=None)
            sleep(0.2)

            for proc in psutil.process_iter(attrs=['pid', 'name']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    if name == "System Idle Process" or pid == 0:
                        continue
                    cpu = proc.cpu_percent(interval=None) / psutil.cpu_count()  # Utilizare procesor
                    memory = proc.memory_info().rss / 1024 ** 2 # Utilizare memorie in MB
                    total_cpu += cpu
                    total_memory += memory
                    all_procs.append([pid, f"{cpu:.1f}", f"{memory:.1f}", name])
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            self.change_value.emit([total_cpu, total_memory, all_procs])

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.processes = {}
        self.processTimer = QtCore.QTimer()
        self.setObjectName("MainWindow")
        self.resize(800, 600)
        self.setMinimumSize(400, 200)
        self.setWindowTitle("SO - Procese")
        self.setupUI()
        self.startProcessThread()

    def startProcessThread(self):
        self.proc_thread = ProcessThread()
        self.proc_thread.change_value.connect(self.setProcesses)
        self.proc_thread.start()

    def setProcesses(self, data):
        total_cpu, total_memory, procs = data
        self.updateHeader(total_cpu, total_memory)
        self.processes = {proc[0]: proc for proc in procs}

        to_remove = []
        for x in range(self.processlist.rowCount()):
            if self.processlist.item(x, 0) is not None:
                if int(self.processlist.item(x, 0).text()) not in self.processes.keys():
                    to_remove.append(x)

        for item in to_remove:
            self.processlist.removeRow(item)

        self.updateProcessList()

    def setupUI(self):
        self.setupCentralWindow()
        self.setupMenuBar()

        self.retranslateUI()
        QtCore.QMetaObject.connectSlotsByName(self)

        self.setupUIActions()

    def setupUIActions(self):
        self.deleteSelectedItemButton.clicked.connect(self.killSelectedProcess)
        self.searchBar.textChanged.connect(self.filterProcesses)

    def setupCentralWindow(self):
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.headerLabel = QtWidgets.QLabel(self.centralwidget)
        self.headerLabel.setObjectName("headerLabel")
        self.headerLabel.setAlignment(QtCore.Qt.AlignCenter)
        font = self.headerLabel.font()
        font.setPointSize(12)
        self.headerLabel.setFont(font)

        self.searchBar = QtWidgets.QLineEdit(self.centralwidget)
        self.searchBar.setPlaceholderText("Caută proces...")
        self.searchBar.setObjectName("searchBar")

        self.deleteSelectedItemButton = QtWidgets.QPushButton(self.centralwidget)
        self.deleteSelectedItemButton.setObjectName("deleteSelectedItemButton")
        self.deleteSelectedItemButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        font = self.deleteSelectedItemButton.font()
        font.setPointSize(11)
        self.deleteSelectedItemButton.setFont(font)

        self.processlist = QtWidgets.QTableWidget(self.centralwidget)
        self.processlist.setRowCount(0)
        self.processlist.setColumnCount(4)
        self.processlist.setShowGrid(True)
        self.processlist.setFocusPolicy(QtCore.Qt.NoFocus)
        self.processlist.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        stylesheet = "QTableWidget::item{selection-background-color: #C9D6DF; selection-color: black;}"
        self.processlist.setStyleSheet(stylesheet)
        self.processlist.setHorizontalHeaderLabels(["  PID  ", "  CPU %  ", " Memorie (MB) ", "Nume proces"])
        self.processlist.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.processlist.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.processlist.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.processlist.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        font = self.processlist.horizontalHeader().font()
        font.setPointSize(11)
        self.processlist.horizontalHeader().setFont(font)

        self.vBox = QtWidgets.QVBoxLayout(self.centralwidget)
        self.vBox.addWidget(self.headerLabel)
        self.vBox.addWidget(self.searchBar)
        self.vBox.addWidget(self.processlist)
        self.vBox.addWidget(self.deleteSelectedItemButton, alignment=QtCore.Qt.AlignRight)

        self.setCentralWidget(self.centralwidget)

    def setupMenuBar(self):
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

    def retranslateUI(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "SO - Procese"))
        self.deleteSelectedItemButton.setText(_translate("MainWindow", "Închide proces"))

    def updateHeader(self, total_cpu, total_memory):
        self.headerLabel.setText(f"CPU: {total_cpu:.1f}% | Memorie: {total_memory:.1f} MB")

    def updateProcessList(self):
        for i, key in enumerate(self.processes):
            cont_flag = False
            for x in range(self.processlist.rowCount()):
                if self.processlist.item(x, 0) is not None:
                    if int(self.processlist.item(x, 0).text()) == int(key):
                        self.processlist.item(x, 0).setText(f"{key}")
                        self.processlist.item(x, 1).setText(f"{self.processes[key][1]}")
                        self.processlist.item(x, 2).setText(f"{self.processes[key][2]}")
                        self.processlist.item(x, 3).setText(f"{self.processes[key][3]}")
                        cont_flag = True
                        break
            if cont_flag:
                continue
            self.processlist.insertRow(i)
            self.processlist.setItem(i, 0, QtWidgets.QTableWidgetItem(f"{key}"))
            self.processlist.setItem(i, 1, QtWidgets.QTableWidgetItem(f"{self.processes[key][1]}"))
            self.processlist.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{self.processes[key][2]}"))
            self.processlist.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{self.processes[key][3]}"))

    def filterProcesses(self):
        search_term = self.searchBar.text().lower()
        for row in range(self.processlist.rowCount()):
            item = self.processlist.item(row, 3)
            if item and search_term not in item.text().lower():
                self.processlist.hideRow(row)
            else:
                self.processlist.showRow(row)

    def killSelectedProcess(self):
        current_row = self.processlist.currentRow()
        if current_row == -1:
            return  # Nu a fost selectat nici un proces

        pid = int(self.processlist.item(current_row, 0).text())
        try:
            os.kill(pid, signal.SIGTERM)
        except PermissionError:
            QtWidgets.QMessageBox.warning(self, "Atenție", "Nu aveți permisiunea să închideți acest proces.")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 32, 34))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(82, 97, 107))
    palette.setColor(QPalette.AlternateBase, QColor(30, 32, 34))
    palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(50, 53, 63))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(201, 214, 223))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())