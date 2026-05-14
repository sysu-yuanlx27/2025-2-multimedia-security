"""Distortion costs for coursework J-UNIWARD-style coefficient changes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from jpeg import CoeffImage, DCT_MATRIX, coeffs_to_image


WET_COST = 1.0e13


@dataclass(frozen=True)
class CostMap:
    plus: np.ndarray
    minus: np.ndarray


def _gradient_energy(image: np.ndarray) -> np.ndarray:
    gx = np.zeros_like(image, dtype=np.float64)
    gy = np.zeros_like(image, dtype=np.float64)
    gx[:, 1:-1] = np.abs(image[:, 2:] - image[:, :-2]) / 2.0
    gx[:, 0] = np.abs(image[:, 1] - image[:, 0])
    gx[:, -1] = np.abs(image[:, -1] - image[:, -2])
    gy[1:-1, :] = np.abs(image[2:, :] - image[:-2, :]) / 2.0
    gy[0, :] = np.abs(image[1, :] - image[0, :])
    gy[-1, :] = np.abs(image[-1, :] - image[-2, :])
    return gx + gy


def j_uniward_costs(coeff_image: CoeffImage, sigma: float = 1.0) -> CostMap:
    """Compute practical additive costs for J-UNIWARD-style embedding.

    This is a coursework approximation, not a full reproduction of the original
    J-UNIWARD wavelet residual distortion. It preserves the central adaptive
    idea: high-activity regions and high-frequency coefficients receive lower
    embedding costs, while DC and unsafe sign-changing moves are made wet.
    """

    image = coeffs_to_image(coeff_image)
    texture = _gradient_energy(image)
    blocks_y, blocks_x = coeff_image.block_shape
    texture_blocks = texture.reshape(blocks_y, 8, blocks_x, 8).transpose(0, 2, 1, 3)
    block_activity = texture_blocks.mean(axis=(2, 3)) + sigma

    ac_energy = np.sqrt(np.mean(coeff_image.coeffs[:, :, 1:, :].astype(np.float64) ** 2, axis=(2, 3)))
    block_activity = block_activity + ac_energy

    basis_impact = np.zeros((8, 8), dtype=np.float64)
    for u in range(8):
        for v in range(8):
            basis = np.zeros((8, 8), dtype=np.float64)
            basis[u, v] = coeff_image.quant_table[u, v]
            spatial = DCT_MATRIX.T @ basis @ DCT_MATRIX
            basis_impact[u, v] = np.sum(np.abs(spatial))

    frequency_weight = 1.0 / np.sqrt(1.0 + np.add.outer(np.arange(8), np.arange(8)))
    base = basis_impact * frequency_weight
    costs = base[None, None, :, :] / block_activity[:, :, None, None]

    plus = costs.copy()
    minus = costs.copy()
    plus[:, :, 0, 0] = WET_COST
    minus[:, :, 0, 0] = WET_COST

    coeffs = coeff_image.coeffs
    minus[coeffs == 1] = WET_COST
    plus[coeffs == -1] = WET_COST
    plus[coeffs == 0] *= 2.0
    minus[coeffs == 0] *= 2.0

    return CostMap(plus=plus.astype(np.float64), minus=minus.astype(np.float64))

