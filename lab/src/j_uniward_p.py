"""J-UNIWARD-P coursework algorithm flow."""

from __future__ import annotations

from adjustment import adjust_coefficients_for_channel
from costs import j_uniward_costs
from embedding import AlgorithmResult, bit_error_rate, embed_message, extract_message
from jpeg import CoeffImage, channel_compress, quality_to_quant_table


def _coeff_image_like(cover: CoeffImage, coeffs, quant_table) -> CoeffImage:
    return CoeffImage(
        coeffs=coeffs,
        quant_table=quant_table,
        original_shape=cover.original_shape,
    )


def run_j_uniward_p(
    cover: CoeffImage,
    channel_quality: int,
    payload_bpnzac: float,
    seed: int,
) -> AlgorithmResult:
    """Embed in the channel domain, then adjust source coefficients to hit that target."""

    channel_quant_table = quality_to_quant_table(channel_quality)
    cover_channel_coeffs = channel_compress(cover.coeffs, cover.quant_table, channel_quant_table)
    cover_channel = _coeff_image_like(cover, cover_channel_coeffs, channel_quant_table)

    costs = j_uniward_costs(cover_channel)
    embedded_target = embed_message(
        cover_channel.coeffs,
        costs.plus,
        costs.minus,
        payload_bpnzac,
        seed,
    )

    adjusted_coeffs, adjusted_count = adjust_coefficients_for_channel(
        cover.coeffs,
        embedded_target.coeffs,
        cover.quant_table,
        channel_quant_table,
    )

    channel_coeffs = channel_compress(adjusted_coeffs, cover.quant_table, channel_quant_table)
    recovered = extract_message(channel_coeffs, embedded_target.positions)
    ber = bit_error_rate(embedded_target.message, recovered)

    return AlgorithmResult(
        method="J-UNIWARD-P",
        stego_coeffs=adjusted_coeffs,
        channel_coeffs=channel_coeffs,
        message=embedded_target.message,
        recovered=recovered,
        positions=embedded_target.positions,
        message_bits=embedded_target.message_bits,
        candidates=embedded_target.candidate_count,
        changes=embedded_target.changes,
        adjusted_coefficients=adjusted_count,
        ber_after_channel=ber,
        total_cost=embedded_target.total_cost,
        target_channel_coeffs=embedded_target.coeffs,
    )
