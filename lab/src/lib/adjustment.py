"""Coefficient adjustment for the J-UNIWARD-P algorithm."""

from __future__ import annotations

import numpy as np

from .jpeg import channel_compress, jpeg_round


def _ensure_recompression_direction(source_quant_table: np.ndarray, channel_quant_table: np.ndarray) -> None:
    if np.any(channel_quant_table < source_quant_table):
        raise ValueError(
            "J-UNIWARD-P requires channel quantization steps to be greater than "
            "or equal to source quantization steps; use a channel quality no "
            "higher than the source quality."
        )


def adjust_coefficients_for_channel(
    original_coeffs: np.ndarray,
    target_channel_coeffs: np.ndarray,
    source_quant_table: np.ndarray,
    channel_quant_table: np.ndarray,
) -> tuple[np.ndarray, int]:
    """Find source-domain coefficients that recompress to the target channel.

    For every target-channel coefficient that differs from the current channel
    output, choose the nearest source-domain integer coefficient so that:

        round(I * source_quant_table / channel_quant_table) == target

    A final verification pass raises a clear error if any target is unreachable.
    """

    _ensure_recompression_direction(source_quant_table, channel_quant_table)

    adjusted = original_coeffs.copy()
    current_channel = channel_compress(adjusted, source_quant_table, channel_quant_table)
    changed = np.argwhere(current_channel != target_channel_coeffs)
    if changed.size == 0:
        return adjusted, 0

    for pos in changed:
        by, bx, u, v = (int(x) for x in pos)
        original = int(original_coeffs[by, bx, u, v])
        target = int(target_channel_coeffs[by, bx, u, v])
        source_q = float(source_quant_table[u, v])
        channel_q = float(channel_quant_table[u, v])

        ratio = source_q / channel_q
        search_radius = int(np.ceil(channel_q / source_q * 4)) + 16
        best_value = None
        best_distance = None

        for delta in range(search_radius + 1):
            options = [original] if delta == 0 else [original - delta, original + delta]
            for candidate in options:
                mapped = int(jpeg_round(candidate * ratio))
                if mapped != target:
                    continue
                distance = abs(candidate - original)
                if best_distance is None or distance < best_distance:
                    best_value = candidate
                    best_distance = distance
            if best_value is not None:
                break

        if best_value is None:
            low = int(np.floor((target - 0.5) / ratio)) - 2
            high = int(np.ceil((target + 0.5) / ratio)) + 2
            candidates = np.arange(min(low, high), max(low, high) + 1)
            mapped = jpeg_round(candidates.astype(np.float64) * ratio).astype(np.int32)
            valid = candidates[mapped == target]
            if valid.size == 0:
                raise RuntimeError(f"could not adjust coefficient {tuple(pos)} to channel target {target}")
            best_value = int(valid[np.argmin(np.abs(valid - original))])

        adjusted[by, bx, u, v] = best_value

    recompressed = channel_compress(adjusted, source_quant_table, channel_quant_table)
    if not np.array_equal(recompressed, target_channel_coeffs):
        raise RuntimeError("coefficient adjustment did not reproduce the target channel coefficients")

    return adjusted, int(len(changed))

