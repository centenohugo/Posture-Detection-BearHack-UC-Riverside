# Human Posture Detection using MediaPipe

import cv2
import time
import math as m
import mediapipe as mp
import serial

# Function to calculate Euclidean distance
def findDistance(x1, y1, x2, y2):
    return m.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Function to calculate angle between a vector and y-axis
def findAngle(x1, y1, x2, y2):
    if y1 == 0:
        return 0
    try:
        theta = m.acos((y2 - y1) * (-y1) / (m.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) * y1))
        degree = int(180 / m.pi) * theta
    except:
        degree = 0
    return degree


arduino_input = "output.txt"

# Arduino connection
#Modify the COM port as per your system
arduino = serial.Serial('COM4', 9600)
time.sleep(2)

# Visuals
font = cv2.FONT_HERSHEY_SIMPLEX
blue = (255, 127, 0)
red = (50, 50, 255)
green = (127, 255, 0)
yellow = (0, 255, 255)

# Initialize MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Camera capture
cap = cv2.VideoCapture(0)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Thresholds
NECK_THRESHOLD = 30
TORSO_THRESHOLD = 17

# Counters
good_frames = 0
bad_frames = 0

# Final report variables
total_good = 0
total_bad = 0
total_errors = 0

start = time.time()

try:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Error when reading video.")
            break

        h, w = image.shape[:2]
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        keypoints = pose.process(image_rgb)
        image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        lm = keypoints.pose_landmarks
        if not lm:
            cv2.imshow('Posture Detection', image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        lmPose = mp_pose.PoseLandmark

        l_shldr = (int(lm.landmark[lmPose.LEFT_SHOULDER].x * w), int(lm.landmark[lmPose.LEFT_SHOULDER].y * h))
        r_shldr = (int(lm.landmark[lmPose.RIGHT_SHOULDER].x * w), int(lm.landmark[lmPose.RIGHT_SHOULDER].y * h))
        l_hip = (int(lm.landmark[lmPose.LEFT_HIP].x * w), int(lm.landmark[lmPose.LEFT_HIP].y * h))
        l_ear = (int(lm.landmark[lmPose.LEFT_EAR].x * w), int(lm.landmark[lmPose.LEFT_EAR].y * h))
        l_knee = (int(lm.landmark[lmPose.LEFT_KNEE].x * w), int(lm.landmark[lmPose.LEFT_KNEE].y * h))
        l_ankle = (int(lm.landmark[lmPose.LEFT_ANKLE].x * w), int(lm.landmark[lmPose.LEFT_ANKLE].y * h))
        mid_back = ((l_shldr[0] + l_hip[0]) // 2, (l_shldr[1] + l_hip[1]) // 2)
        l_elbow = (int(lm.landmark[lmPose.LEFT_ELBOW].x * w), int(lm.landmark[lmPose.LEFT_ELBOW].y * h))
        r_elbow = (int(lm.landmark[lmPose.RIGHT_ELBOW].x * w), int(lm.landmark[lmPose.RIGHT_ELBOW].y * h))
        l_wrist = (int(lm.landmark[lmPose.LEFT_WRIST].x * w), int(lm.landmark[lmPose.LEFT_WRIST].y * h))
        r_wrist = (int(lm.landmark[lmPose.RIGHT_WRIST].x * w), int(lm.landmark[lmPose.RIGHT_WRIST].y * h))

        neck_inclination = findAngle(l_shldr[0], l_shldr[1], l_ear[0], l_ear[1])
        torso_inclination = findAngle(l_hip[0], l_hip[1], l_shldr[0], l_shldr[1])

        for pt in [l_shldr, r_shldr, l_ear, l_hip, l_knee, l_ankle, mid_back, l_elbow, r_elbow, l_wrist, r_wrist]:
          cv2.circle(image, pt, 7, yellow, -1)

        lines = [(l_shldr, l_ear), (l_shldr, (l_shldr[0], l_shldr[1] - 100)),
                 (l_hip, l_shldr), (l_hip, (l_hip[0], l_hip[1] - 100)),
                 (mid_back, l_shldr), (mid_back, l_hip),
                 (l_hip, l_knee), (l_knee, l_ankle),
                 (l_shldr, l_elbow), (l_elbow, l_wrist),
                 (r_shldr, r_elbow), (r_elbow, r_wrist)]

        angle_text = f'Neck Inclination: {int(neck_inclination)} | Torso Inclination: {int(torso_inclination)}'
        cv2.putText(image, angle_text, (10, 30), font, 0.7, green, 2)

        for line in lines:
            cv2.line(image, line[0], line[1], green, 2)

        if neck_inclination > NECK_THRESHOLD or torso_inclination > TORSO_THRESHOLD:
            bad_frames += 1
            good_frames = 0

            total_bad += 1

            if neck_inclination > NECK_THRESHOLD:
                cv2.line(image, lines[0][0], lines[0][1], red, 2)
                cv2.line(image, lines[1][0], lines[1][1], red, 2)

            if torso_inclination > TORSO_THRESHOLD:
                cv2.line(image, lines[2][0], lines[2][1], red, 2)
                cv2.line(image, lines[3][0], lines[3][1], red, 2)
        else:
            good_frames += 1
            bad_frames = 0

            total_good += 1

        # Good and bad time in seconds
        good_time = (1/fps) * good_frames
        bad_time = (1/fps) * bad_frames

        with open(arduino_input, "r") as f:
            should_buzz = f.readline().strip()

        if should_buzz == "1":
            arduino.write(b'1')
        else:
            arduino.write(b'0')

        if bad_frames > 0:
            cv2.putText(image, 'Bad Posture', (10, height - 20), font, 1.2, red, 3)
        else:
            cv2.putText(image, 'Good Posture', (10, height - 20), font, 1.2, green, 3)

        with open(arduino_input, "w") as f:
            if bad_time > 1:
                # Add errors when switch
                if should_buzz == "0":
                    total_errors += 1
                f.write("1")
                print("1")
            else:
                f.write("0")
                print("0")
        cv2.imshow('Posture Detection', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    arduino.write(b'x')  
    time.sleep(0.3)
    arduino.close()
    cap.release()
    cv2.destroyAllWindows()

    final_report = "posture_report.txt"

    total_good /= fps
    total_bad /= fps

    endtime = time.time() - start

    # Avoid division by zero
    total_time = total_good + total_bad
    good_ratio = total_good / total_time if total_time > 0 else 0
    bad_ratio = total_bad / total_time if total_time > 0 else 0

    # Choose final message
    if good_ratio >= 0.8:
        final_message = "Great job! You maintained good posture for most of the session."
    elif good_ratio >= 0.5:
        final_message = "Not bad! But there is room for improvement in your posture."
    else:
        final_message = "You need to work on your posture more. Try to sit straighter!"

    # Generate formatted report
    with open(final_report, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("HUMAN POSTURE MONITORING REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"TOTAL TIME RECORD =  {endtime:.2f} seconds\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Metric':<30} {'Time (s)':<10} {'Relative %':<10}\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Good Posture':<30} {total_good:<10.2f} {good_ratio * 100:<10.1f}\n")
        f.write(f"{'Bad Posture':<30} {total_bad:<10.2f} {bad_ratio * 100:<10.1f}\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Posture Alarms':<30} {total_errors:<10}\n")
        f.write("-" * 80 + "\n\n")
        f.write(f"Summary: {final_message}\n")
        f.write("=" * 80 + "\n")
        f.close()