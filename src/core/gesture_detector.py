import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
from src.utils.SuppressStderr import SuppressStderr


class GestureDetector:
    def __init__(self,model_path):

        """初始化手部模型"""

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            result_callback=self.process_result,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        with SuppressStderr():
            self.recognizer = vision.GestureRecognizer.create_from_options(options)
        self.latest_result = None
        self.timestamp = 0

        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_style = mp.solutions.drawing_styles



    def draw_landmarks(self, img, landmarks):
        mp.solutions.drawing_utils.draw_landmarks(
            img,
            landmarks,
            mp.solutions.hands.HAND_CONNECTIONS,
        )

    def is_pinch(self,hand_landmarks):

        """检测是否为捏合手势"""
        thumb=hand_landmarks[4]
        index_finger=hand_landmarks[8]

        distance=euclidean_distance(thumb,index_finger)
        return distance<0.04

    def is_spread_finger(self,hand_landmarks):

        """检测是否为五指张开手势"""
        # thumb_list=[hand_landmarks.landmark[2],hand_landmarks.landmark[3],hand_landmarks.landmark[4]]
        # index_finger_list=[hand_landmarks.landmark[5],hand_landmarks.landmark[6],hand_landmarks.landmark[7],hand_landmarks.landmark[8]]
        # middle_finger_list=[hand_landmarks.landmark[9],hand_landmarks.landmark[10],hand_landmarks.landmark[11],hand_landmarks.landmark[12]]
        # ring_finger_list=[hand_landmarks.landmark[13],hand_landmarks.landmark[14],hand_landmarks.landmark[15],hand_landmarks.landmark[16]]
        # little_finger_list=[hand_landmarks.landmark[17],hand_landmarks.landmark[18],hand_landmarks.landmark[19],hand_landmarks.landmark[20]]
        thumb_list = [hand_landmarks[2], hand_landmarks[3], hand_landmarks[4]]
        index_finger_list = [hand_landmarks[5], hand_landmarks[6], hand_landmarks[7],
                             hand_landmarks[8]]
        middle_finger_list = [hand_landmarks[9], hand_landmarks[10], hand_landmarks[11],
                              hand_landmarks[12]]
        ring_finger_list = [hand_landmarks[13], hand_landmarks[14], hand_landmarks[15],
                            hand_landmarks[16]]
        little_finger_list = [hand_landmarks[17], hand_landmarks[18], hand_landmarks[19],
                              hand_landmarks[20]]

        return (is_collinear(thumb_list) and is_collinear(index_finger_list)
                and is_collinear(middle_finger_list) and is_collinear(ring_finger_list)
                and is_collinear(little_finger_list))

    def process_result(self,result,output_image,timestamp_ms):
        self.latest_result=result

    def recognize_gesture(self,img):

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        mp_image=mp.Image(image_format=mp.ImageFormat.SRGB,data=img_rgb)
        self.recognizer.recognize_async(mp_image, self.timestamp)

        self.timestamp +=1

    def get_gesture_info(self):
        """获取手势信息"""

        if self.latest_result is None:
            return None

        gesture_info= {
            "gesture":[],
            "handedness":[],
            "landmarks":[],
        }

        if self.latest_result.gestures:
            for gesture in self.latest_result.gestures:
                top_gesture = gesture[0]
                gesture_info["gesture"].append({
                    "category_name":top_gesture.category_name,
                    "score":float(top_gesture.score),
                })
        if self.latest_result.handedness:
            for handedness in self.latest_result.handedness:
                top_handedness = handedness[0]
                gesture_info["handedness"].append({
                    "label":top_handedness.category_name,
                    "score":float(top_handedness.score),
                })

        if self.latest_result.hand_landmarks:
            for i,landmarks in enumerate(self.latest_result.hand_landmarks):
                # if self.is_pinch(landmarks):
                #     gesture_info["gesture"][i]=({
                #         "category_name":"pinch",
                #         "score":0.8
                #     })
                # elif self.is_spread_finger(landmarks):
                #     gesture_info["gesture"][i]=({
                #         "category_name":"spread",
                #         "score":0.8
                #     })
                landmark_list=[]
                for landmark in landmarks:
                    landmark_list.append({
                        "x":landmark.x,
                        "y":landmark.y,
                        "z":landmark.z,
                    })
                gesture_info["landmarks"].append(landmark_list)
        return gesture_info

    def draw_landmarks_and_gesture(self, image, gesture_info):
        """在图像上绘制关键点和手势信息"""
        if gesture_info is None:
            return image

        h, w, _ = image.shape

        # 绘制关键点和连接线
        if gesture_info['landmarks']:
            for i, landmarks in enumerate(gesture_info['landmarks']):
                # 绘制关键点
                for landmark in landmarks:
                    x = int(landmark['x'] * w)
                    y = int(landmark['y'] * h)
                    cv2.circle(image, (x, y), 5, (255, 0, 0), -1)

                # 绘制连接线
                connections = [
                    [0, 1], [1, 2], [2, 3], [3, 4],  # 拇指
                    [0, 5], [5, 6], [6, 7], [7, 8],  # 食指
                    [0, 9], [9, 10], [10, 11], [11, 12],  # 中指
                    [0, 13], [13, 14], [14, 15], [15, 16],  # 无名指
                    [0, 17], [17, 18], [18, 19], [19, 20],  # 小指
                    [5, 9], [9, 13], [13, 17]  # 手掌
                ]

                for connection in connections:
                    start_idx, end_idx = connection
                    start_point = (int(landmarks[start_idx]['x'] * w),
                                   int(landmarks[start_idx]['y'] * h))
                    end_point = (int(landmarks[end_idx]['x'] * w),
                                 int(landmarks[end_idx]['y'] * h))
                    cv2.line(image, start_point, end_point, (0, 255, 0), 2)

        # 显示手势信息
        y_offset = 30
        for i, gesture in enumerate(gesture_info['gesture']):
            if i < len(gesture_info['handedness']):
                hand = gesture_info['handedness'][i]
                text = f"{hand['label']}: {gesture['category_name']} ({gesture['score']:.2f})"
                cv2.putText(image, text, (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                y_offset += 30

        return image

def euclidean_distance(a,b):

    """计算欧氏距离"""

    a=np.array([a.x,a.y,a.z])
    b=np.array([b.x,b.y,b.z])
    return np.sqrt(np.sum(np.square(a-b)))

def is_collinear(points,eps=1e-6):

    """检测点列是否共线"""

    points=np.array([[p.x,p.y,p.z] for p in points])
    if(len(points)<3):
        return True

    v1=points[1]-points[0]

    for p in points[2:]:
        v2=p-points[0]
        cross=np.cross(v1,v2)
        if np.linalg.norm(cross)>eps:
            return False
    return True



