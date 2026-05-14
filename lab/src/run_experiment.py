"""Run the J-UNIWARD and J-UNIWARD-P experiments."""

from __future__ import annotations

from collections import defaultdict
import csv
import hashlib
import re
from pathlib import Path

import numpy as np

from .lib.adjustment import adjust_coefficients_for_channel
from .lib.costs import j_uniward_costs
from .lib.embedding import AlgorithmResult, bit_error_rate, embed_message, extract_message
from .lib.jpeg import (
    CoeffImage,
    channel_compress,
    image_to_coeffs,
    load_grayscale,
    quality_to_quant_table,
)


LAB_ROOT = Path(__file__).resolve().parents[1]
PREPARED_ROOT = LAB_ROOT / "data" / "prepared"
RESULTS_ROOT = LAB_ROOT / "results" / "table1"
IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".pgm", ".tif", ".tiff"}
PAYLOADS = (0.1, 0.2, 0.3, 0.4)
CHANNEL_QUALITY_BY_COVER_QUALITY = {100: 95, 95: 75}
SEED = 20260514
PREPARED_DIR_PATTERN = re.compile(r"^(?P<dataset>.+)-q(?P<quality>\d+)$")


def _iter_images(path: Path) -> list[Path]:
    return sorted(item for item in path.rglob("*") if item.suffix.lower() in IMAGE_SUFFIXES)


def _coeff_image_like(cover: CoeffImage, coeffs: np.ndarray, quant_table: np.ndarray) -> CoeffImage:
    return CoeffImage(
        coeffs=coeffs,
        quant_table=quant_table,
        original_shape=cover.original_shape,
    )


def run_j_uniward(
    cover: CoeffImage,
    channel_quality: int,
    payload_bpnzac: float,
    seed: int,
) -> AlgorithmResult:
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


def run_j_uniward_p(
    cover: CoeffImage,
    channel_quality: int,
    payload_bpnzac: float,
    seed: int,
) -> AlgorithmResult:
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


def _prepared_sets() -> list[tuple[str, int, Path]]:
    sets: list[tuple[str, int, Path]] = []
    for path in sorted(PREPARED_ROOT.iterdir()) if PREPARED_ROOT.exists() else []:
        if not path.is_dir():
            continue
        match = PREPARED_DIR_PATTERN.match(path.name)
        if match is None:
            continue
        quality = int(match.group("quality"))
        if quality not in CHANNEL_QUALITY_BY_COVER_QUALITY:
            continue
        sets.append((match.group("dataset"), quality, path))
    return sets


def _row(
    dataset: str,
    image_path: Path,
    cover_quality: int,
    channel_quality: int,
    payload: float,
    result: AlgorithmResult,
) -> dict[str, object]:
    return {
        "dataset": dataset,
        "image": image_path.name,
        "cover_quality": cover_quality,
        "channel_quality": channel_quality,
        "payload_bpnzac": payload,
        "method": result.method,
        "message_bits": result.message_bits,
        "candidates": result.candidates,
        "changes": result.changes,
        "adjusted_coefficients": result.adjusted_coefficients,
        "ber_after_channel": result.ber_after_channel,
        "total_cost": result.total_cost,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("no rows to write")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = (
            row["dataset"],
            row["cover_quality"],
            row["channel_quality"],
            row["payload_bpnzac"],
            row["method"],
        )
        grouped[key].append(row)

    summary_rows: list[dict[str, object]] = []
    for (dataset, cover_quality, channel_quality, payload, method), items in sorted(grouped.items()):
        summary_rows.append(
            {
                "dataset": dataset,
                "cover_quality": cover_quality,
                "channel_quality": channel_quality,
                "payload_bpnzac": payload,
                "method": method,
                "images": len(items),
                "avg_message_bits": sum(float(item["message_bits"]) for item in items) / len(items),
                "avg_changes": sum(float(item["changes"]) for item in items) / len(items),
                "avg_adjusted_coefficients": sum(float(item["adjusted_coefficients"]) for item in items) / len(items),
                "avg_ber_after_channel": sum(float(item["ber_after_channel"]) for item in items) / len(items),
                "avg_total_cost": sum(float(item["total_cost"]) for item in items) / len(items),
            }
        )
    return summary_rows


def _seed_for(image_path: Path, payload: float, method: str) -> int:
    material = f"{SEED}:{image_path.name}:{payload}:{method}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "big")


def run() -> None:
    prepared_sets = _prepared_sets()
    if not prepared_sets:
        raise SystemExit("no prepared datasets found; run `python main.py prepare` first")

    rows: list[dict[str, object]] = []
    for dataset, cover_quality, directory in prepared_sets:
        channel_quality = CHANNEL_QUALITY_BY_COVER_QUALITY[cover_quality]
        images = _iter_images(directory)
        if not images:
            print(f"Skipping empty prepared dataset: {directory}")
            continue

        for image_path in images:
            cover_pixels = load_grayscale(image_path)
            cover = image_to_coeffs(cover_pixels, cover_quality)
            for payload in PAYLOADS:
                j_result = run_j_uniward(
                    cover,
                    channel_quality=channel_quality,
                    payload_bpnzac=payload,
                    seed=_seed_for(image_path, payload, "J-UNIWARD"),
                )
                jp_result = run_j_uniward_p(
                    cover,
                    channel_quality=channel_quality,
                    payload_bpnzac=payload,
                    seed=_seed_for(image_path, payload, "J-UNIWARD-P"),
                )
                rows.append(_row(dataset, image_path, cover_quality, channel_quality, payload, j_result))
                rows.append(_row(dataset, image_path, cover_quality, channel_quality, payload, jp_result))

    if not rows:
        raise SystemExit("no experiment rows were produced")

    results_path = RESULTS_ROOT / "results.csv"
    summary_path = RESULTS_ROOT / "summary.csv"
    _write_csv(results_path, rows)
    _write_csv(summary_path, _summary(rows))
    print(f"Wrote {results_path}")
    print(f"Wrote {summary_path}")
