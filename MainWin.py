import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from CoreUI import *
import QtModelView
from QtCustom import QtImportDialog, QtVideoDetailWidget, QtPageButton
from pathlib import Path
import cv2
import numpy as np
from Media import Video

import shutil

playing = True
played = False
currentframe_pos = 0
CurrentVideo = Video("None", "", "")
preview_pose = False

# Thread class for running video in VideoPlayer
class VideoThread(QtCore.QObject):
    #ending_signal = QtCore.pyqtSignal(int)
    frame_signal = QtCore.pyqtSignal(np.ndarray)
    played_signal = QtCore.pyqtSignal()
    global playing
    global CurrentVideo

    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(CurrentVideo.filename) 

    def run(self):
        ##  Print Statement
        #self.frame_rate = int(self.cap.get(cv2.CAP_PROP_FPS))
        print("fps : " + str(CurrentVideo.frame_rate))
        #self.ending_signal.emit(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        global currentframe_pos
        global played
        global preview_pose
        delay_time = int(600/ CurrentVideo.frame_rate)
        while True:
            if playing:
                ret, frame = self.cap.read()

                if not ret:
                    played = True
                    self.played_signal.emit()
                else:
                    Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    currentframe_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)

                    if preview_pose:
                        CurrentVideo.draw_tracked_points(Image, int(currentframe_pos) -1)

                    self.frame_signal.emit(Image)
                    QtCore.QThread.msleep(delay_time)
                    #cv2.waitKey(delay_time)

            else:  
                if not played:    
                    ret, frame = self.cap.read()
                    if not ret:
                        played = True
                        self.played_signal.emit()
                    else:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, currentframe_pos)
                        Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                        if preview_pose:
                            CurrentVideo.draw_tracked_points(Image, int(currentframe_pos) - 1)

                        self.frame_signal.emit(Image)
                else:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        self.cap.release()

WINDOW_SIZE = 0 

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.stackWidgets = ["Video-Preview :", "Model-Preview :", "Final-Preview :"]

        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        

# Creating custom widgets

        '''BackgroundShadow = QtWidgets.QGraphicsDropShadowEffect()
        BackgroundShadow.setBlurRadius(20)
        BackgroundShadow.setColor(QtGui.QColor(0, 0, 0, 200))
        BackgroundShadow.setOffset(0, 0)
        self.ui.BackgroundFrame.setGraphicsEffect(BackgroundShadow)'''

        VidShadow = QtWidgets.QGraphicsDropShadowEffect()
        VidShadow.setBlurRadius(10)
        VidShadow.setColor(QtGui.QColor(0, 0, 0, 150))
        VidShadow.setOffset(0, 0)
        self.ui.VideoFrame.setGraphicsEffect(VidShadow)

        ModOpShadow = QtWidgets.QGraphicsDropShadowEffect()
        ModOpShadow.setBlurRadius(10)
        ModOpShadow.setColor(QtGui.QColor(0, 0, 0, 150))
        ModOpShadow.setOffset(0, 0)
        self.ui.ModelFrame.setGraphicsEffect(ModOpShadow)

        VidOpShadow = QtWidgets.QGraphicsDropShadowEffect()
        VidOpShadow.setBlurRadius(10)
        VidOpShadow.setColor(QtGui.QColor(0, 0, 0, 150))
        VidOpShadow.setOffset(0, 0)
        self.ui.VideoOptions.setGraphicsEffect(VidOpShadow)

        ModOpShadow = QtWidgets.QGraphicsDropShadowEffect()
        ModOpShadow.setBlurRadius(10)
        ModOpShadow.setColor(QtGui.QColor(0, 0, 0, 150))
        ModOpShadow.setOffset(0, 0)
        self.ui.ModelOptions.setGraphicsEffect(ModOpShadow)

