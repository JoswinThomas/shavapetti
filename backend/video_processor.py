import cv2
import os


def extract_frames(video_path):

    # Open the video
    video = cv2.VideoCapture(video_path)

    # Check if video opened successfully
    if not video.isOpened():
        print("Could not open video")
        return []

    # Get video information
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)

    duration = frame_count / fps

    print("FPS:", fps)
    print("Total frames:", int(frame_count))
    print("Duration:", round(duration, 2), "seconds")

    # Folder to save extracted frames
    frames_folder = "frames"

    os.makedirs(frames_folder, exist_ok=True)

    extracted_frames = []

    # We will take one frame every 3 seconds
    interval = 3

    current_time = 0
    frame_number = 0

    while current_time < duration:

        # Move video to the required time
        video.set(
            cv2.CAP_PROP_POS_MSEC,
            current_time * 1000
        )

        success, frame = video.read()

        if success:

            filename = os.path.join(
                frames_folder,
                f"frame_{frame_number}.jpg"
            )

            cv2.imwrite(filename, frame)

            extracted_frames.append(filename)

            print("Extracted:", filename)

            frame_number += 1

        current_time += interval

    video.release()

    print(
        "Total frames extracted:",
        len(extracted_frames)
    )

    return extracted_frames