"""J-UNIWARD coursework algorithm flow."""

from __future__ import annotations

from costs import j_uniward_costs
from embedding import AlgorithmResult, bit_error_rate, embed_message, extract_message
from jpeg import CoeffImage, channel_compress, quality_to_quant_table


def run_j_uniward(
    cover: CoeffImage,
    channel_quality: int,
    payload_bpnzac: float,
    seed: int,
) -> AlgorithmResult:
    """Embed in the source JPEG domain, then measure extraction after channel compression."""

    costs = j_uniward_costs(cover)
    embedded = embed_message(cover.coeffs, costs.plus, costs.minus, payload_bpnzac, seed)

    channel_quant_table = quality_to_quant_table(channel_quality)
    channel_coeffs = channel_compress(embedded.coeffs, cover.quant_table, channel_quant_table)
    recovered = extract_message(channel_coeffs, embedded.positions)
    ber = bit_error_rate(embedded.message, recovered)

    return AlgorithmResult(
        method="J-UNIWARD",
        stego_coeffs=embedded.coeffs,
        channel_coeffs=channel_coeffs,
        message=embedded.message,
        recovered=recovered,
        positions=embedded.positions,
        message_bits=embedded.message_bits,
        candidates=embedded.candidate_count,
        changes=embedded.changes,
        adjusted_coefficients=0,
        ber_after_channel=ber,
        total_cost=embedded.total_cost,
    )

