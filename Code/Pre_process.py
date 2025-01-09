import os
import cv2
import numpy as np
import time

def augment(frame2, frame, boxes):
    mask = np.zeros(frame.shape, dtype=np.uint8)
    for box in boxes:
        x, y, w, h = box
        object_patch = frame[y:y+h, x:x+w]
        mask[y:y+h, x:x+w] = object_patch
    # cv2.imshow("Image2", mask)

    return mask

def process_video(video_path, output_dir):
    net = cv2.dnn.readNet("yolov8", "yolov8.cfg")
    classes = []
    with open("coco", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layer_names = net.getLayerNames()
    outputlayers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    cap = cv2.VideoCapture(video_path)
    font = cv2.FONT_HERSHEY_PLAIN
    starting_time = time.time()
    frame_id = 0
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    video_name = os.path.basename(video_path)
    video_name_no_ext = os.path.splitext(video_name)[0]

    output_video_dir = os.path.join(output_dir, video_name_no_ext)
    if not os.path.exists(output_video_dir):
        os.makedirs(output_video_dir)
    human_class_index = 0
    frame_counter = 0
    for f in range(length - 2):
        _, frame = cap.read()
        frame = cv2.resize(frame, (1280, 720))
        frame_id += 1
        frame2 = frame
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(outputlayers)
        class_ids = []
        confidences = []
        boxes = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.1 and class_id == human_class_index:
                    center_x = int(detection[0] * 1280)
                    center_y = int(detection[1] * 720)
                    w = int(detection[2] * 1280)
                    h = int(detection[3] * 720)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        if not boxes:
            continue

        frame_with_masks = augment(frame2, frame, boxes)

        elapsed_time = time.time() - starting_time
        fps = frame_id / elapsed_time
        frame_name = f"frame_{frame_counter:04d}.jpg"
        print(">>>>>>>>>>>>>>>>>>>>>>>>>",frame_name )
        frame_path = os.path.join(output_video_dir, frame_name)
        cv2.imwrite(frame_path, frame_with_masks)

        frame_counter += 1


    cap.release()

input_dir = "Data"
output_base_dir = "Out_Data"

for class_folder in os.listdir(input_dir):
    class_path = os.path.join(input_dir, class_folder)
    output_class_dir = os.path.join(output_base_dir, class_folder)

    if not os.path.exists(output_class_dir):
        os.makedirs(output_class_dir)

    for video_file in os.listdir(class_path):
        video_path = os.path.join(class_path, video_file)
        process_video(video_path, output_class_dir)
