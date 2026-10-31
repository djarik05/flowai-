"""
HaGRIDv2 official dataset constants, URLs, and gesture metadata.

Based on official repository: https://github.com/hukenovs/hagrid
License: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Paper: HaGRIDv2: 1M Images for Static and Dynamic Hand Gesture Recognition (arXiv:2412.01508)
"""

from typing import Dict, List

HAGRID_V2_BASE_URL = "https://rndml-team-cv.obs.ru-moscow-1.hc.sbercloud.ru/datasets/hagrid_v2/"
HAGRID_MAIN_BASE_URL = "https://rndml-team-cv.obs.ru-moscow-1.hc.sbercloud.ru/datasets/hagrid/hagrid_dataset_new_554800/"

HAGRID_ANNOTATIONS_URL = f"{HAGRID_V2_BASE_URL}annotations_with_landmarks/annotations.zip"

# Official download URLs per gesture from download.py
HAGRID_GESTURE_URLS: Dict[str, str] = {
    "call": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/call.zip",
    "dislike": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/dislike.zip",
    "fist": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/fist.zip",
    "four": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/four.zip",
    "like": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/like.zip",
    "mute": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/mute.zip",
    "ok": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/ok.zip",
    "one": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/one.zip",
    "palm": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/palm.zip",
    "peace_inverted": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/peace_inverted.zip",
    "peace": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/peace.zip",
    "rock": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/rock.zip",
    "stop_inverted": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/stop_inverted.zip",
    "stop": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/stop.zip",
    "three": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/three.zip",
    "three2": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/three2.zip",
    "two_up_inverted": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/two_up_inverted.zip",
    "two_up": f"{HAGRID_MAIN_BASE_URL}hagrid_dataset/two_up.zip",
    "grabbing": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/grabbing.zip",
    "grip": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/grip.zip",
    "holy": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/holy.zip",
    "point": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/point.zip",
    "three3": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/three3.zip",
    "timeout": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/timeout.zip",
    "xsign": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/xsign.zip",
    "hand_heart": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/hand_heart.zip",
    "hands_heart2": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/hands_heart2.zip",
    "little_finger": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/little_finger.zip",
    "middle_finger": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/middle_finger.zip",
    "take_picture": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/take_picture.zip",
    "three_gun": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/three_gun.zip",
    "thumb_index": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/thumb_index.zip",
    "thumb_index2": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/thumb_index2.zip",
    "no_gesture": f"{HAGRID_V2_BASE_URL}hagrid_v2_zip/no_gesture.zip",
}

# Two-handed gestures officially specified in HaGRIDv2 paper & README
TWO_HANDED_GESTURES = {
    "hand_heart",
    "hands_heart2",
    "thumb_index2",
    "timeout",
    "holy",
    "take_picture",
    "xsign",
}

# Approximate size in GB per gesture archive
HAGRID_CLASS_SIZES: Dict[str, float] = {
    "call": 37.2,
    "dislike": 40.9,
    "fist": 42.3,
    "four": 43.1,
    "like": 42.2,
    "mute": 43.2,
    "ok": 42.5,
    "one": 42.7,
    "palm": 43.0,
    "peace_inverted": 40.5,
    "peace": 41.4,
    "rock": 41.7,
    "stop_inverted": 41.4,
    "stop": 41.8,
    "three": 42.2,
    "three2": 40.2,
    "two_up_inverted": 40.9,
    "two_up": 41.8,
    "grabbing": 48.7,
    "grip": 48.6,
    "holy": 52.7,
    "point": 50.4,
    "three3": 54.0,
    "timeout": 39.5,
    "xsign": 51.3,
    "hand_heart": 39.6,
    "hands_heart2": 42.6,
    "little_finger": 48.6,
    "middle_finger": 50.5,
    "take_picture": 37.3,
    "three_gun": 50.1,
    "thumb_index": 62.8,
    "thumb_index2": 24.8,
    "no_gesture": 4.2,
}

