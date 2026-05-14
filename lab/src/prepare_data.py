"""Prepare raw BOSSbase and UCID images for the experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import tarfile
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlretrieve
import zipfile

from PIL import Image


LAB_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = LAB_ROOT / "data"
RAW_ROOT = DATA_ROOT / "raw"
PREPARED_ROOT = DATA_ROOT / "prepared"
DOWNLOAD_ROOT = RAW_ROOT / "downloads"
IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".pgm", ".tif", ".tiff"}
ORIGINAL_QUALITIES = (100, 95)


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    display_name: str
    raw_dir: Path
    prepared_prefix: str
    urls: tuple[str, ...]
    manual_url: str


DATASETS = (
    DatasetSpec(
        key="bossbase",
        display_name="BOSSbase-1.01",
        raw_dir=RAW_ROOT / "BOSSbase-1.01",
        prepared_prefix="bossbase",
        urls=("https://dde.binghamton.edu/download/ImageDB/BOSSbase_1.01.zip",),
        manual_url="https://dde.binghamton.edu/download/",
    ),
    DatasetSpec(
        key="ucid",
        display_name="UCID",
        raw_dir=RAW_ROOT / "UCID",
        prepared_prefix="ucid",
        urls=("http://jasoncantarella.com/downloads/ucid.v2.tar.gz",),
        manual_url="https://qualinet.github.io/databases/image/uncompressed_colour_image_database_ucid/",
    ),
)


def _iter_images(path: Path) -> list[Path]:
    return sorted(item for item in path.rglob("*") if item.suffix.lower() in IMAGE_SUFFIXES)


def _has_images(path: Path) -> bool:
    return path.exists() and any(_iter_images(path))


def _missing_datasets() -> list[DatasetSpec]:
    return [spec for spec in DATASETS if not _has_images(spec.raw_dir)]


def _archive_name(url: str) -> str:
    name = Path(urlparse(url).path).name
    if not name:
        raise ValueError(f"cannot infer archive name from {url}")
    return name


def _extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as file:
            file.extractall(destination)
    elif archive.name.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive, "r:gz") as file:
            file.extractall(destination)
    else:
        raise ValueError(f"unsupported archive format: {archive}")


def _best_image_root(path: Path) -> Path:
    candidates = [item for item in path.rglob("*") if item.is_dir()]
    candidates.append(path)
    return max(candidates, key=lambda item: len(_iter_images(item)))


def _install_extracted_dataset(extract_dir: Path, raw_dir: Path) -> None:
    image_root = _best_image_root(extract_dir)
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(image_root), str(raw_dir))


def _download_dataset(spec: DatasetSpec) -> bool:
    DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    for url in spec.urls:
        archive = DOWNLOAD_ROOT / _archive_name(url)
        extract_dir = DOWNLOAD_ROOT / f"{spec.key}-extract"
        try:
            print(f"Downloading {spec.display_name} from {url}")
            urlretrieve(url, archive)
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            _extract_archive(archive, extract_dir)
            _install_extracted_dataset(extract_dir, spec.raw_dir)
        except (OSError, URLError, ValueError, zipfile.BadZipFile, tarfile.TarError) as exc:
            print(f"Failed to download {spec.display_name}: {exc}")
            continue

        if _has_images(spec.raw_dir):
            return True
        print(f"Downloaded archive for {spec.display_name}, but no images were found.")
    return False


def _print_manual_instructions(missing: list[DatasetSpec]) -> None:
    print("Please download the missing datasets manually and place them here:")
    for spec in missing:
        print(f"- {spec.display_name}: {spec.raw_dir}")
        print(f"  Source: {spec.manual_url}")


def _ensure_raw_datasets() -> None:
    missing = _missing_datasets()
    if not missing:
        return

    print("Missing raw datasets:")
    for spec in missing:
        print(f"- {spec.display_name}")

    try:
        answer = input("Download missing datasets automatically? [y/N]: ").strip().lower()
    except EOFError:
        answer = ""

    if answer not in {"y", "yes"}:
        _print_manual_instructions(missing)
        raise SystemExit(1)

    failed: list[DatasetSpec] = []
    for spec in missing:
        if not _download_dataset(spec):
            failed.append(spec)

    if failed:
        _print_manual_instructions(failed)
        raise SystemExit(1)


def _reset_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for image in _iter_images(path):
        image.unlink()


def _write_prepared_dataset(spec: DatasetSpec, quality: int) -> int:
    output_dir = PREPARED_ROOT / f"{spec.prepared_prefix}-q{quality}"
    _reset_output_dir(output_dir)
    images = _iter_images(spec.raw_dir)
    for index, path in enumerate(images, start=1):
        with Image.open(path) as image:
            prepared = image.convert("L")
            prepared.save(output_dir / f"{index:05d}.jpg", quality=quality, optimize=True)
    return len(images)


def prepare() -> None:
    _ensure_raw_datasets()
    PREPARED_ROOT.mkdir(parents=True, exist_ok=True)

    for spec in DATASETS:
        for quality in ORIGINAL_QUALITIES:
            count = _write_prepared_dataset(spec, quality)
            output_dir = PREPARED_ROOT / f"{spec.prepared_prefix}-q{quality}"
            print(f"Prepared {count} images in {output_dir}")

