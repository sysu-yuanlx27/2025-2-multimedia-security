"""Prepare local BOSSbase and UCID images for the experiments."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn, TimeRemainingColumn


LAB_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = LAB_ROOT / "data"
RAW_ROOT = DATA_ROOT / "raw"
PREPARED_ROOT = DATA_ROOT / "prepared"
IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".pgm", ".tif", ".tiff"}
ORIGINAL_QUALITIES = (100, 95)
SAMPLE_IMAGES_PER_DATASET = 100
SEED = 20260514
CONSOLE = Console()


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    display_name: str
    raw_dir: Path
    prepared_prefix: str
    manual_url: str


DATASETS = (
    DatasetSpec(
        key="bossbase",
        display_name="BOSSbase-1.01",
        raw_dir=RAW_ROOT / "BOSSbase-1.01",
        prepared_prefix="bossbase",
        manual_url="https://dde.binghamton.edu/download/",
    ),
    DatasetSpec(
        key="ucid",
        display_name="UCID",
        raw_dir=RAW_ROOT / "UCID",
        prepared_prefix="ucid",
        manual_url="https://qualinet.github.io/databases/image/uncompressed_colour_image_database_ucid/",
    ),
)


def _iter_images(path: Path) -> list[Path]:
    return sorted(item for item in path.rglob("*") if item.suffix.lower() in IMAGE_SUFFIXES)


def _has_images(path: Path) -> bool:
    return path.exists() and any(_iter_images(path))


def _missing_datasets() -> list[DatasetSpec]:
    return [spec for spec in DATASETS if not _has_images(spec.raw_dir)]


def _print_manual_instructions(missing: list[DatasetSpec]) -> None:
    print("Missing raw datasets. Please download them manually and place them here:")
    for spec in missing:
        print(f"- {spec.display_name}: {spec.raw_dir}")
        print(f"  Source: {spec.manual_url}")


def _ensure_raw_datasets() -> None:
    missing = _missing_datasets()
    if not missing:
        return

    _print_manual_instructions(missing)
    raise SystemExit(1)


def _reset_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for image in _iter_images(path):
        image.unlink()


def _make_progress() -> Progress:
    return Progress(
        TextColumn("[progress.description]{task.description:<28}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("{task.percentage:>6.2f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=CONSOLE,
    )


def _sample_images(spec: DatasetSpec) -> list[Path]:
    images = _iter_images(spec.raw_dir)
    if len(images) <= SAMPLE_IMAGES_PER_DATASET:
        return images

    seed_material = f"{SEED}:{spec.key}:prepare-sample".encode("utf-8")
    sample_seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:4], "big")
    shuffled = images.copy()
    random.Random(sample_seed).shuffle(shuffled)

    sampled: list[Path] = []
    with _make_progress() as progress:
        task = progress.add_task(f"Sampling {spec.display_name}", total=SAMPLE_IMAGES_PER_DATASET)
        for path in shuffled:
            try:
                with Image.open(path) as image:
                    image.verify()
            except (OSError, UnidentifiedImageError) as error:
                CONSOLE.print(f"Skipping unreadable image during sampling {path}: {error}")
                continue

            sampled.append(path)
            progress.advance(task)
            if len(sampled) == SAMPLE_IMAGES_PER_DATASET:
                break

    if len(sampled) < SAMPLE_IMAGES_PER_DATASET:
        raise RuntimeError(
            f"{spec.display_name} has only {len(sampled)} readable images; "
            f"{SAMPLE_IMAGES_PER_DATASET} are required"
        )

    return sorted(sampled)


def _write_prepared_dataset(spec: DatasetSpec, quality: int, images: list[Path]) -> tuple[int, int]:
    output_dir = PREPARED_ROOT / f"{spec.prepared_prefix}-q{quality}"
    _reset_output_dir(output_dir)
    label = f"{spec.prepared_prefix}-q{quality}"
    CONSOLE.print(
        f"Preparing {spec.display_name} q{quality}: {len(images)} sampled images -> {output_dir}",
    )

    written = 0
    skipped = 0
    with _make_progress() as progress:
        task = progress.add_task(label, total=len(images))
        for path in images:
            try:
                with Image.open(path) as image:
                    prepared = image.convert("L")
                    written += 1
                    prepared.save(output_dir / f"{written:05d}.jpg", quality=quality, optimize=True)
            except (OSError, UnidentifiedImageError) as error:
                skipped += 1
                CONSOLE.print(f"Skipping unreadable image {path}: {error}")
            finally:
                progress.advance(task)

    if written != len(images):
        raise RuntimeError(f"expected to prepare {len(images)} images for {label}, but wrote {written}")

    return written, skipped


def prepare() -> None:
    _ensure_raw_datasets()
    PREPARED_ROOT.mkdir(parents=True, exist_ok=True)

    for spec in DATASETS:
        images = _sample_images(spec)
        CONSOLE.print(
            f"Sampled {len(images)} images from {spec.display_name} "
            f"for qualities {', '.join(str(quality) for quality in ORIGINAL_QUALITIES)}",
        )
        for quality in ORIGINAL_QUALITIES:
            count, skipped = _write_prepared_dataset(spec, quality, images)
            output_dir = PREPARED_ROOT / f"{spec.prepared_prefix}-q{quality}"
            if skipped:
                CONSOLE.print(f"Prepared {count} images in {output_dir} ({skipped} skipped)")
            else:
                CONSOLE.print(f"Prepared {count} images in {output_dir}")
