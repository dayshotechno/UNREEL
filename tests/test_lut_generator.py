"""Offline tests for lut_generator.py – color math and .cube file structure."""
import unittest
import tempfile
from pathlib import Path

import lut_generator as lg


class TestColorMath(unittest.TestCase):
    def test_clamp_bounds(self):
        self.assertEqual(lg._clamp(-0.5), 0.0)
        self.assertEqual(lg._clamp(1.5), 1.0)
        self.assertEqual(lg._clamp(0.42), 0.42)

    def test_srgb_linear_roundtrip(self):
        for c in (0.0, 0.04, 0.2, 0.5, 0.8, 1.0):
            back = lg._linear_to_srgb(lg._srgb_to_linear(c))
            self.assertAlmostEqual(back, c, places=5)

    def test_transforms_return_valid_rgb(self):
        transforms = (
            lg._transform_underground_dark,
            lg._transform_vhs_analog,
            lg._transform_neon_nights,
        )
        for fn in transforms:
            for rgb in [(0.0, 0.0, 0.0), (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), (0.2, 0.6, 0.9)]:
                out = fn(*rgb)
                self.assertEqual(len(out), 3)
                for v in out:
                    self.assertGreaterEqual(v, 0.0)
                    self.assertLessEqual(v, 1.0)


class TestCubeFile(unittest.TestCase):
    def test_generate_cube_file_structure(self):
        # Use a tiny size for speed; structure must still be valid.
        size = 3
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "test.cube"
            lg._generate_cube_file(lg._transform_vhs_analog, out, "test", size=size)
            self.assertTrue(out.exists())

            lines = out.read_text().splitlines()
            self.assertIn(f"LUT_3D_SIZE {size}", lines)
            self.assertIn('TITLE "test"', lines)

            data_lines = [
                ln for ln in lines
                if ln and ln[0].isdigit() and len(ln.split()) == 3
            ]
            self.assertEqual(len(data_lines), size ** 3)

            # Every data triple must be parseable floats in [0,1].
            r, g, b = (float(x) for x in data_lines[0].split())
            for v in (r, g, b):
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)

    def test_get_lut_path_resolves_and_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "underground_dark.cube").write_text("TITLE \"x\"\n")
            self.assertEqual(
                lg.get_lut_path("underground_dark", lut_dir=d),
                d / "underground_dark.cube",
            )
            with self.assertRaises(FileNotFoundError):
                lg.get_lut_path("does_not_exist", lut_dir=d)


if __name__ == "__main__":
    unittest.main()
