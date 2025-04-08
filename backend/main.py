import os
import cv2
import shutil
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

# Define directory structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Model paths
OBJ_DET_MODEL_PATH = os.path.join(MODELS_DIR, "yolov8s.pt")
POSE_EST_MODEL_PATH = os.path.join(MODELS_DIR, "yolov8s-pose.pt")

print(OBJ_DET_MODEL_PATH)
print(POSE_EST_MODEL_PATH)

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Load YOLO models
object_detector = YOLO(OBJ_DET_MODEL_PATH)
pose_estimator = YOLO(POSE_EST_MODEL_PATH)

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        final_output_path = process_image(file_path)
        print(final_output_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    if os.path.exists(final_output_path):
        ext = os.path.splitext(final_output_path)[1].lower()
        media_type = "image/png" if ext == ".png" else "image/jpeg"
        return FileResponse(final_output_path, media_type=media_type)
    else:
        return JSONResponse(status_code=500, content={"error": "Processed image not found"})

def process_image(image_path):
    image_name = os.path.basename(image_path)
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Error loading image: {image_path}")

    det_results = object_detector(image)[0]

    if not det_results.boxes:
        det_image = image
    else:
        boxes = det_results.boxes.xyxy.cpu().numpy() if det_results.boxes is not None else []
        det_image = det_results.plot()
    pose_image = det_image.copy()

    for box in boxes:
        x1, y1, x2, y2 = map(int, box)
        cropped_object = image[y1:y2, x1:x2]

        if cropped_object.size == 0:
            continue

        pose_results = pose_estimator(cropped_object)[0]

        if pose_results.keypoints is None or not hasattr(pose_results.keypoints, 'xy'):
            continue

        keypoints = pose_results.keypoints.xy.cpu().numpy().squeeze()

        if keypoints.ndim != 2 or keypoints.shape[1] < 2:
            continue

        for keypoint in keypoints:
            x, y = map(float, keypoint[:2])
            cv2.circle(pose_image, (int(x) + x1, int(y) + y1), 5, (0, 255, 0), -1)

    pose_image_resized = cv2.resize(pose_image, (500, 500), interpolation=cv2.INTER_LINEAR)

    final_output_path = os.path.join(RESULTS_DIR, f"final_{image_name}")
    cv2.imwrite(final_output_path, pose_image_resized)

    return final_output_path
