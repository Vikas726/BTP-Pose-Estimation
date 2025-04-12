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
OBJ_DET_MODEL_PATH = os.path.join(MODELS_DIR, "object_detection.pt")
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
        print("Error")
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
        raise ValueError(f"❌ Error: Failed to load image -> {image_path}")

    print(f"📌 Processing image: {image_name}")
    # Object detection

    det_results = object_detector(image)[0]

    if det_results and det_results.boxes is not None and len(det_results.boxes) > 0:
        # ✅ Case 1: Object detected, process for pose estimation
        boxes = det_results.boxes.xyxy.cpu().numpy()
        print(f"✅ {len(boxes)} objects detected. Proceeding to pose estimation.")

        det_image = det_results.plot()  # Draw bounding boxes
        pose_image = det_image.copy()

        # Continue with pose estimation...
    else:
        # ❌ Case 2: No object detected, return resized image
        print(f"⚠️ Warning: No objects detected in {image_name}")

        if image is None:
            raise RuntimeError(f"❌ Error: Image '{image_name}' failed to load.")

        resized_image = cv2.resize(image, (500, 500), interpolation=cv2.INTER_LINEAR)
        
        os.makedirs(RESULTS_DIR, exist_ok=True)  # Ensure directory exists
        final_output_path = os.path.join(RESULTS_DIR, f"final_{image_name}")

        if not cv2.imwrite(final_output_path, resized_image):
            raise RuntimeError(f"❌ Error: Failed to save image at {final_output_path}")

        print(f"✅ No object detected. Returning resized image: {final_output_path}")
        return final_output_path


    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box)
        
        # Ensure bounding box is within valid range
        if x1 < 0 or y1 < 0 or x2 > image.shape[1] or y2 > image.shape[0]:
            print(f"⚠️ Warning: Skipping invalid box in {image_name}: {box}")
            continue

        cropped_object = image[y1:y2, x1:x2]
        if cropped_object.size == 0:
            print(f"⚠️ Warning: Empty crop in {image_name}: {box}")
            continue

        # Check if the cropped image is valid before processing
        if cropped_object.shape[0] == 0 or cropped_object.shape[1] == 0:
            print(f"❌ Error: Invalid cropped image at index {i} in {image_name}")
            continue
        
        # Pose estimation with exception handling
        try:
            pose_results = pose_estimator(cropped_object)[0]
        except Exception as e:
            print(f"❌ Error in pose estimation for box {i} -> {str(e)}")
            continue

        if pose_results.keypoints is None or not hasattr(pose_results.keypoints, 'xy'):
            print(f"⚠️ Warning: No keypoints detected for object {i} in {image_name}")
            continue

        keypoints = pose_results.keypoints.xy.cpu().numpy().squeeze()

        if keypoints.ndim != 2 or keypoints.shape[1] < 2:
            print(f"⚠️ Warning: Invalid keypoints format for object {i} in {image_name}")
            continue

        # Draw keypoints
        for keypoint in keypoints:
            x, y = map(float, keypoint[:2])
            cv2.circle(pose_image, (int(x) + x1, int(y) + y1), 5, (0, 255, 0), -1)

    print("flag")
    # Resize processed image to 500x500
    pose_image_resized = cv2.resize(pose_image, (500, 500), interpolation=cv2.INTER_LINEAR)

    final_output_path = os.path.join(RESULTS_DIR, f"final_{image_name}")
    cv2.imwrite(final_output_path, pose_image_resized)

    print(f"✅ Successfully processed {image_name} -> {final_output_path}")
    return final_output_path


