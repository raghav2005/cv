#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_root="$repo_root/.build"

clean_build_directory() {
  if [[ "$build_root" != "$repo_root/.build" ]]; then
    echo "Refusing to clean an unexpected build path: $build_root" >&2
    exit 1
  fi
  rm -rf -- "$build_root"
}

if [[ "${1:-}" == "--clean" ]]; then
  if [[ "$#" -ne 1 ]]; then
    echo "Usage: $0 [--clean]" >&2
    exit 2
  fi
  clean_build_directory
  exit 0
fi

if [[ "$#" -ne 0 ]]; then
  echo "Usage: $0 [--clean]" >&2
  exit 2
fi

for required_command in pdflatex; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    echo "Missing required command: $required_command" >&2
    exit 1
  fi
done

tracks=(backend-systems security-software applied-ai-ml)
variants=(gmail me-com)

email_for_variant() {
  case "$1" in
    gmail) printf '%s' 'raghavawasthi2005@gmail.com' ;;
    me-com) printf '%s' 'raghavawasthi@me.com' ;;
    *)
      echo "Unknown email variant: $1" >&2
      exit 2
      ;;
  esac
}

build_variant() {
  local track="$1"
  local variant="$2"
  local email_address
  local output_directory
  local tex_command

  email_address="$(email_for_variant "$variant")"
  output_directory="$build_root/$track/$variant"
  tex_command="\\def\\ResumeEmail{$email_address}\\def\\ResumeTrack{$track}\\input{shared/resume.tex}"

  mkdir -p "$output_directory" "$repo_root/$track/$variant"

  for pass_number in 1 2; do
    (
      cd "$repo_root"
      SOURCE_DATE_EPOCH=315532800 FORCE_SOURCE_DATE=1 \
        pdflatex \
          -interaction=nonstopmode \
          -halt-on-error \
          -file-line-error \
          -jobname=Resume \
          -output-directory="$output_directory" \
          "$tex_command" >/dev/null
    )
  done

  if grep -Fq 'Overfull \hbox' "$output_directory/Resume.log" || \
     grep -Fq 'Overfull \vbox' "$output_directory/Resume.log"; then
    echo "Layout overflow detected for $track/$variant" >&2
    grep -F 'Overfull' "$output_directory/Resume.log" >&2
    exit 1
  fi

  install -m 0644 "$output_directory/Resume.pdf" "$repo_root/$track/$variant/Resume.pdf"
}

build_google_cover_letter() {
  local output_directory="$build_root/applications/google-early-career-swe/cover-letter"
  local source_file="applications/google-early-career-swe/Cover-Letter.tex"

  mkdir -p "$output_directory"

  for pass_number in 1 2; do
    (
      cd "$repo_root"
      SOURCE_DATE_EPOCH=315532800 FORCE_SOURCE_DATE=1 \
        pdflatex \
          -interaction=nonstopmode \
          -halt-on-error \
          -file-line-error \
          -jobname=Cover-Letter \
          -output-directory="$output_directory" \
          "$source_file" >/dev/null
    )
  done

  if grep -Fq 'Overfull \hbox' "$output_directory/Cover-Letter.log" || \
     grep -Fq 'Overfull \vbox' "$output_directory/Cover-Letter.log"; then
    echo "Layout overflow detected for the Google cover letter" >&2
    grep -F 'Overfull' "$output_directory/Cover-Letter.log" >&2
    exit 1
  fi

  install -m 0644 \
    "$output_directory/Cover-Letter.pdf" \
    "$repo_root/applications/google-early-career-swe/Cover-Letter.pdf"
}

clean_build_directory

for track in "${tracks[@]}"; do
  for variant in "${variants[@]}"; do
    echo "Building $track ($variant)"
    build_variant "$track" "$variant"
  done

  install -m 0644 "$repo_root/$track/me-com/Resume.pdf" "$repo_root/$track/Resume.pdf"
done

google_application_directory="$repo_root/applications/google-early-career-swe"
if [[ -f "$google_application_directory/content.tex" && \
      -f "$google_application_directory/Cover-Letter.tex" ]]; then
  echo "Building local Google Early Career SWE application"
  build_variant "applications/google-early-career-swe" "gmail"
  install -m 0644 \
    "$google_application_directory/gmail/Resume.pdf" \
    "$google_application_directory/Resume.pdf"
  build_google_cover_letter
else
  echo "Skipping local Google application documents (not present)."
fi

apple_application_directory="$repo_root/applications/apple-ist-early-career"
if [[ -f "$apple_application_directory/content.tex" ]]; then
  echo "Building local Apple IS&T Early Career application"
  build_variant "applications/apple-ist-early-career" "gmail"
  install -m 0644 \
    "$apple_application_directory/gmail/Resume.pdf" \
    "$apple_application_directory/Resume.pdf"
else
  echo "Skipping local Apple application resume (not present)."
fi

# Preserve the repository's historical root paths as aliases to the default
# backend/systems resume so old bookmarks continue to receive a current file.
install -m 0644 "$repo_root/backend-systems/Resume.pdf" "$repo_root/Resume.pdf"
install -m 0644 "$repo_root/backend-systems/Resume.pdf" "$repo_root/Resume-latest.pdf"

echo "Built all role-specific resumes and any local application documents."
