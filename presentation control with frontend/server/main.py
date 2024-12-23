from flask import Flask, Response, jsonify, request
import cv2
import os
import numpy as np
from flask_cors import CORS
import mediapipe as mp  # MediaPipe import for hand tracking

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Camera and presentation setup
width, height = 1280, 720
folderpath = 'presentation'
cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

pathImages = sorted(os.listdir(folderpath), key=len)
imgNumber = 0
hs, ws = int(120 * 1), int(213 * 1)
gestureThreshold = 300
annotations = [[]]
annotationsnumber = -1
annotationstart = False
buttonpress = False
counter = 0
buttonDelay = 25

# Initialize MediaPipe Hand Solution
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils


@app.route('/start_camera', methods=['POST'])
def start_camera():
    global imgNumber, annotations, annotationsnumber, annotationstart, buttonpress, counter
    imgNumber = 0
    annotations = [[]]
    annotationsnumber = -1
    annotationstart = False
    buttonpress = False
    counter = 0
    return jsonify({'status': 'Camera initialized'})


def generate_frames():
    global imgNumber, annotations, annotationsnumber, annotationstart, buttonpress, counter
    while True:
        success, img = cap.read()
        if not success:
            break
        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Process the image with MediaPipe Hands
        result = hands.process(img_rgb)
        pathFullImage = os.path.join(folderpath, pathImages[imgNumber])
        imgCurrent = cv2.imread(pathFullImage)
        cv2.line(img, (0, gestureThreshold), (width, gestureThreshold), (0, 255, 0), 10)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                # Get hand landmarks and bounding box center
                lm_list = []
                for id, lm in enumerate(hand_landmarks.landmark):
                    lm_list.append((int(lm.x * width), int(lm.y * height)))
                cx, cy = lm_list[9]  # Wrist landmark for center
                
                # Check fingers state
                fingers_up = [1 if lm_list[tip][1] < lm_list[tip - 2][1] else 0 for tip in [8, 12, 16, 20]]
                
                # Gesture controls
                if cy <= gestureThreshold:  # Hand above threshold line
                    if fingers_up == [1, 0, 0, 0]:
                        if imgNumber > 0:
                            buttonpress = True
                            annotations = [[]]
                            annotationsnumber = -1
                            annotationstart = False
                            imgNumber -= 1

                    if fingers_up == [0, 0, 0, 1]:
                        if imgNumber < len(pathImages) - 1:
                            buttonpress = True
                            annotations = [[]]
                            annotationsnumber = -1
                            annotationstart = False
                            imgNumber += 1

                if fingers_up == [0, 1, 0, 0]:
                    if not annotationstart:
                        annotationstart = True
                        annotationsnumber += 1
                        annotations.append([])
                    annotations[annotationsnumber].append(lm_list[8])  # Add index finger point
                else:
                    annotationstart = False

                if fingers_up == [0, 1, 1, 1]:
                    if annotations:
                        annotations.pop(-1)
                        annotationsnumber -= 1
                        buttonpress = True

                mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        if buttonpress:
            counter += 1
            if counter > buttonDelay:
                counter = 0
                buttonpress = False

        for i in range(len(annotations)):
            for j in range(len(annotations[i])):
                if j != 0:
                    cv2.line(imgCurrent, tuple(annotations[i][j - 1]), tuple(annotations[i][j]), (0, 0, 200), 12)

        imgSmall = cv2.resize(img, (ws, hs))
        h, w, _ = imgCurrent.shape
        imgCurrent[0:hs, w - ws:w] = imgSmall
        _, buffer = cv2.imencode('.jpg', imgCurrent)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
