import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton, QLineEdit,
                               QLabel, QWidget, QHBoxLayout, QFileDialog, QComboBox, QSpacerItem,
                               QSizePolicy, QSlider, QScrollArea, QMessageBox, QProgressDialog, QCheckBox)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont, QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import QCursor
from ui.components import ClickableSlider
from core.video_controller import VideoController, FrameDisplay
from core.time_utils import TimeUtils
from core.export_manager import ExportThread
from datetime import timedelta
import pytz
class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        # 去掉左上角系统菜单 + 保留最小化最大化关闭
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        # 最骗子版图标（红色播放三角，Windows必出）
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont("Segoe UI Emoji", 50))
        p.drawText(pixmap.rect(), Qt.AlignCenter, "▶")
        p.end()
        self.setWindowIcon(QIcon(pixmap))

        # 下面你原来的代码全不动
        self.video_controller = VideoController()
        self.time_utils = TimeUtils()
        self.video_filename = ""
        self.video_datetime = None
        self.playback_speed = 1
        self.is_playing = False
        self.init_ui()
        self.video_controller.timer.timeout.connect(self.play_next_frame)


    def center_on_screen(self):
        """将窗口居中显示在鼠标所在的屏幕"""
        # 获取鼠标位置
        cursor_pos = QCursor.pos()
       
        # 获取包含鼠标的屏幕
        screen = QApplication.screenAt(cursor_pos)
        if not screen:
            screen = QApplication.primaryScreen()
       
        # 获取屏幕的几何信息
        screen_geometry = screen.availableGeometry()
       
        # 计算居中位置
        x = screen_geometry.left() + (screen_geometry.width() - self.width()) // 2
        y = screen_geometry.top() + (screen_geometry.height() - self.height()) // 2
       
        # 设置窗口位置
        self.move(x, y)
    def play_next_frame(self):
        """播放下一帧 - 连续播放"""
        if self.video_controller.is_playing:
            frame, ret = self.video_controller.step_forward()
            if ret:
                self.display_frame(frame)
                current_time = self.video_controller.get_current_time()
                self.slider.setValue(int(current_time))
                self.update_frame_label()
            else:
                # 播放到结尾，停止播放
                self.pause_playing()

    def init_ui(self):
        self.setWindowTitle("智能视频播放器 - 支持时间解析和片段导出")
        self.setGeometry(100, 100, 1000, 800)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowSystemMenuHint)
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #666666;  /* 默认灰色 */
                color: #cccccc;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #777777;
                color: white !important;
                font-weight: 500;
            }
            QPushButton:pressed {
                background-color: #4CAF50;  /* 按下时绿色 */
                color: white !important;
                font-weight: 500;
            }
            QPushButton:checked {
                background-color: #4CAF50;  /* 选中状态绿色 */
                color: white !important;
                font-weight: 500;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
            /* 特殊按钮样式 */
            #open_button {
                background-color: #2196F3;  /* 打开按钮蓝色 */
                color: white;
            }
            #open_button:hover {
                background-color: #1976D2;
            }
            #export_button {
                background-color: #FF9800;  /* 导出按钮橙色 */
                color: white;
            }
            #export_button:hover {
                background-color: #F57C00;
            }
            /* 播放/暂停按钮特殊样式 */
            #play_button:checked {
                background-color: #4CAF50;  /* 播放时绿色 */
                color: white !important;
                font-weight: 600 !important;
            }
            #pause_button:checked {
                background-color: #FF5722;  /* 暂停时红色 */
                color: white !important;
                font-weight: 600 !important;
            }
            QLineEdit, QComboBox {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #4CAF50;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QSlider::groove:horizontal {
                background-color: #555555;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #4CAF50;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }
            QSlider::handle:horizontal:hover {
                background-color: #45a049;
            }
            QCheckBox {
                color: white;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
            }
            QProgressDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QScrollArea {
                background-color: #1e1e1e;
                border: 2px solid #555555;
                border-radius: 4px;
            }
        """)

        # 创建界面组件
        self.create_video_display()
        self.create_control_buttons()
        self.create_time_controls()
        self.create_export_controls()
        self.create_layout()

        # 连接信号槽
        self.connect_signals()

        self.center_on_screen()

    def create_video_display(self):
        """创建视频显示区域"""
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(self.video_label)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
    def create_control_buttons(self):
        """创建控制按钮"""
        self.open_button = QPushButton("📁 打开视频")
        self.open_button.setObjectName("open_button")  # 设置对象名称
        self.play_button = QPushButton("▶️ 播放")
        self.play_button.setObjectName("play_button")
        self.play_button.setCheckable(True)  # 设置为可选中
        
        self.pause_button = QPushButton("⏸️ 暂停") 
        self.pause_button.setObjectName("pause_button")
        self.pause_button.setCheckable(True)  # 设置为可选中")
        self.prev_second_button = QPushButton("⏪ 上一秒")
        self.next_second_button = QPushButton("⏩ 下一秒")
        self.prev_minute_button = QPushButton("⏪ 上一分钟")
        self.next_minute_button = QPushButton("⏩ 下一分钟")
       
        # 保留原来的加减号控制
        self.jump_button_sub = QPushButton("-")
        self.frame_input = QLineEdit()
        self.frame_input.setPlaceholderText("秒数...")
        self.frame_input.setFixedWidth(60)
        self.jump_button_add = QPushButton("+")
        # 设置小按钮样式
        self.jump_button_add.setFixedSize(30, 30)
        self.jump_button_sub.setFixedSize(30, 30)
        self.jump_button_add.setStyleSheet("font-size: 16px; font-weight: 500;")
        self.jump_button_sub.setStyleSheet("font-size: 16px; font-weight: 500;")
        # 倍速选择
        self.speed_label = QLabel("🎚️ 播放倍速：")
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "1x", "2x", "4x"])
        self.speed_combo.setCurrentIndex(2)
        # 进度条
        self.slider = ClickableSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setValue(0)
        self.slider.setMaximumHeight(20)
    def create_time_controls(self):
        """创建时间控制组件"""
        self.lint_dt_start = QLineEdit()
        self.lint_dt_end = QLineEdit()
        self.lint_dt_start.setPlaceholderText("HHMMSS")
        self.lint_dt_end.setPlaceholderText("HHMMSS")
        self.lint_dt_start.setFixedWidth(80)
        self.lint_dt_end.setFixedWidth(80)
        self.jump_button_dt = QPushButton("🔄 跳转")
       
        # 新增：跳转到秒的输入框
        self.jump_seconds_input = QLineEdit()
        self.jump_seconds_input.setPlaceholderText("秒数")
        self.jump_seconds_input.setFixedWidth(80)
        self.jump_seconds_button = QPushButton("🎯 跳转到秒")
        # 时间显示 - 美化样式
        self.frame_label = QLabel("⏱️ 当前时间: 0s / 0s")
        self.frame_label.setAlignment(Qt.AlignLeft)
        self.frame_label_dt = QLabel("🕐 绝对时间: 未加载视频")
        self.filename_label = QLabel("📄 文件名: 未打开")
        self.fps_label = QLabel("📊 帧率: 未加载")
    def create_export_controls(self):
        """创建导出控制组件"""
        self.export_start_input = QLineEdit()
        self.export_start_input.setPlaceholderText("起始秒数")
        self.export_start_input.setFixedWidth(80)
       
        self.export_end_input = QLineEdit()
        self.export_end_input.setPlaceholderText("结束秒数")
        self.export_end_input.setFixedWidth(80)
       
        self.watermark_input = QLineEdit()
        self.watermark_input.setPlaceholderText("水印文字")
        self.watermark_input.setFixedWidth(100)
       
        self.watermark_checkbox = QCheckBox("💧 添加水印")
       
        self.export_button = QPushButton("💾 导出视频片段")
        self.export_button.setObjectName("export_button")  # 设置对象名称
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
    def create_layout(self):
        """创建整体布局"""
        # 控制按钮布局
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        # 第一行：基本控制
        basic_controls = QHBoxLayout()
        basic_controls.addWidget(self.speed_label)
        basic_controls.addWidget(self.speed_combo)
        basic_controls.addWidget(self.open_button)
        basic_controls.addWidget(self.play_button)
        basic_controls.addWidget(self.pause_button)
        
        # 第二行：时间跳转控制（保留加减号）
        time_jump_controls = QHBoxLayout()
        time_jump_controls.addWidget(self.prev_second_button)
        time_jump_controls.addWidget(self.next_second_button)
        time_jump_controls.addWidget(self.prev_minute_button)
        time_jump_controls.addWidget(self.next_minute_button)
        time_jump_controls.addWidget(self.jump_button_sub)
        time_jump_controls.addWidget(self.frame_input)
        time_jump_controls.addWidget(self.jump_button_add)
        
        # 组合控制布局
        control_layout.addLayout(basic_controls)
        control_layout.addLayout(time_jump_controls)
        control_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # 时间跳转布局（第三行）- 合并文件起始和跳转到秒
        time_jump_layout = QHBoxLayout()
        time_jump_layout.setSpacing(8)
        time_jump_layout.addWidget(QLabel("🗓️ 文件起始时间:"))
        time_jump_layout.addWidget(self.lint_dt_start)
        time_jump_layout.addWidget(QLabel("🎯 跳转到指定时间:"))
        time_jump_layout.addWidget(self.lint_dt_end)
        time_jump_layout.addWidget(self.jump_button_dt)
        time_jump_layout.addWidget(QLabel("⏱️ 跳转到秒:"))
        time_jump_layout.addWidget(self.jump_seconds_input)
        time_jump_layout.addWidget(self.jump_seconds_button)
        time_jump_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 导出布局（第四行）
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)
        export_layout.addWidget(QLabel("✂️ 导出片段:"))
        export_layout.addWidget(self.export_start_input)
        export_layout.addWidget(QLabel("-"))
        export_layout.addWidget(self.export_end_input)
        export_layout.addWidget(self.watermark_input)
        export_layout.addWidget(self.watermark_checkbox)
        export_layout.addWidget(self.export_button)
        export_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # 创建承载控件
        slider_widget = QWidget()
        slider_layout = QVBoxLayout()
        slider_layout.addWidget(self.slider)
        slider_widget.setLayout(slider_layout)
        slider_widget.setFixedHeight(50)

        # 信息显示布局
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        info_layout.addWidget(self.frame_label)
        info_layout.addWidget(self.frame_label_dt)
        info_layout.addWidget(self.filename_label)
        info_layout.addWidget(self.fps_label)
        info_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        info_widget.setFixedHeight(40)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)  # 设置边距
        
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(slider_widget)
        main_layout.addWidget(info_widget)
        main_layout.addLayout(control_layout)
        main_layout.addLayout(time_jump_layout)  # 合并后的第三行
        main_layout.addLayout(export_layout)     # 导出控制（第四行）

        # 设置中央窗口部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 初始化按钮状态
        self.pause_button.setEnabled(False)
    def connect_signals(self):
        """连接信号和槽"""
        # 按钮连接
        self.open_button.clicked.connect(self.open_video)
        self.play_button.clicked.connect(self.start_playing)
        self.pause_button.clicked.connect(self.pause_playing)
        self.prev_second_button.clicked.connect(self.play_prev_second)
        self.next_second_button.clicked.connect(self.play_next_second)
        self.prev_minute_button.clicked.connect(self.play_prev_minute)
        self.next_minute_button.clicked.connect(self.play_next_minute)
        self.jump_button_add.clicked.connect(self.jump_to_specific_second_add)
        self.jump_button_sub.clicked.connect(self.jump_to_specific_second_sub)
        self.jump_button_dt.clicked.connect(self.jump_to_dt)
        self.jump_seconds_button.clicked.connect(self.jump_to_specific_second) # 连接到新的跳转秒按钮
        self.export_button.clicked.connect(self.export_video_segment)
       
        # 其他连接
        self.speed_combo.currentIndexChanged.connect(self.change_speed)
        self.slider.sliderReleased.connect(self.slider_released)
    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv)"
        )
       
        if file_path:
            if self.video_controller.open_video(file_path):
                self.video_filename = Path(file_path).stem
               
                # 从文件名解析日期时间
                self.video_datetime = self.time_utils.parse_datetime_from_filename(self.video_filename)
               
                # 更新界面
                total_seconds = self.video_controller.get_total_seconds()
                self.slider.setMaximum(int(total_seconds))
                self.slider.setValue(0)
               
                # 更新标签
                if self.video_datetime:
                    self.filename_label.setText(f"文件: {self.video_filename}")
                   
                    # 转换为美东时间
                    import pytz
                    eastern = pytz.timezone('US/Eastern')
                    eastern_start_time = self.video_datetime.astimezone(eastern)
                    self.lint_dt_start.setText(eastern_start_time.strftime("%H%M%S"))
                   
                    # 自动填充结束时间为视频结束时间（美东时间）
                    end_time = self.video_datetime + timedelta(seconds=total_seconds)
                    eastern_end_time = end_time.astimezone(eastern)
                    self.lint_dt_end.setText(eastern_end_time.strftime("%H%M%S"))
                else:
                    self.filename_label.setText(f"文件: {self.video_filename}")
                    self.lint_dt_start.clear()
                    self.lint_dt_end.clear()
               
                # 显示帧率信息
                self.fps_label.setText(f"帧率: {self.video_controller.fps:.1f}fps")
                # 显示第一帧
                frame, ret = self.video_controller.get_frame(0)
                if ret:
                    self.display_frame(frame)
                    self.update_frame_label()
                else:
                    QMessageBox.warning(self, "错误", "无法读取视频帧")
            else:
                QMessageBox.warning(self, "错误", "无法打开视频文件")
    def display_frame(self, frame):
        pixmap = FrameDisplay.convert_frame_to_pixmap(frame)
        if pixmap:
            self.video_label.setPixmap(pixmap)
            self.video_label.resize(pixmap.size())
    def update_frame_label(self):
        current_time = self.video_controller.get_current_time()
        total_time = self.video_controller.get_total_seconds()
        self.frame_label.setText(f"时间: {current_time:.1f}s / {total_time:.1f}s")
       
        # 显示绝对时间
        absolute_time = self.time_utils.calculate_absolute_time(self.video_datetime, current_time)
        self.frame_label_dt.setText(f"日期时间: {absolute_time}")

    def start_playing(self):
        """开始播放 - 连续播放每一帧"""
        if not self.video_controller.is_playing:
            # 根据倍速和帧率计算播放间隔
            interval_ms = int(1000 / (self.video_controller.fps * self.playback_speed))
            self.video_controller.start_playback(interval_ms)
            self.play_button.setChecked(True)    # 设置播放按钮为选中状态
            self.pause_button.setChecked(False)  # 设置暂停按钮为非选中状态
            self.play_button.setEnabled(False)   # 播放时禁用播放按钮
            self.pause_button.setEnabled(True)   # 播放时启用暂停按钮

    def pause_playing(self):
        """暂停播放"""
        self.video_controller.stop_playback()
        self.play_button.setChecked(False)  # 设置播放按钮为非选中状态
        self.pause_button.setChecked(True)  # 设置暂停按钮为选中状态
        self.play_button.setEnabled(True)   # 暂停时启用播放按钮
        self.pause_button.setEnabled(False) # 暂停时禁用暂停按钮

    def play_next_second(self):
        """播放下一秒 - 跳转1秒的帧数"""
        frame, ret = self.video_controller.jump_by_seconds(1)
        if ret:
            self.display_frame(frame)
            current_time = self.video_controller.get_current_time()
            self.slider.setValue(int(current_time))
            self.update_frame_label()
    def play_prev_second(self):
        """播放上一秒 - 跳转-1秒的帧数"""
        frame, ret = self.video_controller.jump_by_seconds(-1)
        if ret:
            self.display_frame(frame)
            current_time = self.video_controller.get_current_time()
            self.slider.setValue(int(current_time))
            self.update_frame_label()
    def play_next_minute(self):
        """播放下一分钟"""
        frame, ret = self.video_controller.jump_by_seconds(60)
        if ret:
            self.display_frame(frame)
            current_time = self.video_controller.get_current_time()
            self.slider.setValue(int(current_time))
            self.update_frame_label()
    def play_prev_minute(self):
        """播放上一分钟"""
        frame, ret = self.video_controller.jump_by_seconds(-60)
        if ret:
            self.display_frame(frame)
            current_time = self.video_controller.get_current_time()
            self.slider.setValue(int(current_time))
            self.update_frame_label()
    def slider_released(self):
        """进度条跳转"""
        time_in_seconds = self.slider.value()
        frame, ret = self.video_controller.jump_to_second(time_in_seconds)
        if ret:
            self.display_frame(frame)
            self.update_frame_label()
    def change_speed(self):
        """更改播放倍速"""
        speed_text = self.speed_combo.currentText()
        self.playback_speed = float(speed_text.replace("x", ""))
       
        # 如果正在播放，更新定时器
        if self.video_controller.is_playing:
            interval_ms = int(1000 / (self.video_controller.fps * self.playback_speed))
            self.video_controller.timer.start(interval_ms)
    def jump_to_specific_second(self):
        """跳转到指定秒数"""
        try:
            seconds = float(self.jump_seconds_input.text()) # 使用新的输入框
            frame, ret = self.video_controller.jump_to_second(seconds)
            if ret:
                self.display_frame(frame)
                current_time = self.video_controller.get_current_time()
                self.slider.setValue(int(current_time))
                self.update_frame_label()
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的秒数")
    def jump_to_specific_second_add(self):
        """正向跳转指定秒数"""
        try:
            seconds = float(self.frame_input.text())
            frame, ret = self.video_controller.jump_by_seconds(seconds)
            if ret:
                self.display_frame(frame)
                current_time = self.video_controller.get_current_time()
                self.slider.setValue(int(current_time))
                self.update_frame_label()
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的秒数")
    def jump_to_specific_second_sub(self):
        """反向跳转指定秒数"""
        try:
            seconds = float(self.frame_input.text())
            frame, ret = self.video_controller.jump_by_seconds(-seconds)
            if ret:
                self.display_frame(frame)
                current_time = self.video_controller.get_current_time()
                self.slider.setValue(int(current_time))
                self.update_frame_label()
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的秒数")
    def jump_to_dt(self):
        """按时间差跳转"""
        try:
            dt_start = self.lint_dt_start.text()
            dt_end = self.lint_dt_end.text()
           
            if not dt_start or not dt_end:
                QMessageBox.warning(self, "警告", "请输入起始和结束时间")
                return
               
            seconds = self.time_utils.calculate_seconds_difference(dt_start, dt_end)
            frame, ret = self.video_controller.jump_to_second(seconds)
            if ret:
                self.display_frame(frame)
                current_time = self.video_controller.get_current_time()
                self.slider.setValue(int(current_time))
                self.update_frame_label()
        except ValueError:
            QMessageBox.warning(self, "错误", "时间格式错误，请使用 HHMMSS 格式")
    def handle_export_result(self, success, message):
        """处理导出结果"""
        if hasattr(self, 'export_progress'):
            self.export_progress.close()
           
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.critical(self, "失败", message)
    def closeEvent(self, event):
        """关闭事件，确保资源被释放"""
        self.video_controller.release()
        event.accept()
    def export_video_segment(self):
        """导出视频片段"""
        if not self.video_controller.cap or not self.video_controller.video_path:
            QMessageBox.warning(self, "警告", "请先打开视频文件")
            return
        try:
            start_seconds_str = self.export_start_input.text().strip()
            end_seconds_str = self.export_end_input.text().strip()
           
            if not start_seconds_str or not end_seconds_str:
                QMessageBox.warning(self, "警告", "请输入起始和结束秒数")
                return
            # 直接使用秒数
            video_start_seconds = float(start_seconds_str)
            video_end_seconds = float(end_seconds_str)
            duration = video_end_seconds - video_start_seconds
            if duration <= 0:
                QMessageBox.warning(self, "警告", "结束秒数必须大于起始秒数")
                return
            # 确保时间在视频范围内
            total_seconds = self.video_controller.get_total_seconds()
            video_start_seconds = max(0, video_start_seconds)
            video_end_seconds = min(total_seconds, video_end_seconds)
            duration = video_end_seconds - video_start_seconds
            # 生成输出文件名
            if self.video_datetime:
                # 计算实际时间
                start_actual_time = self.video_datetime + timedelta(seconds=video_start_seconds)
                end_actual_time = self.video_datetime + timedelta(seconds=video_end_seconds)
               
                base_name = self.video_filename.split('_')[0] # 只要 "cety"
                output_filename = f"{base_name}_{start_actual_time.strftime('%Y-%m-%d %H-%M-%S')}.avi"
            else:
                base_name = self.video_filename.split('_')[0]
                output_filename = f"{base_name}_{int(video_start_seconds)}s_{int(video_end_seconds)}s.avi"
            # 选择保存路径
            output_path, _ = QFileDialog.getSaveFileName(
                self, "保存视频片段", output_filename, "AVI (*.avi);;MP4 (*.mp4)"
            )
           
            if not output_path:
                return
            # 检查是否添加水印
            watermark_text = self.watermark_input.text().strip()
            if self.watermark_checkbox.isChecked() and watermark_text:
                # 带水印的FFmpeg命令
                # 带水印的FFmpeg命令
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                   
                    "-i", self.video_controller.video_path,
                    "-ss", str(video_start_seconds),
                    "-t", str(duration),
                    "-vf", f"drawtext=text='{watermark_text}':fontsize=24:fontcolor=white@0.7:fontfile=/Windows/Fonts/arial.ttf:x='mod(10*t\,w-tw)':y='mod(20*t\,h-th)'",
                    "-c:v", "libx264", # 指定视频编码器
                    "-crf", "18", # 高质量（0-51，18是高质量）
                    "-preset", "medium", # 编码速度和质量平衡
                    "-c:a", "aac", # 音频编码
                    "-b:a", "192k", # 音频码率
                    output_path
                ]
            else:
                # 不带水印的FFmpeg命令
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                   
                    "-i", self.video_controller.video_path,
                    "-ss", str(video_start_seconds),
                    "-t", str(duration),
                    "-c", "copy",
                    output_path
                ]
            # 显示进度对话框
            self.export_progress = QProgressDialog("正在导出视频片段...", "取消", 0, 0, self)
            self.export_progress.setWindowModality(Qt.WindowModal)
            self.export_progress.show()
            # 启动导出线程
            self.export_thread = ExportThread(ffmpeg_cmd)
            self.export_thread.finished_signal.connect(self.handle_export_result)
            self.export_thread.start()
        except ValueError as e:
            QMessageBox.warning(self, "错误", f"请输入有效的秒数: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
