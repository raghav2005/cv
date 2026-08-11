# Role-specific resumes

This repository contains three one-page, single-column resumes tailored to related role families:

- `backend-systems/` - backend, platform, infrastructure, distributed systems, storage, database and edge roles.
- `security-software/` - security software engineering, PKI, certificate infrastructure, post-quantum cryptography, application security and AI security roles.
- `applied-ai-ml/` - applied AI, LLM, RAG, inference, model serving and ML engineering roles.

Each role folder contains:

- `Resume.pdf` - the canonical version, currently using `raghavawasthi@me.com`.
- `gmail/Resume.pdf` - the Gmail variant.
- `me-com/Resume.pdf` - the `@me.com` variant.
- `content.tex` - role-specific experience, project and skill content.

The two email variants are generated from the same source. The visible email and its `mailto:` target are the only intended content differences. The root `Resume.pdf` and `Resume-latest.pdf` mirror the canonical backend/systems resume for backwards compatibility.

## Application-specific documents

Application-specific résumés and cover letters belong under `applications/`. This
directory is deliberately ignored by Git so tailored application materials stay
local and are never committed, uploaded as GitHub Actions artifacts or published
in the repository. When the directory exists locally, `make all` still builds and
validates the supported application documents.

## Build and validate

Requirements: a current TeX Live installation with pdfLaTeX, plus Poppler (`pdfinfo`, `pdftotext`, `pdffonts` and `pdftoppm`).

```sh
make all
```

Useful targets:

```sh
make resumes   # Build all role and email variants
make validate  # Check page count, extraction, fonts, links and variant consistency
make clean     # Remove only the repository's .build directory
```

The GitHub Actions workflow rebuilds and validates every reusable role résumé on
pull requests. On pushes to `main`, it also commits updated reusable PDFs when the
source changed and uploads only those reusable PDFs as a workflow artifact.

## Editing guidance

- Keep every claim evidence-based. Do not invent metrics to force an XYZ-style bullet.
- Prefer the pattern: outcome and scale, followed by the method used to achieve it.
- Keep standard headings, a single column, selectable text and plain-text contact details.
- Run `make all` and visually inspect all three canonical PDFs after meaningful content changes.

No resume can guarantee an ATS pass or an interview. The build checks remove common parsing failures and keep each version targeted, consistent and reproducible.
