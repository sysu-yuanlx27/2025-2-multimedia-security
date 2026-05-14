"""Cost-guided embedding, extraction, and shared algorithm results."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from costs import WET_COST
from jpeg import nonzero_ac_mask


@dataclass(frozen=True)
class EmbeddingResult:
    coeffs: np.ndarray
    message: np.ndarray
    positions: np.ndarray
    changes: int
    total_cost: float
    candidate_count: int

    @property
    def message_bits(self) -> int:
        return int(self.message.size)


@dataclass(frozen=True)
class AlgorithmResult:
    method: str
    stego_coeffs: np.ndarray
    channel_coeffs: np.ndarray
    message: np.ndarray
    recovered: np.ndarray
    positions: np.ndarray
    message_bits: int
    candidates: int
    changes: int
    adjusted_coefficients: int
    ber_after_channel: float
    total_cost: float
    target_channel_coeffs: np.ndarray | None = None


def coefficient_lsb(values: np.ndarray) -> np.ndarray:
    return (np.abs(values).astype(np.int32) & 1).astype(np.uint8)


def bit_error_rate(expected: np.ndarray, actual: np.ndarray) -> float:
    if expected.shape != actual.shape:
        raise ValueError("expected and actual messages must have the same shape")
    if expected.size == 0:
        return 0.0
    return float(np.mean(expected.astype(np.uint8) != actual.astype(np.uint8)))


def _candidate_positions(coeffs: np.ndarray, plus_cost: np.ndarray, minus_cost: np.ndarray) -> np.ndarray:
    usable = nonzero_ac_mask(coeffs)
    usable &= np.minimum(plus_cost, minus_cost) < WET_COST
    return np.argwhere(usable)


def embed_message(
    coeffs: np.ndarray,
    plus_cost: np.ndarray,
    minus_cost: np.ndarray,
    payload_bpnzac: float,
    seed: int,
) -> EmbeddingResult:
    """Embed a random message with cost-guided LSB matching.

    Payload is measured in bits per non-zero AC coefficient. A full J-UNIWARD
    system normally uses STC; this coursework implementation uses deterministic
    low-cost coefficient selection plus LSB matching so extraction and BER are
    real and reproducible without extra coding libraries.
    """

    if payload_bpnzac <= 0:
        raise ValueError("payload_bpnzac must be positive")

    candidates = _candidate_positions(coeffs, plus_cost, minus_cost)
    nzac_count = int(nonzero_ac_mask(coeffs).sum())
    message_bits = int(np.floor(payload_bpnzac * nzac_count))
    if message_bits <= 0:
        raise ValueError("payload is too small for the available non-zero AC coefficients")
    if message_bits > len(candidates):
        raise ValueError(
            f"payload requires {message_bits} coefficients, but only {len(candidates)} are usable"
        )

    rng = np.random.default_rng(seed)
    jitter = rng.random(len(candidates)) * 1.0e-9
    flat_costs = np.minimum(
        plus_cost[tuple(candidates.T)],
        minus_cost[tuple(candidates.T)],
    )
    order = np.argsort(flat_costs + jitter)
    positions = candidates[order[:message_bits]]
    message = rng.integers(0, 2, size=message_bits, dtype=np.uint8)

    stego = coeffs.copy()
    changes = 0
    total_cost = 0.0

    for bit, pos in zip(message, positions):
        idx = tuple(pos)
        current_bit = int(coefficient_lsb(stego[idx]))
        if current_bit == int(bit):
            continue

        p_cost = plus_cost[idx]
        m_cost = minus_cost[idx]
        if p_cost <= m_cost:
            stego[idx] += 1
            total_cost += float(p_cost)
        else:
            stego[idx] -= 1
            total_cost += float(m_cost)
        changes += 1

    return EmbeddingResult(
        coeffs=stego,
        message=message,
        positions=positions.astype(np.int32),
        changes=changes,
        total_cost=total_cost,
        candidate_count=int(len(candidates)),
    )


def extract_message(coeffs: np.ndarray, positions: np.ndarray) -> np.ndarray:
    return coefficient_lsb(coeffs[tuple(positions.T)])

