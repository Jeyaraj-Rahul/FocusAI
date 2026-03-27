import cv2


def detect_face(frame, face_cascade):
    """
    Return True if at least one face is detected in the frame, else False.

    This function keeps processing lightweight for better real-time performance.
    """
    # Convert the frame to grayscale because Haar Cascade works faster on gray images.
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Shrink the image before detection to reduce computation per frame.
    small_gray = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)

    # Detect faces in the smaller grayscale image.
    faces = face_cascade.detectMultiScale(
        small_gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(60, 60),
    )

    # Return True when at least one face is found.
    return len(faces) > 0


def main():
    # Load OpenCV's built-in Haar Cascade file for face detection.
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    # Open the default webcam (camera index 0).
    cap = cv2.VideoCapture(0)

    # Reduce capture size for faster processing and smoother real-time detection.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        return

    print("Press 'q' to quit.")

    while True:
        # Read one frame from the webcam.
        success, frame = cap.read()

        if not success:
            print("Warning: Failed to read frame from webcam.")
            break

        # Run face detection and store the boolean result.
        face_found = detect_face(frame, face_cascade)

        # Print the result for each loop iteration.
        print(face_found)

        # Show the current detection result on the video window.
        label = "Face Detected: True" if face_found else "Face Detected: False"
        color = (0, 255, 0) if face_found else (0, 0, 255)
        cv2.putText(
            frame,
            label,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            color,
            2,
        )

        # Display the live webcam feed.
        cv2.imshow("Real-Time Face Detection", frame)

        # Exit when the user presses the q key.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release the webcam and close all OpenCV windows.
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
