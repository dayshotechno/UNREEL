import cv2
import math
from ultralytics import YOLO

# Globale YOLO Modell-Instanz (wird lazy geladen, um Startzeit zu minimieren)
_model = None

def get_yolo_model():
    global _model
    if _model is None:
        # yolo11n.pt wird automatisch heruntergeladen, falls nicht lokal vorhanden
        _model = YOLO("yolo11n.pt")
    return _model

def sample_x_center(video_path, start_time=0.0, end_time=None, samples=10, imgsz=640):
    """
    Schneller JIT-Pfad für das Auto-Framing: Da der Export ohnehin nur den
    DURCHSCHNITT der x-Positionen nutzt (statischer Crop), reichen wenige
    direkt angesprungene Frames. Im Gegensatz zu analyze_tracking() wird
    nicht jeder Frame dekodiert (bei 120-fps-Material hunderte Reads),
    sondern pro Sample gezielt geseekt.

    Returns:
        Durchschnittliche normalisierte x-Position der größten Person
        (0.0–1.0) oder None, wenn keine Person gefunden wurde.
    """
    try:
        model = get_yolo_model()
    except Exception as e:
        print(f"YOLO konnte nicht geladen werden: {e}")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    if end_time is None:
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        end_time = (total / video_fps) if total > 0 else start_time + 1.0

    span = max(0.0, end_time - start_time)
    # Samples gleichmäßig im Fenster verteilen (Mittelpunkte der Teilstücke)
    times = [start_time + span * (i + 0.5) / samples for i in range(samples)]

    positions = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ret, frame = cap.read()
        if not ret:
            continue
        results = model.predict(frame, classes=[0], verbose=False, imgsz=imgsz)
        best, max_area = None, 0
        if len(results) > 0:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                area = (x2 - x1) * (y2 - y1)
                if area > max_area:
                    max_area = area
                    best = float(((x1 + x2) / 2.0) / frame.shape[1])
        if best is not None:
            positions.append(best)

    cap.release()
    if not positions:
        return None
    return sum(positions) / len(positions)


def analyze_tracking(video_path, fps=1.0, start_time=0.0, end_time=None, progress_callback=None):
    """
    Führt YOLO-basiertes Tracking von Personen (Klasse 0) im Video durch.
    
    Args:
        video_path: Pfad zum Video
        fps: Wie viele Frames pro Sekunde für Tracking analysiert werden sollen (z.B. 1 oder 2)
        start_time: Startzeit in Sekunden (für Just-In-Time Tracking)
        end_time: Endzeit in Sekunden (für Just-In-Time Tracking)
        progress_callback: Callback für Fortschritt
        
    Returns:
        Liste von Dicts: [{"time": 0.0, "x_center": 0.5}, ...]
    """
    try:
        model = get_yolo_model()
    except Exception as e:
        print(f"YOLO konnte nicht geladen werden: {e}")
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        video_fps = 30.0
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, int(video_fps / fps))
    
    tracking_data = []
    
    frame_idx = 0
    if start_time > 0.0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000.0)
        frame_idx = int(start_time * video_fps)
        
    analyzed = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        current_time = frame_idx / video_fps
        if end_time is not None and current_time > end_time:
            break
            
        if frame_idx % frame_interval == 0:
            # Verkleinern für schnellere Inferenz (640px ist Standard für YOLOn)
            # YOLO skaliert intern sowieso, aber OpenCV resize spart Speicher/Zeit beim Übergeben
            results = model.predict(frame, classes=[0], verbose=False, imgsz=640)
            
            best_person = None
            max_area = 0
            
            if len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    # box.xyxy: [x1, y1, x2, y2]
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    area = (x2 - x1) * (y2 - y1)
                    if area > max_area:
                        max_area = area
                        # Mitte berechnen und normalisieren
                        x_center = (x1 + x2) / 2.0
                        norm_x = float(x_center / frame.shape[1])
                        best_person = norm_x
                        
            # Wenn Person gefunden, X-Koordinate speichern (sonst 0.5 als Fallback in der späteren Verarbeitung)
            if best_person is not None:
                tracking_data.append({
                    "time": round(current_time, 2),
                    "x_center": round(best_person, 4)
                })
                
            analyzed += 1
            if progress_callback and analyzed % 10 == 0:
                pct = int((frame_idx / max(total_frames, 1)) * 100)
                progress_callback("tracking", pct, f"Tracking: Frame {frame_idx}/{total_frames} (Auto-Framing)")

        frame_idx += 1
        
    cap.release()
    return tracking_data
