import subprocess
from PySide6.QtCore import QThread, Signal

class ExportThread(QThread):
    finished_signal = Signal(bool, str)
    
    def __init__(self, ffmpeg_cmd):
        super().__init__()
        self.ffmpeg_cmd = ffmpeg_cmd
    
    def run(self):
        try:
            result = subprocess.run(self.ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.finished_signal.emit(True, "视频导出成功！")
            else:
                self.finished_signal.emit(False, f"导出失败：{result.stderr}")
        except Exception as e:
            self.finished_signal.emit(False, f"导出异常：{str(e)}")

class ExportManager:
    def __init__(self):
        pass
    
    @staticmethod
    def build_ffmpeg_command(input_path, output_path, start_time, duration):
        """构建 FFmpeg 命令"""
        return [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",
            output_path
        ]