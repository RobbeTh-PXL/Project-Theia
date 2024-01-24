import cv2
import numpy as np

def detect_eyes(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    eyes_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    # Detect eyes in the image
    eyes = eyes_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    return eyes
    

def track_eyes(frame, eyes):
    eye_centers = []

    for (x, y, w, h) in eyes:
        eye_center = (int(x + w/2), int(y + h/2))
        eye_centers.append(eye_center)

        # Draw a rectangle around the eyes
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Draw a point at the center of each eye
        cv2.circle(frame, eye_center, 2, (0, 255, 0), -1)

    return eye_centers

def main():
    # Open a video capture object (0 is typically the default camera)
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        eyes = detect_eyes(frame)
        eye_centers = track_eyes(frame, eyes)

        # Display the frame
        cv2.imshow('Eye Tracking', frame)

        # Break the loop if 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
