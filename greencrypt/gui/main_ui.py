# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMenu, QMenuBar, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setWindowModality(Qt.WindowModality.NonModal)
        MainWindow.setEnabled(True)
        MainWindow.resize(240, 480)
        MainWindow.setMinimumSize(QSize(240, 480))
        MainWindow.setMaximumSize(QSize(240, 480))
        self.actionOpenFiles = QAction(MainWindow)
        self.actionOpenFiles.setObjectName(u"actionOpenFiles")
        self.actionOpenFolder = QAction(MainWindow)
        self.actionOpenFolder.setObjectName(u"actionOpenFolder")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.mainLayout = QVBoxLayout(self.centralwidget)
        self.mainLayout.setObjectName(u"mainLayout")
        self.dropFrame = QFrame(self.centralwidget)
        self.dropFrame.setObjectName(u"dropFrame")
        self.dropFrame.setMinimumSize(QSize(0, 150))
        self.dropFrame.setAcceptDrops(True)
        self.dropFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.dropFrame.setFrameShadow(QFrame.Shadow.Sunken)
        self.dropFrame.setLineWidth(2)
        self.dropFrame.setMidLineWidth(0)
        self.dropLayout = QVBoxLayout(self.dropFrame)
        self.dropLayout.setSpacing(0)
        self.dropLayout.setObjectName(u"dropLayout")
        self.dropLayout.setContentsMargins(0, 0, 0, 0)
        self.lblLogo = QLabel(self.dropFrame)
        self.lblLogo.setObjectName(u"lblLogo")
        self.lblLogo.setMinimumSize(QSize(0, 150))
        self.lblLogo.setScaledContents(True)
        self.lblLogo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logoLayout = QVBoxLayout(self.lblLogo)
        self.logoLayout.setSpacing(0)
        self.logoLayout.setObjectName(u"logoLayout")
        self.logoLayout.setContentsMargins(12, 0, 12, 12)
        self.logoSpacerTop = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.logoLayout.addItem(self.logoSpacerTop)

        self.lblDropHint = QLabel(self.lblLogo)
        self.lblDropHint.setObjectName(u"lblDropHint")
        self.lblDropHint.setStyleSheet(u"color: #ffffff; font-size: 14px; font-weight: bold;")
        self.lblDropHint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblDropHint.setWordWrap(True)

        self.logoLayout.addWidget(self.lblDropHint)


        self.dropLayout.addWidget(self.lblLogo)


        self.mainLayout.addWidget(self.dropFrame)

        self.grpOptions = QGroupBox(self.centralwidget)
        self.grpOptions.setObjectName(u"grpOptions")
        self.optionsLayout = QVBoxLayout(self.grpOptions)
        self.optionsLayout.setObjectName(u"optionsLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.labelPwd1 = QLabel(self.grpOptions)
        self.labelPwd1.setObjectName(u"labelPwd1")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.labelPwd1)

        self.txtPwd1 = QLineEdit(self.grpOptions)
        self.txtPwd1.setObjectName(u"txtPwd1")
        self.txtPwd1.setEchoMode(QLineEdit.EchoMode.Password)
        self.txtPwd1.setClearButtonEnabled(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.txtPwd1)

        self.labelPwd2 = QLabel(self.grpOptions)
        self.labelPwd2.setObjectName(u"labelPwd2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.labelPwd2)

        self.txtPwd2 = QLineEdit(self.grpOptions)
        self.txtPwd2.setObjectName(u"txtPwd2")
        self.txtPwd2.setEchoMode(QLineEdit.EchoMode.Password)
        self.txtPwd2.setClearButtonEnabled(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.txtPwd2)


        self.optionsLayout.addLayout(self.formLayout)

        self.chkDeleteOriginal = QCheckBox(self.grpOptions)
        self.chkDeleteOriginal.setObjectName(u"chkDeleteOriginal")

        self.optionsLayout.addWidget(self.chkDeleteOriginal)

        self.chkUsePasswordFile = QCheckBox(self.grpOptions)
        self.chkUsePasswordFile.setObjectName(u"chkUsePasswordFile")

        self.optionsLayout.addWidget(self.chkUsePasswordFile)

        self.btnBrowse = QPushButton(self.grpOptions)
        self.btnBrowse.setObjectName(u"btnBrowse")

        self.optionsLayout.addWidget(self.btnBrowse)

        self.progressBar = QProgressBar(self.grpOptions)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setVisible(False)
        self.progressBar.setTextVisible(True)

        self.optionsLayout.addWidget(self.progressBar)

        self.lblStatus = QLabel(self.grpOptions)
        self.lblStatus.setObjectName(u"lblStatus")
        self.lblStatus.setStyleSheet(u"color: #666; font-size: 11px;")
        self.lblStatus.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.optionsLayout.addWidget(self.lblStatus)


        self.mainLayout.addWidget(self.grpOptions)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.btnEncrypt = QPushButton(self.centralwidget)
        self.btnEncrypt.setObjectName(u"btnEncrypt")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnEncrypt.sizePolicy().hasHeightForWidth())
        self.btnEncrypt.setSizePolicy(sizePolicy)

        self.buttonLayout.addWidget(self.btnEncrypt)

        self.btnDecrypt = QPushButton(self.centralwidget)
        self.btnDecrypt.setObjectName(u"btnDecrypt")
        sizePolicy.setHeightForWidth(self.btnDecrypt.sizePolicy().hasHeightForWidth())
        self.btnDecrypt.setSizePolicy(sizePolicy)

        self.buttonLayout.addWidget(self.btnDecrypt)


        self.mainLayout.addLayout(self.buttonLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 240, 23))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setSizeGripEnabled(False)
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionOpenFiles)
        self.menuFile.addAction(self.actionOpenFolder)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuHelp.addAction(self.actionAbout)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"GreenCrypt", None))
        self.actionOpenFiles.setText(QCoreApplication.translate("MainWindow", u"Open files...", None))
#if QT_CONFIG(shortcut)
        self.actionOpenFiles.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionOpenFolder.setText(QCoreApplication.translate("MainWindow", u"Open folder...", None))
#if QT_CONFIG(shortcut)
        self.actionOpenFolder.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Shift+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
#if QT_CONFIG(shortcut)
        self.actionExit.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Q", None))
#endif // QT_CONFIG(shortcut)
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"About GreenCrypt...", None))
        self.lblLogo.setText("")
        self.lblDropHint.setText(QCoreApplication.translate("MainWindow", u"Drag files or folders here", None))
        self.grpOptions.setTitle(QCoreApplication.translate("MainWindow", u"Options", None))
        self.labelPwd1.setText(QCoreApplication.translate("MainWindow", u"Password:", None))
        self.txtPwd1.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Password", None))
        self.labelPwd2.setText(QCoreApplication.translate("MainWindow", u"Repeat:", None))
        self.txtPwd2.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Repeat password", None))
        self.chkDeleteOriginal.setText(QCoreApplication.translate("MainWindow", u"Delete original", None))
        self.chkUsePasswordFile.setText(QCoreApplication.translate("MainWindow", u"Use password file", None))
        self.btnBrowse.setText(QCoreApplication.translate("MainWindow", u"Browse...", None))
        self.lblStatus.setText(QCoreApplication.translate("MainWindow", u"Ready", None))
        self.btnEncrypt.setText(QCoreApplication.translate("MainWindow", u"Encrypt", None))
        self.btnDecrypt.setText(QCoreApplication.translate("MainWindow", u"Decrypt", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"&File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"&Help", None))
    # retranslateUi