# Human-readable descriptions for each gesture class
HAGRID_CLASS_DESCRIPTIONS: Dict[str, str] = {
    "palm": "Open palm facing camera with all five fingers spread",
    "fist": "Closed fist with fingers tightly curled into palm",
    "like": "Thumbs up with fist closed and thumb pointing upward",
    "dislike": "Thumbs down with fist closed and thumb pointing downward",
    "peace": "V sign with index and middle fingers extended",
    "peace_inverted": "V sign with palm facing inward towards user",
    "one": "Index finger extended pointing upward (number 1)",
    "point": "Index finger pointing forward towards object or camera",
    "stop": "Open hand held vertically with palm facing front",
    "stop_inverted": "Open hand held vertically with back of hand facing camera",
    "ok": "Thumb and index finger touching to form a circle",
    "mute": "Index finger vertically touching lips (shush / mute)",
    "call": "Thumb and pinky extended to ear and mouth (phone call sign)",
    "four": "Four fingers extended with thumb tucked in",
    "three": "Three fingers extended (thumb, index, middle)",
    "three2": "Three fingers extended (index, middle, ring)",
    "three3": "Three fingers extended (middle, ring, pinky)",
    "two_up": "Index and middle fingers together pointing up",
    "two_up_inverted": "Index and middle fingers together pointing down or inverted",
    "rock": "Index and pinky fingers extended (rock on / horns)",
    "grabbing": "Hand clawed inward in a grabbing motion",
    "grip": "Hand in power grip around an imaginary cylinder",
    "holy": "Both hands joined in prayer / holy posture",
    "timeout": "Two hands forming a T-shape (timeout referee sign)",
    "xsign": "Two arms or forearms crossed in an X shape",
    "hand_heart": "Two hands joined forming a heart shape",
    "hands_heart2": "Two hands forming an alternative heart contour",
    "little_finger": "Pinky finger extended (pinky promise / tea gesture)",
    "middle_finger": "Middle finger extended",
    "take_picture": "Hands framing an image / camera viewfinder pose",
    "three_gun": "Hand formed into a gun shape with thumb up and two fingers out",
    "thumb_index": "Thumb and index finger extended in an L shape",
    "thumb_index2": "Two hands forming a rectangle or frame with thumbs and index fingers",
    "no_gesture": "Natural neutral hand posture without active command gesture",
}

# Default suggested mapping from HaGRID classes to GestureFlow IDs
DEFAULT_GESTUREFLOW_MAPPINGS: Dict[str, Dict[str, str]] = {
    "palm": {"target_id": "G001", "target_name": "Open Palm", "action": "map"},
    "fist": {"target_id": "G002", "target_name": "Closed Fist", "action": "map"},
    "like": {"target_id": "G003", "target_name": "Thumbs Up", "action": "map"},
    "peace": {"target_id": "G004", "target_name": "Peace Sign", "action": "map"},
    "point": {"target_id": "G005", "target_name": "Pointing", "action": "map"},
    "one": {"target_id": "G005", "target_name": "Pointing", "action": "map"},
    "stop": {"target_id": "G006", "target_name": "Stop", "action": "map"},
    "no_gesture": {"target_id": None, "target_name": None, "action": "skip"},
}

DATASET_ATTRIBUTION_METADATA = {
    "dataset": "HaGRIDv2",
    "full_title": "HaGRIDv2: 1M Images for Static and Dynamic Hand Gesture Recognition",
    "license": "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)",
    "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
    "license_notice": (
        "This dataset is derived from HaGRIDv2 (HAnd Gesture Recognition Image Dataset) "
        "created by Alexander Kapitanov, Andrey Makhlyarchuk, Karina Kvanchiani, Aleksandr Nagaev, "
        "Roman Kraynov, and Anton Nuzhdin, licensed under CC BY-SA 4.0."
    ),
    "repository": "https://github.com/hukenovs/hagrid",
    "paper": "https://arxiv.org/abs/2412.01508",
}
