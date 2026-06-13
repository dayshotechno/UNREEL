"""
UNREEL V3 – LUT Generator
Programmatically generates .cube LUT files for underground techno color grading.
Replaces the previous eq-filter approach with professional 3D-LUT color grading.

Usage:
    python -m analyzer.lut_generator
    → Generates all .cube files into luts/
"""

import os
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# LUT configuration
# ---------------------------------------------------------------------------
LUT_DIR = Path(__file__).resolve().parent / "luts"
LUT_SIZE = 33  # 33x33x33 cube – standard for most NLEs and FFmpeg

# ---------------------------------------------------------------------------
# Color math helpers
# ---------------------------------------------------------------------------

def _srgb_to_linear(c: float) -> float:
    """Convert sRGB [0,1] to linear [0,1]."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    """Convert linear [0,1] to sRGB [0,1]."""
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


# ---------------------------------------------------------------------------
# LUT transform functions (input: R,G,B in [0,1] → output: R,G,B in [0,1])
# ---------------------------------------------------------------------------

def _transform_underground_dark(r: float, g: float, b: float) -> tuple[float, float, float]:
    """
    Underground Dark Techno Look:
    - Crushed blacks (lift shadows into near-black)
    - Cyan/teal shadow tint
    - Desaturated midtones
    - Slightly warm highlights
    - Overall contrast boost
    """
    # Convert to linear for processing
    rl, gl, bl = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)

    # Step 1: Crush blacks – apply a power curve to push shadows down
    crush_power = 1.4
    rl = rl ** crush_power
    gl = gl ** crush_power
    bl = bl ** crush_power

    # Step 2: Desaturate (mix towards luminance)
    lum = 0.2126 * rl + 0.7152 * gl + 0.0722 * bl
    desat_amount = 0.35
    rl = rl * (1 - desat_amount) + lum * desat_amount
    gl = gl * (1 - desat_amount) + lum * desat_amount
    bl = bl * (1 - desat_amount) + lum * desat_amount

    # Step 3: Cyan tint in shadows (add blue-green to low values)
    cyan_strength = 0.08
    shadow_mask = max(0.0, 1.0 - lum * 3.0)  # fades out in midtones
    bl += cyan_strength * shadow_mask
    gl += cyan_strength * 0.3 * shadow_mask

    # Step 4: Warm tint in highlights
    highlight_mask = max(0.0, (lum - 0.5) * 2.0)
    rl += 0.03 * highlight_mask

    # Step 5: Contrast S-curve (in linear)
    contrast = 1.15
    rl = 0.5 + (rl - 0.5) * contrast
    gl = 0.5 + (gl - 0.5) * contrast
    bl = 0.5 + (bl - 0.5) * contrast

    return _clamp(rl), _clamp(gl), _clamp(bl)


def _transform_vhs_analog(r: float, g: float, b: float) -> tuple[float, float, float]:
    """
    VHS Analog Look:
    - Color bleed (red channel shifted)
    - Raised blacks (milky shadows)
    - Reduced contrast
    - Slight green color cast
    - Faded highlights
    """
    rl, gl, bl = r, g, b  # Work in sRGB for this one

    # Step 1: Raise blacks
    black_lift = 0.06
    rl = rl * 0.92 + black_lift
    gl = gl * 0.92 + black_lift
    bl = bl * 0.92 + black_lift

    # Step 2: Color bleed – shift red channel slightly (simulate chroma shift)
    lum = 0.2126 * rl + 0.7152 * gl + 0.0722 * bl
    rl = rl * 0.9 + lum * 0.1  # Red bleeds towards luminance

    # Step 3: Green/warm cast
    gl += 0.02
    bl -= 0.01

    # Step 4: Reduce contrast
    contrast = 0.85
    rl = 0.5 + (rl - 0.5) * contrast
    gl = 0.5 + (gl - 0.5) * contrast
    bl = 0.5 + (bl - 0.5) * contrast

    # Step 5: Desaturate slightly
    desat = 0.15
    rl = rl * (1 - desat) + lum * desat
    gl = gl * (1 - desat) + lum * desat
    bl = bl * (1 - desat) + lum * desat

    # Step 6: Clip highlights (faded look)
    rl = min(rl, 0.95)
    gl = min(gl, 0.95)
    bl = min(bl, 0.95)

    return _clamp(rl), _clamp(gl), _clamp(bl)


def _transform_neon_nights(r: float, g: float, b: float) -> tuple[float, float, float]:
    """
    Neon Nights Look:
    - Crushed blacks
    - Highly saturated colors
    - Magenta/blue highlight tint
    - Electric feel for light show clips
    """
    rl = _srgb_to_linear(r)
    gl = _srgb_to_linear(g)
    bl = _srgb_to_linear(b)

    # Step 1: Crush blacks hard
    rl = max(0, (rl - 0.05)) ** 1.3
    gl = max(0, (gl - 0.05)) ** 1.3
    bl = max(0, (bl - 0.05)) ** 1.3

    # Step 2: Boost saturation significantly
    lum = 0.2126 * rl + 0.7152 * gl + 0.0722 * bl
    sat_boost = 1.5
    rl = lum + (rl - lum) * sat_boost
    gl = lum + (gl - lum) * sat_boost
    bl = lum + (bl - lum) * sat_boost

    # Step 3: Magenta/blue tint in highlights
    highlight_mask = max(0.0, (lum - 0.3) * 1.5)
    rl += 0.04 * highlight_mask
    bl += 0.06 * highlight_mask

    # Step 4: Strong contrast
    contrast = 1.25
    rl = 0.5 + (rl - 0.5) * contrast
    gl = 0.5 + (gl - 0.5) * contrast
    bl = 0.5 + (bl - 0.5) * contrast

    return _clamp(rl), _clamp(gl), _clamp(bl)


def _transform_tech_noir(r: float, g: float, b: float) -> tuple[float, float, float]:
    """
    Tech-Noir Look (tarantino preset flashback):
    - Near-monochrome (heavy desaturation), cold industrial tint
    - Very high contrast with crushed blacks and clipped highlights
    - For the daytime/outdoor flashback: cold, mechanical, almost B&W

    Works in sRGB space directly (no linear round-trip) so the contrast
    curve reads as a hard, photographic S-curve.
    """
    # Step 1: luminance (Rec.709)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # Step 2: heavy desaturation toward luma (0.15 = near-monochrome)
    sat = 0.15
    r = lum + (r - lum) * sat
    g = lum + (g - lum) * sat
    b = lum + (b - lum) * sat

    # Step 3: cold industrial tint (lift blue, drop red slightly)
    r *= 0.96
    b *= 1.08

    # Step 4: hard S-curve – crush shadows, then expand contrast around 0.5
    contrast = 1.6

    def _scurve(c: float) -> float:
        c = max(0.0, c - 0.04)            # crush shadows
        return 0.5 + (c - 0.5) * contrast  # expand contrast

    return _clamp(_scurve(r)), _clamp(_scurve(g)), _clamp(_scurve(b))


# ---------------------------------------------------------------------------
# .cube file writer
# ---------------------------------------------------------------------------

def _generate_cube_file(
    transform_fn,
    output_path: Path,
    lut_name: str,
    size: int = LUT_SIZE,
) -> None:
    """Generate an Adobe .cube LUT file from a transform function."""
    total_entries = size ** 3
    print(f"Generating '{lut_name}' ({size}^3 = {total_entries} entries)...")

    with open(output_path, "w") as f:
        # Header
        f.write(f'TITLE "{lut_name}"\n')
        f.write(f'LUT_3D_SIZE {size}\n')
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        f.write("\n")

        # Generate LUT entries
        # .cube format iterates: R changes fastest, then G, then B
        for b_idx in range(size):
            for g_idx in range(size):
                for r_idx in range(size):
                    r_in = r_idx / (size - 1)
                    g_in = g_idx / (size - 1)
                    b_in = b_idx / (size - 1)

                    r_out, g_out, b_out = transform_fn(r_in, g_in, b_in)

                    # Convert linear back to sRGB for underground/neon transforms
                    if transform_fn in (_transform_underground_dark, _transform_neon_nights):
                        r_out = _linear_to_srgb(r_out)
                        g_out = _linear_to_srgb(g_out)
                        b_out = _linear_to_srgb(b_out)

                    f.write(f"{r_out:.6f} {g_out:.6f} {b_out:.6f}\n")

    size_kb = output_path.stat().st_size / 1024
    print(f"  Written to {output_path} ({size_kb:.0f} KB)")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_all_luts(output_dir: Path | None = None) -> dict[str, Path]:
    """Generate all LUT files. Returns dict of {name: path}."""
    out = output_dir or LUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    luts = {
        "underground_dark": (_transform_underground_dark, out / "underground_dark.cube"),
        "vhs_analog": (_transform_vhs_analog, out / "vhs_analog.cube"),
        "neon_nights": (_transform_neon_nights, out / "neon_nights.cube"),
        "tech_noir": (_transform_tech_noir, out / "tech_noir.cube"),
    }

    for name, (fn, path) in luts.items():
        _generate_cube_file(fn, path, name)

    return {name: path for name, (_, path) in luts.items()}


def get_lut_path(lut_name: str, lut_dir: Path | None = None) -> Path:
    """Resolve a LUT name to its .cube file path."""
    d = lut_dir or LUT_DIR
    path = d / f"{lut_name}.cube"
    if not path.exists():
        raise FileNotFoundError(f"LUT file not found: {path}. Run lut_generator first.")
    return path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("UNREEL V3 – LUT Generator")
    print("=" * 40)
    paths = generate_all_luts()
    print(f"\nDone. Generated {len(paths)} LUT files in {LUT_DIR}/")
