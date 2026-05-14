"""JPEG-domain helpers for the steganography algorithms.

This module keeps the experiment in the quantized DCT domain. It does not parse
or emit JPEG bitstreams; it provides just enough JPEG-domain machinery for the
coursework algorithms to reason about source coefficients and recompression.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


LUMA_Q50 = np.array(
    [
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99],
    ],
    dtype=np.float64,
)


def quality_to_quant_table(quality: int) -> np.ndarray:
    """Return the standard JPEG luminance quantization table for a quality."""

    if not 1 <= quality <= 100:
        raise ValueError("JPEG quality must be in [1, 100]")

    if quality < 50:
        scale = 5000 / quality
    else:
        scale = 200 - quality * 2

    table = np.floor((LUMA_Q50 * scale + 50) / 100)
    return np.clip(table, 1, 255).astype(np.float64)


def jpeg_round(values: np.ndarray | float) -> np.ndarray:
    """Round with JPEG-style half-away-from-zero behavior."""

    arr = np.asarray(values, dtype=np.float64)
    return np.sign(arr) * np.floor(np.abs(arr) + 0.5)


def _dct_matrix() -> np.ndarray:
    matrix = np.zeros((8, 8), dtype=np.float64)
    for k in range(8):
        scale = np.sqrt(1 / 8) if k == 0 else np.sqrt(2 / 8)
        for n in range(8):
            matrix[k, n] = scale * np.cos(((2 * n + 1) * k * np.pi) / 16)
    return matrix


DCT_MATRIX = _dct_matrix()


@dataclass(frozen=True)
class CoeffImage:
    coeffs: np.ndarray
    quant_table: np.ndarray
    original_shape: tuple[int, int]

    @property
    def block_shape(self) -> tuple[int, int]:
        return self.coeffs.shape[:2]


def load_grayscale(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float64)


def save_grayscale(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(np.rint(image), 0, 255).astype(np.uint8)
    Image.fromarray(clipped, mode="L").save(path)


def pad_to_blocks(image: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    height, width = image.shape
    padded_height = ((height + 7) // 8) * 8
    padded_width = ((width + 7) // 8) * 8
    padded = np.pad(
        image,
        ((0, padded_height - height), (0, padded_width - width)),
        mode="edge",
    )
    return padded, (height, width)


def image_to_coeffs(image: np.ndarray, quality: int) -> CoeffImage:
    quant_table = quality_to_quant_table(quality)
    padded, original_shape = pad_to_blocks(image)
    centered = padded - 128.0
    blocks_y, blocks_x = centered.shape[0] // 8, centered.shape[1] // 8
    blocks = centered.reshape(blocks_y, 8, blocks_x, 8).transpose(0, 2, 1, 3)
    dct_blocks = DCT_MATRIX @ blocks @ DCT_MATRIX.T
    coeffs = jpeg_round(dct_blocks / quant_table).astype(np.int32)
    return CoeffImage(coeffs=coeffs, quant_table=quant_table, original_shape=original_shape)


def coeffs_to_image(coeff_image: CoeffImage) -> np.ndarray:
    dequant = coeff_image.coeffs.astype(np.float64) * coeff_image.quant_table
    blocks = DCT_MATRIX.T @ dequant @ DCT_MATRIX
    blocks_y, blocks_x = coeff_image.block_shape
    padded = blocks.transpose(0, 2, 1, 3).reshape(blocks_y * 8, blocks_x * 8)
    image = padded + 128.0
    height, width = coeff_image.original_shape
    return np.clip(image[:height, :width], 0, 255)


def channel_compress(
    coeffs: np.ndarray,
    source_quant_table: np.ndarray,
    channel_quant_table: np.ndarray,
) -> np.ndarray:
    """Requantize coefficients to simulate JPEG channel recompression."""

    scaled = coeffs.astype(np.float64) * source_quant_table / channel_quant_table
    return jpeg_round(scaled).astype(np.int32)


def nonzero_ac_mask(coeffs: np.ndarray) -> np.ndarray:
    mask = coeffs != 0
    mask[:, :, 0, 0] = False
    return mask