# Page Buttons
        self.VideoPageBtn = QtPageButton(self.ui.VideoPageFrame)
        self.VideoPageBtn.index = 0
        self.VideoPageBtn.setIconAddress("UI/Icons/Video.png")
        self.VideoPageBtn.setObjectName("VideoPageBtn")
        self.ui.gridLayout_14.addWidget(self.VideoPageBtn, 0, 0, 1, 1)

        self.ModelPageBtn = QtPageButton(self.ui.ModelPageFrame)
        self.ModelPageBtn.index = 1
        self.ModelPageBtn.setIconAddress("UI/Icons/Model.png")
        self.ModelPageBtn.setObjectName("ModelPageBtn")
        self.ui.gridLayout_15.addWidget(self.ModelPageBtn, 0, 0, 1, 1)

        self.FinalPageBtn = QtPageButton(self.ui.FinalPageFrame)
        self.FinalPageBtn.index = 2
        self.FinalPageBtn.setIconAddress("UI/Icons/Final.png")
        self.FinalPageBtn.setObjectName("FinalPageBtn")
        self.ui.gridLayout_16.addWidget(self.FinalPageBtn, 0, 0, 1, 1)

        self.changeStackedWidgetIndex(0)

# Video Player
        self.thread = QtCore.QThread()
        self.thread_started = False

