#!/usr/bin/env python3
"""Validate generated resumes for ATS readability and variant consistency."""

from __future__ import annotations

import filecmp
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
TRACKS = ("backend-systems", "security-software", "applied-ai-ml")
EMAILS = {
    "gmail": "raghavawasthi2005@gmail.com",
    "me-com": "raghavawasthi@me.com",
}
REQUIRED_TEXT = (
    "Raghav Awasthi",
    "+44 7448 420483",
    "linkedin.com/in/raghavawasthi2005",
    "github.com/raghav2005",
    "Education",
    "Experience",
    "Projects",
    "Technical Skills",
)
TRACK_MARKERS = {
    "backend-systems": ("Walrus-Cache-CDN", "4.2x", "RocksDB"),
    "security-software": ("CWE-288", "PQC/HSM", "ML-KEM"),
    "applied-ai-ml": ("LoRA", "MiniLM", "hallucination rate"),
    "applications/google-early-career-swe": (
        "Data structures and algorithms",
        "AI coding tools",
        "Assembly Code Visualiser",
    ),
    "applications/apple-ist-early-career": (
        "Data structures and algorithms",
        "140M+ rows",
        "Prometheus",
    ),
}


def run(*args: str) -> str:
    completed = subprocess.run(
        args,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout


def normalized_text(text: str) -> str:
    for email in EMAILS.values():
        text = text.replace(email, "<EMAIL>")
    return re.sub(r"\s+", " ", text).strip()


def validate_fonts(pdf_path: Path) -> list[str]:
    errors: list[str] = []
    lines = run("pdffonts", str(pdf_path)).splitlines()[2:]
    if not lines:
        return [f"{pdf_path}: no fonts found"]

    for line in lines:
        columns = line.split()
        if len(columns) < 8:
            errors.append(f"{pdf_path}: could not parse font row: {line}")
            continue
        # Read the stable columns from the right because the font type can be
        # either one token (TrueType) or two tokens (Type 1).
        if columns[-5] != "yes":
            errors.append(f"{pdf_path}: font is not embedded: {columns[0]}")
        if columns[-3] != "yes":
            errors.append(f"{pdf_path}: font lacks a Unicode map: {columns[0]}")
    return errors


def validate_pdf(pdf_path: Path, expected_email: str, track: str) -> tuple[list[str], str]:
    errors: list[str] = []
    if not pdf_path.is_file():
        return [f"Missing PDF: {pdf_path}"], ""

    info = run("pdfinfo", str(pdf_path))
    expected_info = {
        "Pages": "1",
        "Encrypted": "no",
        "Form": "none",
        "JavaScript": "no",
    }
    for field, expected_value in expected_info.items():
        match = re.search(rf"^{re.escape(field)}:\s*(.+)$", info, re.MULTILINE)
        actual = match.group(1).strip() if match else "<missing>"
        if actual != expected_value:
            errors.append(f"{pdf_path}: {field} is {actual!r}, expected {expected_value!r}")

    size_match = re.search(r"^Page size:\s+([\d.]+) x ([\d.]+) pts", info, re.MULTILINE)
    if not size_match or tuple(map(float, size_match.groups())) != (612.0, 792.0):
        errors.append(f"{pdf_path}: expected US Letter page size")

    text = run("pdftotext", "-layout", str(pdf_path), "-")
    if len(text.strip()) < 2_500:
        errors.append(f"{pdf_path}: extracted text is unexpectedly short")
    if "\ufffd" in text:
        errors.append(f"{pdf_path}: extracted text contains replacement characters")

    for required in REQUIRED_TEXT + TRACK_MARKERS[track] + (expected_email,):
        if required not in text:
            errors.append(f"{pdf_path}: missing extractable text {required!r}")

    for other_email in set(EMAILS.values()) - {expected_email}:
        if other_email in text:
            errors.append(f"{pdf_path}: contains the wrong visible email {other_email!r}")

    url_output = run("pdfinfo", "-url", str(pdf_path))
    mailto_urls = re.findall(r"mailto:[^\s]+", url_output)
    if mailto_urls.count(f"mailto:{expected_email}") != 1:
        errors.append(f"{pdf_path}: expected exactly one mailto link for {expected_email}")
    for other_email in set(EMAILS.values()) - {expected_email}:
        if f"mailto:{other_email}" in url_output:
            errors.append(f"{pdf_path}: contains the wrong mailto target {other_email!r}")
    for required_url in (
        "https://www.linkedin.com/in/raghavawasthi2005",
        "https://github.com/raghav2005",
    ):
        if required_url not in url_output:
            errors.append(f"{pdf_path}: missing URL annotation {required_url}")

    errors.extend(validate_fonts(pdf_path))
    return errors, text


def validate_cover_letter(pdf_path: Path) -> list[str]:
    errors: list[str] = []
    if not pdf_path.is_file():
        return [f"Missing PDF: {pdf_path}"]

    info = run("pdfinfo", str(pdf_path))
    expected_info = {
        "Pages": "1",
        "Encrypted": "no",
        "Form": "none",
        "JavaScript": "no",
    }
    for field, expected_value in expected_info.items():
        match = re.search(rf"^{re.escape(field)}:\s*(.+)$", info, re.MULTILINE)
        actual = match.group(1).strip() if match else "<missing>"
        if actual != expected_value:
            errors.append(f"{pdf_path}: {field} is {actual!r}, expected {expected_value!r}")

    text = run("pdftotext", "-layout", str(pdf_path), "-")
    for required in (
        "Raghav Awasthi",
        "raghavawasthi2005@gmail.com",
        "Google Hiring Team",
        "Software Engineer, Early Career, Campus",
        "linear elastic caching",
        "Spanner",
        "81.7%",
        "4.2x",
    ):
        if required not in text:
            errors.append(f"{pdf_path}: missing extractable text {required!r}")
    if "raghavawasthi@me.com" in text:
        errors.append(f"{pdf_path}: contains the wrong visible email")
    if "\ufffd" in text:
        errors.append(f"{pdf_path}: extracted text contains replacement characters")

    url_output = run("pdfinfo", "-url", str(pdf_path))
    if url_output.count("mailto:raghavawasthi2005@gmail.com") != 1:
        errors.append(f"{pdf_path}: expected exactly one Gmail mailto link")
    if "mailto:raghavawasthi@me.com" in url_output:
        errors.append(f"{pdf_path}: contains the wrong mailto target")

    errors.extend(validate_fonts(pdf_path))
    return errors


def main() -> int:
    missing_commands = [
        command
        for command in ("pdfinfo", "pdftotext", "pdffonts")
        if shutil.which(command) is None
    ]
    if missing_commands:
        print(f"Missing required commands: {', '.join(missing_commands)}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for track in TRACKS:
        texts: dict[str, str] = {}
        for variant, expected_email in EMAILS.items():
            pdf_path = REPO_ROOT / track / variant / "Resume.pdf"
            pdf_errors, extracted_text = validate_pdf(pdf_path, expected_email, track)
            errors.extend(pdf_errors)
            texts[variant] = extracted_text

        if all(texts.values()) and normalized_text(texts["gmail"]) != normalized_text(texts["me-com"]):
            errors.append(f"{track}: email variants differ beyond the email address")

        canonical = REPO_ROOT / track / "Resume.pdf"
        default_variant = REPO_ROOT / track / "me-com" / "Resume.pdf"
        if not canonical.is_file() or not filecmp.cmp(canonical, default_variant, shallow=False):
            errors.append(f"{track}: canonical Resume.pdf is not identical to me-com/Resume.pdf")

    backend_default = REPO_ROOT / "backend-systems" / "Resume.pdf"
    for root_alias in (REPO_ROOT / "Resume.pdf", REPO_ROOT / "Resume-latest.pdf"):
        if not root_alias.is_file() or not filecmp.cmp(root_alias, backend_default, shallow=False):
            errors.append(f"{root_alias}: root alias is not identical to backend-systems/Resume.pdf")

    google_track = "applications/google-early-career-swe"
    google_directory = REPO_ROOT / google_track
    validated_google_application = False
    if (google_directory / "content.tex").is_file() and (
        google_directory / "Cover-Letter.tex"
    ).is_file():
        validated_google_application = True
        google_gmail = google_directory / "gmail" / "Resume.pdf"
        google_errors, _ = validate_pdf(
            google_gmail, EMAILS["gmail"], google_track
        )
        errors.extend(google_errors)
        google_canonical = google_directory / "Resume.pdf"
        if not google_canonical.is_file() or not filecmp.cmp(
            google_canonical, google_gmail, shallow=False
        ):
            errors.append(
                f"{google_track}: canonical Resume.pdf is not identical to gmail/Resume.pdf"
            )

        errors.extend(validate_cover_letter(google_directory / "Cover-Letter.pdf"))

    apple_track = "applications/apple-ist-early-career"
    apple_directory = REPO_ROOT / apple_track
    validated_apple_application = False
    if (apple_directory / "content.tex").is_file():
        validated_apple_application = True
        apple_gmail = apple_directory / "gmail" / "Resume.pdf"
        apple_errors, _ = validate_pdf(
            apple_gmail, EMAILS["gmail"], apple_track
        )
        errors.extend(apple_errors)
        apple_canonical = apple_directory / "Resume.pdf"
        if not apple_canonical.is_file() or not filecmp.cmp(
            apple_canonical, apple_gmail, shallow=False
        ):
            errors.append(
                f"{apple_track}: canonical Resume.pdf is not identical to gmail/Resume.pdf"
            )

    if errors:
        print("Resume validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    summary = "Validated 6 role variants, 3 canonical role resumes and 2 root aliases"
    if validated_google_application:
        summary += ", plus the local Google application resume and cover letter"
    if validated_apple_application:
        summary += ", plus the local Apple application resume"
    print(f"{summary}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
