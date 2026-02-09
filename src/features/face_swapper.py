import threading
import cv2
import numpy as np
import mediapipe as mp

import time
import os


class FaceSwapper:
    def __init__(self, source_face_path=None):
        self.lock = threading.Lock()

        # 初始化MediaPipe人脸关键点检测
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils

        # 加载源人脸（要替换成的人脸）
        self.source_face_path = source_face_path
        self.source_face = None
        self.source_face_points = None

        self.load_source_face(self.source_face_path)

        # 初始化人脸网格（468个关键点）
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # 用于存储最近的人脸关键点
        self.last_face_landmarks = None

    def load_source_face(self, image_path):
        """加载源人脸图像并提取关键点"""
        try:
            source_img = cv2.imread(image_path)
            if source_img is None:
                print(f"无法加载源人脸图像: {image_path}")
                return False

            print(f"成功加载源人脸图像: {image_path}, 尺寸: {source_img.shape}")
            self.source_face = source_img

            # 使用高精度模式提取源人脸关键点
            with self.mp_face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5
            ) as face_mesh:
                rgb_img = cv2.cvtColor(self.source_face, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb_img)

                if results.multi_face_landmarks:
                    self.source_face_points = self.extract_all_face_points(
                        results.multi_face_landmarks[0],
                        self.source_face.shape
                    )
        except Exception as e:
            print(f"加载源人脸时出错: {str(e)}")
            return False

    def extract_all_face_points(self, landmarks, image_shape):
        """提取所有人脸关键点（468个点）"""
        h, w = image_shape[:2]
        points = []

        # 使用所有468个关键点
        for idx in range(len(landmarks.landmark)):
            landmark = landmarks.landmark[idx]
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            points.append((x, y))

        return np.array(points, dtype=np.float32)

    def get_face_mask(self, points, image_shape):
        """生成更精确的人脸掩码"""
        h, w = image_shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)

        # 使用凸包生成基础掩码
        hull = cv2.convexHull(points.astype(np.int32))
        cv2.fillConvexPoly(mask, hull, 255)

        # 使用形态学操作扩展掩码
        kernel = np.ones((15, 15), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # 模糊边缘
        mask = cv2.GaussianBlur(mask, (31, 31), 15)

        return mask

    def detect_and_swap(self, frame,source_face_path):
        """检测人脸并执行换脸"""

        if source_face_path is None:
            return frame

        if self.source_face_path != source_face_path:
            self.load_source_face(source_face_path)
            self.source_face_path = source_face_path

        if self.source_face_points is None or self.source_face is None:
            # print("未加载源人脸或源人脸关键点")
            return frame

        # 转换颜色空间
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        try:
            # 使用FaceMesh检测人脸关键点
            results = self.face_mesh.process(rgb_frame)

            if not results.multi_face_landmarks:
                # 如果没有检测到新的人脸，使用上一次的检测结果
                if self.last_face_landmarks:
                    results = type('obj', (object,), {
                        'multi_face_landmarks': [self.last_face_landmarks]
                    })()
                else:
                    return frame

            # 对每个检测到的人脸执行换脸
            output_frame = frame.copy()

            for face_landmarks in results.multi_face_landmarks:
                # 保存最近的人脸关键点
                self.last_face_landmarks = face_landmarks

                # 提取目标人脸关键点
                target_points = self.extract_all_face_points(face_landmarks, frame.shape)

                if len(target_points) >= 3 and len(target_points) == len(self.source_face_points):
                    # 执行换脸
                    output_frame = self.swap_faces(
                        output_frame,
                        self.source_face,
                        self.source_face_points,
                        target_points
                    )
                else:
                    # 如果不匹配，使用快速换脸方法
                    print(f"关键点数量不匹配: 源={len(self.source_face_points)}, 目标={len(target_points)}")
                    output_frame = self.quick_swap(frame)

            return output_frame

        except Exception as e:
            print(f"人脸检测和换脸过程中出错: {str(e)}")
            return frame


    def swap_faces(self, target_img, source_img, source_points, target_points):
        """执行人脸交换"""
        try:
            # 计算仿射变换矩阵
            h, mask = cv2.findHomography(source_points, target_points, cv2.RANSAC, 5.0)
            if h is None:
                print("无法计算Homography矩阵")
                return target_img

            # 将源人脸变形到目标人脸
            warped_source = cv2.warpPerspective(
                source_img, h, (target_img.shape[1], target_img.shape[0])
            )

            # 创建掩码（只替换面部区域）
            mask = np.zeros(target_img.shape[:2], dtype=np.uint8)

            # 创建面部凸包作为掩码
            hull = cv2.convexHull(target_points.astype(np.int32))
            cv2.fillConvexPoly(mask, hull, 255)

            # 扩展掩码以避免边缘问题
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=3)

            # 模糊掩码边缘以获得更自然的过渡
            mask = cv2.GaussianBlur(mask, (21, 21), 10)
            mask = mask[:, :, np.newaxis] / 255.0

            # 混合图像
            result = target_img.copy()
            result = (1 - mask) * result + mask * warped_source
            result = result.astype(np.uint8)

            return result

        except Exception as e:
            print(f"换脸过程中出错: {str(e)}")
            return target_img

    def quick_swap(self, frame):
        """快速换脸（使用简单的方法）"""
        if self.source_face is None:
            return frame

        try:
            # 检测人脸
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            if not results.multi_face_landmarks:
                return frame

            output_frame = frame.copy()

            for face_landmarks in results.multi_face_landmarks:
                # 获取人脸边界框
                h, w = frame.shape[:2]
                x_coords = [lm.x * w for lm in face_landmarks.landmark]
                y_coords = [lm.y * h for lm in face_landmarks.landmark]

                x_min, x_max = int(min(x_coords)), int(max(x_coords))
                y_min, y_max = int(min(y_coords)), int(max(y_coords))

                # 扩展边界框
                padding_x = int((x_max - x_min) * 0.2)
                padding_y = int((y_max - y_min) * 0.2)
                x_min = max(0, x_min - padding_x)
                x_max = min(w, x_max + padding_x)
                y_min = max(0, y_min - padding_y)
                y_max = min(h, y_max + padding_y)

                # 计算人脸区域
                face_width = x_max - x_min
                face_height = y_max - y_min

                if face_width <= 0 or face_height <= 0:
                    continue

                # 调整源人脸大小
                resized_source = cv2.resize(self.source_face, (face_width, face_height))

                # 创建椭圆掩码
                mask = np.zeros((face_height, face_width), dtype=np.uint8)
                cv2.ellipse(mask,
                            (face_width // 2, face_height // 2),
                            (face_width // 2, face_height // 2),
                            0, 0, 360, 255, -1)

                # 模糊掩码边缘
                mask = cv2.GaussianBlur(mask, (15, 15), 10)
                mask = mask[:, :, np.newaxis] / 255.0

                # 确保区域在图像范围内
                y1, y2 = max(y_min, 0), min(y_min + face_height, h)
                x1, x2 = max(x_min, 0), min(x_min + face_width, w)

                if y2 <= y1 or x2 <= x1:
                    continue

                # 调整大小以匹配实际可用区域
                actual_height = y2 - y1
                actual_width = x2 - x1

                resized_source = cv2.resize(resized_source, (actual_width, actual_height))
                mask = cv2.resize(mask, (actual_width, actual_height))

                # 混合人脸
                output_frame[y1:y2, x1:x2] = (
                        (1 - mask) * output_frame[y1:y2, x1:x2] +
                        mask * resized_source
                ).astype(np.uint8)

            return output_frame

        except Exception as e:
            print(f"快速换脸过程中出错: {str(e)}")
            return frame

    def release(self):
        """释放资源"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()





# 简单的测试函数
def main():
    # 测试换脸功能

    # 构建源人脸路径
    # current_dir = os.path.dirname(os.path.abspath(__file__))



    # source_face_path = "E:/GesturePaint/assets/avatar_sticker/avataaars.png"
    source_face_path ="E:/GesturePaint/assets/avatar_sticker/adventurer-1765898372321.png"


    if source_face_path is None:
        print("未找到源人脸图像，使用默认图像")
        # 创建一个简单的测试图像
        source_face = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.circle(source_face, (100, 100), 50, (0, 255, 0), -1)  # 绿色圆形
        source_face_path = "temp_face.png"
        cv2.imwrite(source_face_path, source_face)

    # 初始化换脸器
    face_swapper = FaceSwapper(source_face_path=source_face_path)

    # 打开摄像头
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("无法打开摄像头")
        return

    print("按 'q' 退出, 's' 保存当前帧")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头画面")
            break

        # 执行换脸
        swapped_frame = face_swapper.detect_and_swap(frame,"E:/GesturePaint/assets/avatar_sticker/img1.png")

        # 显示结果
        cv2.imshow('Face Swap', swapped_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # 保存当前帧
            timestamp = int(time.time())
            cv2.imwrite(f"swap_result_{timestamp}.jpg", swapped_frame)
            print(f"已保存图像: swap_result_{timestamp}.jpg")

    cap.release()
    cv2.destroyAllWindows()
    face_swapper.release()

    # 清理临时文件
    if source_face_path == "temp_face.png" and os.path.exists("temp_face.png"):
        os.remove("temp_face.png")


if __name__ == "__main__":
    main()