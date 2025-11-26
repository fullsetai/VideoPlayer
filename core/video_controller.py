import cv2
from PySide6.QtCore import QTimer  # 改为 PySide6
from PySide6.QtGui import QImage, QPixmap  # 改为 PySide6

class VideoController:
    def __init__(self):
        self.cap = None
        self.video_path = ""
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 1
        self.is_playing = False
        self.timer = QTimer()
        
    def open_video(self, file_path):
        """打开视频文件"""
        if self.cap:
            self.cap.release()
            
        self.cap = cv2.VideoCapture(file_path)
        self.video_path = file_path
        
        if not self.cap.isOpened():
            return False
            
        # 获取视频信息
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"视频帧率: {self.fps}, 总帧数: {self.total_frames}")
        
        if self.fps <= 0:
            self.fps = 1  # 默认帧率
            
        self.current_frame = 0
        self.is_playing = False
        self.timer.stop()
        return True
    
    def get_frame(self, frame_number=None):
        """获取指定帧"""
        if not self.cap or not self.cap.isOpened():
            return None, False
            
        if frame_number is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number
            
        ret, frame = self.cap.read()

        return frame, ret
    
    def jump_to_frame(self, frame_number):
        """跳转到指定帧"""
        if self.cap and self.cap.isOpened():
            frame_number = max(0, min(frame_number, self.total_frames - 1))
            return self.get_frame(frame_number)
        return None, False
    
    def jump_by_seconds(self, seconds):
        """按秒跳转"""
        if self.cap and self.cap.isOpened():
            target_frame = self.current_frame + int(seconds * self.fps)
            return self.jump_to_frame(target_frame)
        return None, False
    
    def jump_to_second(self, seconds):
        """跳转到指定秒数"""
        if self.cap and self.cap.isOpened():
            frame_number = int(seconds * self.fps)
            return self.jump_to_frame(frame_number)
        return None, False
    
    def step_forward(self):
        """向前一帧"""
        return self.jump_to_frame(self.current_frame + 1)
    
    def step_backward(self):
        """向后一帧"""
        return self.jump_to_frame(self.current_frame - 1)
    
    def get_current_time(self):
        """获取当前时间（秒）"""
        return self.current_frame / self.fps if self.fps > 0 else 0
    
    def get_total_seconds(self):
        """获取总时长（秒）"""
        return self.total_frames / self.fps if self.fps > 0 else 0
    
    def start_playback(self, interval_ms):
        """开始播放"""
        self.is_playing = True
        self.timer.start(interval_ms)
    
    def stop_playback(self):
        """停止播放"""
        self.is_playing = False
        self.timer.stop()
    
    def release(self):
        """释放资源"""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.timer.stop()


    def add_watermark(self, frame, watermark_text):
        """给帧添加水印"""
        if frame is None:
            return frame
            
        # 设置水印参数
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = (255, 255, 255)  # 白色
        thickness = 2
        margin = 10
        
        # 获取文本尺寸
        text_size = cv2.getTextSize(watermark_text, font, font_scale, thickness)[0]
        
        # 计算水印位置（右下角）
        height, width = frame.shape[:2]
        x = width - text_size[0] - margin
        y = height - margin
        
        # 添加水印
        cv2.putText(frame, watermark_text, (x, y), font, font_scale, font_color, thickness)
        
        return frame
        
class FrameDisplay:
    @staticmethod
    def convert_frame_to_pixmap(frame):
        """将 OpenCV 帧转换为 QPixmap"""
        if frame is None:
            return None
            
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame_rgb.shape
            bytes_per_line = channel * width
            q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
            return QPixmap.fromImage(q_image)
        except Exception as e:
            print(f"帧转换错误: {e}")
            return None