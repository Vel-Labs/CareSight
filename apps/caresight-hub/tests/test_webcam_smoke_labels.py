import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "yolo26_webcam_smoke.py"
)


def load_webcam_smoke_module():
    spec = importlib.util.spec_from_file_location("yolo26_webcam_smoke", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WebcamSmokeLabelsTest(unittest.TestCase):
    def test_placeholder_class_names_fall_back_to_coco(self) -> None:
        module = load_webcam_smoke_module()

        self.assertEqual(module.class_name({15: "class15"}, 15), "cat")
        self.assertEqual(module.class_name({"16": "Class_16"}, 16), "dog")
        self.assertEqual(module.class_name({}, 57), "couch")


if __name__ == "__main__":
    unittest.main()
