"""Independent all-page Poppler-to-WebP pixel audit; emits no source prose."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "content-private" / "total-money-makeover"
MANIFEST_PATH = PACKAGE / "source-manifest.json"
EXPECTED_PAGES = 229
EXPECTED_DIMENSIONS = (1530, 1980)
PPI = 180
FEATURE_SIZE = (96, 124)
MAX_NORMALIZED_MAE = 0.025
MAX_NORMALIZED_RMSE = 0.11
MIN_LUMA_CORRELATION = 0.85
MAX_FOREGROUND_RATIO_DELTA = 0.025
MIN_MAPPING_CORRELATION = 0.98
MIN_MAPPING_MARGIN = 0.001
DEFAULT_PDFTOCAIRO = Path(
    os.environ.get(
        "PDFTOCAIRO",
        r"C:\Users\dougl\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin\pdftocairo.exe",
    )
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def webp_round_trip(image: Image.Image) -> Image.Image:
    output = io.BytesIO()
    image.convert("RGB").save(output, format="WEBP", quality=82, method=6, exif=b"", icc_profile=None)
    output.seek(0)
    decoded = Image.open(output).convert("RGB")
    decoded.load()
    return decoded


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    left_centered = left.astype(np.float64, copy=False).ravel() - float(left.mean())
    right_centered = right.astype(np.float64, copy=False).ravel() - float(right.mean())
    denominator = float(np.linalg.norm(left_centered) * np.linalg.norm(right_centered))
    if denominator == 0:
        return 1.0 if np.array_equal(left, right) else 0.0
    return float(np.dot(left_centered, right_centered) / denominator)


def page_similarity(reference: Image.Image, candidate: Image.Image) -> dict:
    reference_rgb = np.asarray(reference.convert("RGB"), dtype=np.float32)
    candidate_rgb = np.asarray(candidate.convert("RGB"), dtype=np.float32)
    dimensions_match = reference_rgb.shape == candidate_rgb.shape
    if not dimensions_match:
        return {
            "dimensionsMatch": False,
            "normalizedMeanAbsoluteError": 1.0,
            "normalizedRootMeanSquareError": 1.0,
            "lumaCorrelation": 0.0,
            "foregroundRatioDelta": 1.0,
        }
    delta = reference_rgb - candidate_rgb
    reference_luma = (
        reference_rgb[..., 0] * 0.2126
        + reference_rgb[..., 1] * 0.7152
        + reference_rgb[..., 2] * 0.0722
    )
    candidate_luma = (
        candidate_rgb[..., 0] * 0.2126
        + candidate_rgb[..., 1] * 0.7152
        + candidate_rgb[..., 2] * 0.0722
    )
    return {
        "dimensionsMatch": True,
        "normalizedMeanAbsoluteError": round(float(np.mean(np.abs(delta)) / 255.0), 6),
        "normalizedRootMeanSquareError": round(float(np.sqrt(np.mean(delta * delta)) / 255.0), 6),
        "lumaCorrelation": round(_correlation(reference_luma, candidate_luma), 6),
        "foregroundRatioDelta": round(
            float(abs(np.mean(reference_luma < 245) - np.mean(candidate_luma < 245))),
            6,
        ),
    }


def similarity_passes(metrics: dict) -> bool:
    return bool(
        metrics["dimensionsMatch"]
        and metrics["normalizedMeanAbsoluteError"] <= MAX_NORMALIZED_MAE
        and metrics["normalizedRootMeanSquareError"] <= MAX_NORMALIZED_RMSE
        and metrics["lumaCorrelation"] >= MIN_LUMA_CORRELATION
        and metrics["foregroundRatioDelta"] <= MAX_FOREGROUND_RATIO_DELTA
    )


def feature_vector(image: Image.Image) -> np.ndarray:
    values = np.asarray(
        image.convert("L").resize(FEATURE_SIZE, Image.Resampling.BILINEAR),
        dtype=np.float64,
    ).ravel()
    centered = values - float(values.mean())
    norm = float(np.linalg.norm(centered))
    return centered / norm if norm else centered


def mapping_discriminators(reference_features: list[np.ndarray], asset_features: list[np.ndarray]) -> list[dict]:
    if not reference_features or len(reference_features) != len(asset_features):
        return []
    scores = np.stack(reference_features) @ np.stack(asset_features).T
    results = []
    count = len(reference_features)
    for index in range(count):
        correct = float(scores[index, index])
        wrong_scores = scores[index].copy()
        wrong_scores[index] = -np.inf
        best_wrong_index = int(np.argmax(wrong_scores)) if count > 1 else index
        best_wrong = float(wrong_scores[best_wrong_index]) if count > 1 else -1.0
        best_candidate = int(np.argmax(scores[index]))
        neighbor_indices = [candidate for candidate in (index - 1, index + 1) if 0 <= candidate < count]
        neighbor_scores = [float(scores[index, candidate]) for candidate in neighbor_indices]
        best_neighbor_position = int(np.argmax(neighbor_scores)) if neighbor_scores else 0
        best_neighbor = neighbor_scores[best_neighbor_position] if neighbor_scores else -1.0
        best_neighbor_index = neighbor_indices[best_neighbor_position] if neighbor_indices else None
        margin = correct - best_wrong
        neighbor_margin = correct - best_neighbor
        passed = (
            correct >= MIN_MAPPING_CORRELATION
            and best_candidate == index
            and margin >= MIN_MAPPING_MARGIN
            and neighbor_margin >= MIN_MAPPING_MARGIN
        )
        results.append(
            {
                "correctPageCorrelation": round(correct, 6),
                "bestCandidatePage": best_candidate + 1,
                "bestWrongPage": best_wrong_index + 1,
                "bestWrongPageCorrelation": round(best_wrong, 6),
                "wrongPageMargin": round(margin, 6),
                "bestNeighborPage": best_neighbor_index + 1 if best_neighbor_index is not None else None,
                "bestNeighborCorrelation": round(best_neighbor, 6),
                "neighborMargin": round(neighbor_margin, 6),
                "pass": passed,
            }
        )
    return results


def _poppler_version(executable: Path) -> str:
    result = subprocess.run([str(executable), "-v"], capture_output=True, text=True, check=True)
    first_line = (result.stdout + result.stderr).splitlines()[0]
    return first_line.removeprefix("pdftocairo version ").strip()


def _render_reference_pages(executable: Path, source: Path, output_dir: Path) -> list[Path]:
    prefix = output_dir / "source"
    subprocess.run(
        [
            str(executable),
            "-f",
            "1",
            "-l",
            str(EXPECTED_PAGES),
            "-r",
            str(PPI),
            "-png",
            "-q",
            str(source),
            str(prefix),
        ],
        check=True,
    )
    pages = sorted(output_dir.glob("source-*.png"))
    if len(pages) != EXPECTED_PAGES:
        raise ValueError(f"Poppler rendered {len(pages)} pages; expected {EXPECTED_PAGES}")
    return pages


def _validated_cleanup(path: Path) -> None:
    resolved = path.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if resolved.parent != temp_root or not resolved.name.startswith("boundaries-reader-pixel-audit-"):
        raise RuntimeError(f"refusing cleanup outside exact pixel-audit temporary directory: {resolved}")
    shutil.rmtree(resolved)


def run_audit(pdftocairo: Path) -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    source = Path(manifest["source"]["path"])
    source_identity_verified = (
        source.is_file()
        and source.stat().st_size == manifest["source"]["bytes"]
        and sha256_file(source) == manifest["source"]["sha256"]
    )
    assets = manifest.get("assets", [])
    expected_pages = list(range(1, EXPECTED_PAGES + 1))
    manifest_bijection = (
        [asset.get("page") for asset in assets] == expected_pages
        and [asset.get("path") for asset in assets]
        == [f"pages/page-{page:03d}.webp" for page in expected_pages]
    )
    temp_dir = Path(tempfile.mkdtemp(prefix="boundaries-reader-pixel-audit-"))
    page_results = []
    reference_features = []
    asset_features = []
    decoded_hashes = set()
    try:
        rendered_pages = _render_reference_pages(pdftocairo, source, temp_dir)
        for page_number, reference_path in enumerate(rendered_pages, 1):
            asset_record = assets[page_number - 1] if page_number <= len(assets) else {}
            asset_path = PACKAGE / str(asset_record.get("path", "missing"))
            with Image.open(reference_path) as reference_image, Image.open(asset_path) as asset_image:
                reference_image.load()
                asset_image.load()
                reference_rgb = reference_image.convert("RGB")
                asset_rgb = asset_image.convert("RGB")
                metrics = page_similarity(reference_rgb, asset_rgb)
                reference_features.append(feature_vector(reference_rgb))
                asset_features.append(feature_vector(asset_rgb))
                decoded_hashes.add(hashlib.sha256(asset_rgb.tobytes()).digest())
                page_results.append(
                    {
                        "page": page_number,
                        "referenceWidth": reference_rgb.width,
                        "referenceHeight": reference_rgb.height,
                        "assetWidth": asset_rgb.width,
                        "assetHeight": asset_rgb.height,
                        **metrics,
                        "similarityPass": similarity_passes(metrics),
                    }
                )
        mappings = mapping_discriminators(reference_features, asset_features)
        for page, mapping in zip(page_results, mappings):
            page.update(mapping)
            page["pass"] = bool(page.pop("pass") and page["similarityPass"])
    finally:
        _validated_cleanup(temp_dir)

    unique_decoded_assets = len(decoded_hashes)
    passed_pages = sum(1 for page in page_results if page["pass"])
    result = {
        "audit": "independent-poppler-pixel-comparison",
        "pass": bool(
            source_identity_verified
            and manifest_bijection
            and len(page_results) == EXPECTED_PAGES
            and passed_pages == EXPECTED_PAGES
            and unique_decoded_assets == EXPECTED_PAGES
        ),
        "tools": {
            "pdftocairo": _poppler_version(pdftocairo),
            "python": platform.python_version(),
            "Pillow": Image.__version__,
            "numpy": np.__version__,
        },
        "render": {"ppi": PPI, "format": "PNG", "expectedWidth": 1530, "expectedHeight": 1980},
        "tolerances": {
            "normalizedMeanAbsoluteErrorMax": MAX_NORMALIZED_MAE,
            "normalizedRootMeanSquareErrorMax": MAX_NORMALIZED_RMSE,
            "lumaCorrelationMin": MIN_LUMA_CORRELATION,
            "foregroundRatioDeltaMax": MAX_FOREGROUND_RATIO_DELTA,
            "downsampledMappingCorrelationMin": MIN_MAPPING_CORRELATION,
            "wrongPageAndNeighborMarginMin": MIN_MAPPING_MARGIN,
            "rationale": "Bounds admit quality-82 WebP and independent renderer antialiasing while rejecting the synthetic blank, shifted, duplicated, and wrong-page controls.",
        },
        "aggregate": {
            "sourceIdentityVerified": source_identity_verified,
            "manifestPageAssetBijection": manifest_bijection,
            "pagesCompared": len(page_results),
            "pagesPassed": passed_pages,
            "uniqueDecodedAssets": unique_decoded_assets,
            "dimensionMatches": sum(1 for page in page_results if page["dimensionsMatch"]),
            "maxNormalizedMeanAbsoluteError": max(page["normalizedMeanAbsoluteError"] for page in page_results),
            "maxNormalizedRootMeanSquareError": max(page["normalizedRootMeanSquareError"] for page in page_results),
            "minLumaCorrelation": min(page["lumaCorrelation"] for page in page_results),
            "maxForegroundRatioDelta": max(page["foregroundRatioDelta"] for page in page_results),
            "minCorrectPageCorrelation": min(page["correctPageCorrelation"] for page in page_results),
            "minWrongPageMargin": min(page["wrongPageMargin"] for page in page_results),
            "minNeighborMargin": min(page["neighborMargin"] for page in page_results),
            "mappingTopChoiceMatches": sum(1 for page in page_results if page["bestCandidatePage"] == page["page"]),
        },
        "pages": page_results,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--compare", type=Path)
    parser.add_argument("--pdftocairo", type=Path, default=DEFAULT_PDFTOCAIRO)
    args = parser.parse_args(argv)
    result = run_audit(args.pdftocairo.resolve())
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        recorded = json.loads(args.compare.read_text(encoding="utf-8"))
        if recorded != result:
            raise SystemExit("Independent pixel audit differs from its materialized evidence")
    print(
        "PIXEL_AUDIT="
        f"{'PASS' if result['pass'] else 'FAIL'} "
        f"pages={result['aggregate']['pagesPassed']}/{EXPECTED_PAGES} "
        f"maxMae={result['aggregate']['maxNormalizedMeanAbsoluteError']:.6f} "
        f"minCorr={result['aggregate']['minLumaCorrelation']:.6f} "
        f"minMapMargin={result['aggregate']['minWrongPageMargin']:.6f}"
    )
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
