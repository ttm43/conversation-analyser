import json
from datetime import datetime
import os

class ConsultationRecorder:
    def __init__(self):
        # 创建存储目录
        self.base_dir = 'consultations'
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def save_consultation(self, analysis_data):
        """保存咨询记录"""
        try:
            # 用时间戳命名文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'consultation_{timestamp}.json'
            filepath = os.path.join(self.base_dir, filename)

            # 保存为JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=4)

            print(f"Consultation saved to: {filepath}")

        except Exception as e:
            print(f"Error saving consultation: {str(e)}") 