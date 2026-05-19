import unittest

from caresight.runtime.healthcheck import healthcheck


class RuntimeHealthcheckTest(unittest.TestCase):
    def test_healthcheck_reports_ready(self) -> None:
        self.assertEqual(healthcheck(), "caresight-runtime-ready")


if __name__ == "__main__":
    unittest.main()