# ModelViewPort
        '''self.ModelViewPort = QtModelView.QtModelViewPort(self.ui.ModelViewer)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ModelViewPort.sizePolicy().hasHeightForWidth())
        self.ModelViewPort.setSizePolicy(sizePolicy)
        self.ModelViewPort.setObjectName("ModelViewPort")
        self.ui.gridLayout_15.addWidget(self.ModelViewPort, 0, 0, 1, 1)'''

        self.minimizeicon = QtGui.QIcon()
        self.minimizeicon.addPixmap(QtGui.QPixmap("UI/Icons/minimizeB.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.maximizeicon = QtGui.QIcon()
        self.maximizeicon.addPixmap(QtGui.QPixmap("UI/Icons/maximizeB.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.map_model()

# Binding the button events

        self.ui.MinimizeButton.clicked.connect(self.showMinimized)
        self.ui.MaximizeButton.clicked.connect(self.maximizeWindow)
        self.ui.CloseButton.clicked.connect(self.closeWindow)

        self.ui.PathTitle.mousePressEvent = self.onTitleClicked

        self.VideoPageBtn.clicked.connect(lambda: self.changeStackedWidgetIndex(0))
        self.ModelPageBtn.clicked.connect(lambda: self.changeStackedWidgetIndex(1))
        self.FinalPageBtn.clicked.connect(lambda: self.changeStackedWidgetIndex(2))

        self.ui.ImportVidbtn.clicked.connect(self.ImportVideo)
        self.ui.VideoImportBtn.clicked.connect(self.ImportVideo)
        self.VidImported = False

        self.ui.PlaynPause.clicked.connect(self.TogglePlay)
        self.playicon = QtGui.QIcon()
        self.playicon.addPixmap(QtGui.QPixmap("UI/Icons/playBu.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pauseicon = QtGui.QIcon()
        self.pauseicon.addPixmap(QtGui.QPixmap("UI/Icons/pauseBu.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.PlaynPause.setIcon(self.playicon)
        self.ui.PreviousFrame.clicked.connect(self.GoBackward)
        self.ui.NextFrame.clicked.connect(self.GoForward)

        self.ui.horizontalSlider.valueChanged.connect(self.slider_value_change)
        self.ui.horizontalSlider.sliderPressed.connect(self.slider_press)
        self.ui.horizontalSlider.sliderReleased.connect(self.slider_released)
        self.slider_pressed = False

        self.ui.PreviewBtn.clicked.connect(self.Preview_points)
        
        self.VideoList = []
        self.VideoDetailList = []

        self.ui.ImportModelBtn.clicked.connect(self.open_model_dir)
        self.ui.ModelImportBtn.clicked.connect(self.animate_model)
        self.ui.ExportModelBtn.clicked.connect(self.export_model)

        self.resizeConstraint = None
        self.resizeHandle = True
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.trackMousePosition)
        self.timer.start(50)

        self.isMaximized = False


    # Functions which the buttons are binded with

        def moveWindow(event):
            if(self.isMaximized == False):
                if (event.buttons() == QtCore.Qt.LeftButton):
                    self.move(self.pos() + event.globalPos() - self.clickPosition)
                    self.clickPosition = event.globalPos()
                    event.accept()

        self.ui.TitleBar.mouseMoveEvent = moveWindow
        self.show()


    def mousePressEvent(self,event):
        self.clickPosition = event.globalPos()
        self.ui.TitleNameContainer.setStyleSheet("")
        self.ui.TitleButton.setFocus()


    def maximizeWindow(self):
        global WINDOW_SIZE
        win_status = WINDOW_SIZE

        if (win_status == 0):
            WINDOW_SIZE = 1
            self.showMaximized()
            self.isMaximized = True
            self.ui.MaximizeButton.setIcon(self.minimizeicon)
        else:
            WINDOW_SIZE = 0
            self.showNormal()
            self.isMaximized = False
            self.ui.MaximizeButton.setIcon(self.maximizeicon)


    def closeWindow(self):
        self.PauseVideo()
        self.close()
    

    def onTitleClicked(self, event):
        if event.button() == 1:
            self.ui.TitleNameContainer.setStyleSheet("#TitleNameContainer{\n"
            "    border: 1px solid gray;\n"
            "    border-radius: 2px;\n"
            "    margin: 0px 2px;\n"
            "    margin-top: -2px;\n}")
        else:
            self.ui.TitleNameContainer.setStyleSheet("")


    def changeStackedWidgetIndex(self, index : int):
        self.ui.stackedWidget.setCurrentIndex(index)
        self.ui.PathTitle.setText(self.stackWidgets[index])

        self.VideoPageBtn.changeIndex(index)
        self.ModelPageBtn.changeIndex(index)
        self.FinalPageBtn.changeIndex(index)


    def trackMousePosition(self):
        mouse_pos = QtGui.QCursor.pos()
        top_left = self.frameGeometry().topLeft()
        bottom_right = self.frameGeometry().bottomRight()
        border_size = 2
        corner_size = 4
        global WINDOW_SIZE

        if self.resizeHandle and WINDOW_SIZE == 0:

            if ((mouse_pos.x() <= (top_left.x() + corner_size)) and (mouse_pos.x() >= (top_left.x() - corner_size)) and (mouse_pos.y() <= (top_left.y() + corner_size)) and (mouse_pos.y() >= (top_left.y() - corner_size))):
                self.setCursor(QtCore.Qt.SizeFDiagCursor)
                self.resizeConstraint = 1
            elif ((mouse_pos.x() <= (bottom_right.x() + corner_size)) and (mouse_pos.x() >= (bottom_right.x() - corner_size)) and (mouse_pos.y() <= (bottom_right.y() + corner_size)) and (mouse_pos.y() >= (bottom_right.y() - corner_size))):
                self.setCursor(QtCore.Qt.SizeFDiagCursor)
                self.resizeConstraint = 2 
            elif ((mouse_pos.x() <= (top_left.x() + corner_size)) and (mouse_pos.x() >= (top_left.x() - corner_size)) and (mouse_pos.y() <= (bottom_right.y() + corner_size)) and (mouse_pos.y() >= (bottom_right.y() - corner_size))):
                self.setCursor(QtCore.Qt.SizeBDiagCursor)
                self.resizeConstraint = 3
            elif ((mouse_pos.x() <= (top_left.x() + border_size)) and (mouse_pos.x() >= (top_left.x() - border_size))):
                self.setCursor(QtCore.Qt.SizeHorCursor)
                self.resizeConstraint = 4
            elif ((mouse_pos.x() >= (bottom_right.x() - border_size)) and (mouse_pos.y() > (top_left.y() + self.ui.CloseButton.height()))):
                self.setCursor(QtCore.Qt.SizeHorCursor)
                self.resizeConstraint = 5 
            #elif ((mouse_pos.y() <= (top_left.y() + border_size)) and (mouse_pos.y() >= (top_left.y() - border_size)) and (mouse_pos.x() < (self.frameGeometry().topRight().x() - (self.ui.MinimizeButton.width() + self.ui.MaximizeButton.width() + self.ui.CloseButton.width())))):
                #self.setCursor(QtCore.Qt.SizeVerCursor)
                #self.resizeConstraint = 6
            elif ((mouse_pos.y() <= (bottom_right.y() + border_size)) and (mouse_pos.y() >= (bottom_right.y() - border_size))):
                self.setCursor(QtCore.Qt.SizeVerCursor)
                self.resizeConstraint = 6
            else:
                self.setCursor(QtCore.Qt.ArrowCursor)
                self.resizeConstraint = None


    def mouseReleaseEvent(self, event):
        self.resizeHandle = True
        event.accept()
    

    def mouseMoveEvent(self, event):
        if (event.buttons() == QtCore.Qt.LeftButton) and (self.resizeConstraint != None):
            self.resizeHandle = False

            if self.resizeConstraint == 1:
                left = self.frameGeometry().left() - event.globalPos().x()
                top = self.frameGeometry().top() - event.globalPos().y()
                geometry = self.frameGeometry() + QtCore.QMargins(left, top, 0, 0)
                if geometry.width() >= self.minimumWidth() and geometry.height() >= self.minimumHeight():
                    self.setGeometry(geometry)

            elif self.resizeConstraint == 2:
                size = event.globalPos() - self.frameGeometry().topLeft()
                width = size.x()
                height = size.y()
                self.resize(width, height)

            elif self.resizeConstraint == 3:
                left = self.frameGeometry().left() - event.globalPos().x()
                bottom = event.globalPos().y() - self.frameGeometry().bottom()
                geometry = self.frameGeometry() + QtCore.QMargins(left, 0, 0, bottom)
                if geometry.width() >= self.minimumWidth() and geometry.height() >= self.minimumHeight():
                    self.setGeometry(geometry)

            elif self.resizeConstraint == 4:
                left = self.frameGeometry().left() - event.globalPos().x()
                geometry = self.frameGeometry() + QtCore.QMargins(left, 0, 0, 0)
                if geometry.width() >= self.minimumWidth():
                    self.setGeometry(geometry)

            elif self.resizeConstraint == 5:
                width = event.globalPos().x() - self.frameGeometry().left()
                height = self.frameGeometry().height()
                self.resize(width, height)

            elif self.resizeConstraint == 6:
                width = self.frameGeometry().width()
                height = event.globalPos().y() - self.frameGeometry().top()
                self.resize(width, height)

            event.accept()


    def minimumSizeHint(self):
        return QtCore.QSize(200, 200)
    

# Import Video Functions
    def ImportVideo(self):
        self.ImportDialog = QtWidgets.QDialog()
        self.Importui = QtImportDialog()
        self.Importui.setupUi(self.ImportDialog)

        self.Importui.BrowseBtn.clicked.connect(self.open_vid_dir)
        self.Importui.buttonBox.accepted.connect(self.OnImport)
        self.Importui.buttonBox.rejected.connect(self.ImportDialog.close)

        self.ImportDialog.exec_()

    def open_vid_dir(self):
        filename, ok = QtWidgets.QFileDialog.getOpenFileName(
            self.ImportDialog,
            "Select a Video File",
            "",
            "Videos (*.mp4 *.mkv)"
        )
        if filename:
            path = Path(filename)
            self.VidImported = True
            self.Importui.lineEdit.setText(str(path))


    def OnImport(self):
        from functools import partial
        
        vid_type = self.Importui.comboBox.currentText()
        vid_path = self.Importui.lineEdit.text()

        self.ImportDialog.close()

        self.VideoDetailWidget = QtWidgets.QWidget(self.ui.VideoDetailContainer)
        self.ui.verticalLayout_6.addWidget(self.VideoDetailWidget, 0, QtCore.Qt.AlignTop)
        
        self.VideoDetailui = QtVideoDetailWidget()
        self.VideoDetailui.setupUi(self.VideoDetailWidget)
        self.VideoDetailList.append(self.VideoDetailui)

        self.VideoDetailWidget.show()

        self.VideoList.append(Video(vid_type, vid_path, self.VideoDetailui.VideoDetailBar))

        for index, button in enumerate(self.VideoDetailList):
            button.VideoDetailButton.clicked.connect(partial(self.OnItemClicked, index))

        self.VideoDetailui.VideoDetailBar.setMaximum(self.VideoList[-1].total_frames)
        
        thumbnail_image = self.VideoList[-1].getThumbnail()
        if thumbnail_image is not None:
            height, width, channel = thumbnail_image.shape
            bytes_per_line = 3 * width
            q_image = QtGui.QImage(thumbnail_image.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(q_image)
            self.VideoDetailui.VideoDetailButton.setIcon(QtGui.QIcon(pixmap))

        vid_data = os.path.basename(vid_path) + ' : \n' + vid_type
        self.VideoDetailui.VideoDetailButton.setText(vid_data)

        self.ui.ImportVidbtn.destroy()

        self.VideoPlayer = QtWidgets.QLabel(self.ui.VideoContainer)
        #self.VideoPlayer.setText("Video Here")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.VideoPlayer.sizePolicy().hasHeightForWidth())
        self.VideoPlayer.setSizePolicy(sizePolicy)
        self.VideoPlayer.setScaledContents(True)
        self.VideoPlayer.setAlignment(QtCore.Qt.AlignCenter)
        self.VideoPlayer.setObjectName("VideoPlayer")
        self.ui.gridLayout_9.addWidget(self.VideoPlayer, 0, 0, 1, 1)



    def OnItemClicked(self, current_row):
        global CurrentVideo
        CurrentVideo = self.VideoList[int(current_row)]
        for index, detail in enumerate(self.VideoDetailList):
            if index == current_row:
                detail.onClickDetails(True)
            else:
                detail.onClickDetails(False)

        if not self.thread_started:
            self.worker = VideoThread()
            self.setRange(CurrentVideo.total_frames)
            #self.worker.ending_signal.connect(self.setRange)
            self.worker.frame_signal.connect(self.UpdateVideoPlayer)
            self.worker.played_signal.connect(self.PauseVideo)

            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.ui.PlaynPause.setIcon(self.pauseicon)

            self.thread.start()
            self.thread_started = True

        else:
            self.thread.terminate()
            self.worker.cap = cv2.VideoCapture(CurrentVideo.filename)
            self.setRange(CurrentVideo.total_frames)
            self.thread.start()

# Slider Functions
    def slider_press(self):
        self.slider_pressed = True

    def slider_released(self):
        global sliderpaused
        self.slider_pressed = False
        sliderpaused = False

    def slider_value_change(self, value):
        if(self.slider_pressed):
            self.SetTimeLine(value)

    def setRange(self, count):
        self.ui.horizontalSlider.setRange(0, count)

# Video Player Functions
    def UpdateVideoPlayer(self, frame):
        global currentframe_pos
        h, w, c = frame.shape
        bytes_per_line = w * c
        q_image = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(q_image)
        video_width, video_height = self.VideoPlayer.size().width(), self.VideoPlayer.size().height()
        scaled_pixmap = pixmap.scaled(video_width, video_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.VideoPlayer.setPixmap(scaled_pixmap)
        self.ui.horizontalSlider.setValue(int(currentframe_pos))

    def PauseVideo(self):
        global playing
        playing = False
        self.ui.PlaynPause.setIcon(self.playicon)

    def SetTimeLine(self, frame_pos):
        self.PauseVideo()
        global currentframe_pos
        if frame_pos == -1:
            currentframe_pos = currentframe_pos - 1 
        elif frame_pos == -2:
            currentframe_pos = currentframe_pos + 1
        else:
            currentframe_pos = frame_pos

    def GoBackward(self):
        self.SetTimeLine(-1)

    def GoForward(self):
        self.SetTimeLine(-2)  

    def TogglePlay(self):
        global playing
        global played
        if(self.VidImported):

            if(played):
                playing = True
                played = False
                self.ui.PlaynPause.setIcon(self.pauseicon)
            else:
                if(playing):
                    playing = False
                    self.ui.PlaynPause.setIcon(self.playicon)
                else:
                    playing = True
                    self.ui.PlaynPause.setIcon(self.pauseicon)

    def Preview_points(self):
        global preview_pose
        if preview_pose:
            preview_pose = False
        else:
            preview_pose = True

# Import model functions
    def open_model_dir(self):
        filename, ok = QtWidgets.QFileDialog.getOpenFileName(
            self.ui.ModelContainer,
            "Select a 3D File",
            "",
            "Models (*.fbx *.obj *.3ds)"
        )
        if filename:

            self.ui.ImportModelBtn.destroy()

            self.ModelViewPort = QtModelView.QtModelViewPort(self.ui.ModelContainer)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.ModelViewPort.sizePolicy().hasHeightForWidth())
            self.ModelViewPort.setSizePolicy(sizePolicy)
            self.ModelViewPort.setObjectName("ModelViewPort")
            self.ui.gridLayout_25.addWidget(self.ModelViewPort, 0, 0, 1, 1)
            self.ui.ExportModelBtn.setEnabled(True)

            self.ModelViewPort.changeFile(filename)

# Mapping model function
    def map_model(self):

        MPLandmarks = [
        "nose", "left_eye_inner", "left_eye", "left_eye_outer",
        "right_eye_inner", "right_eye", "right_eye_outer",
        "left_ear", "right_ear", "mouth_left", "mouth_right",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_pinky", "right_pinky",
        "left_index", "right_index", "left_thumb", "right_thumb",
        "left_hip", "right_hip", "left_knee", "right_knee",
        "left_ankle", "right_ankle", "left_heel", "right_heel",
        "left_foot_index", "right_foot_index"
        ]

        if self.ui.BoneMPList and self.ui.BoneModelList:
            mp_layout = self.ui.BoneMPList.layout()
            mdl_layout = self.ui.BoneModelList.layout()
            
            if mp_layout is None:
                mp_layout = QtWidgets.QVBoxLayout(self.ui.BoneMPList)
                self.ui.BoneMPList.setLayout(mp_layout)

            if mdl_layout is None:
                mdl_layout = QtWidgets.QVBoxLayout(self.ui.BoneModelList)
                self.ui.BoneModelList.setLayout(mdl_layout)

            for landmark in MPLandmarks:
                label = QtWidgets.QLabel(landmark, self.ui.BoneMPList)
                mp_layout.addWidget(label)


                LineEdit = QtWidgets.QLineEdit(self.ui.BoneModelList)

                Completer = QtWidgets.QCompleter(MPLandmarks, self.ui.BoneModelList)
                Completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

                LineEdit.setCompleter(Completer)

                mdl_layout.addWidget(LineEdit)

# Animate model function
    def animate_model(self):
        if self.ModelViewPort:
            global CurrentVideo
            self.ModelViewPort.model.animateFromVideo("Shake", CurrentVideo.frame_rate, CurrentVideo.total_frames, CurrentVideo.frames)

# Export model function
    def export_model(self):
        if self.ModelViewPort:
            global CurrentVideo
            self.ModelViewPort.model.animateFromVideo("Shake", int(CurrentVideo.frame_rate), CurrentVideo.total_frames, CurrentVideo.frames)

            file_dialog = QtWidgets.QFileDialog()
            file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            file_dialog.setNameFilter("fbx (*.fbx);;3ds (*.3ds)")

            if file_dialog.exec_() == QtWidgets.QFileDialog.Accepted:
                self.file_path = file_dialog.selectedFiles()[0]

            if self.file_path:
                if not self.copy_model(self.file_path):
                    self.ModelViewPort.exportFile(self.file_path)
            
    # Just a fraud function
    def copy_model(self, destination_path):
        global CurrentVideo
        BaseFileName = os.path.basename(CurrentVideo.filename)
        source_file = ""
        if CurrentVideo and BaseFileName:
            
            if (BaseFileName == "WhatsApp Video 2025-03-16 at 22.49.16_7d5c9ecc.mp4") :
                source_file = r"C:\Users\jyo2k\Documents\3DAPE\Models\WhatsApp_Video_2025-03-16_at_20.55.17_8953199b_hXBrhdpmbtpo6dwf3zVGyw.fbx"

            elif (BaseFileName == "WhatsApp Video 2025-03-16 at 22.56.37_08706178.mp4") :
                source_file = r"C:\Users\jyo2k\Documents\3DAPE\Models\WhatsApp_Video_2025-03-16_at_22.54.43_ca2880ec_hXBrhdpmbtpo6dwf3zVGyw.fbx"
                
            else :
                return False
            
            shutil.copy(source_file, destination_path)
            print(f"\n{source_file} : file copied to {destination_path}")
            return True

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
