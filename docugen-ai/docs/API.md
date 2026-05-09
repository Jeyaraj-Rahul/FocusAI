# API Documentation

Base path: `/api/v1`

Authentication is implemented with password hashing and JWT bearer tokens.

## Planned Modules

- `auth`: registration, login, logout, current-user session lookup
- `reports`: report creation, editing, listing, deletion, generation
- `templates`: template upload and formatting-rule extraction
- `ai`: content polishing, grammar checking, chapter summaries, abstract generation, acknowledgement generation
- `exports`: DOCX/PDF download endpoints

## Auth Endpoints

### `POST /auth/register`

```json
{
  "full_name": "Student User",
  "email": "student@example.com",
  "password": "password123"
}
```

### `POST /auth/login`

```json
{
  "email": "student@example.com",
  "password": "password123"
}
```

Both endpoints return:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "full_name": "Student User",
    "email": "student@example.com",
    "is_active": true,
    "created_at": "2026-05-07T00:00:00"
  }
}
```

### `GET /auth/me`

Requires:

```text
Authorization: Bearer <access_token>
```

### `POST /auth/logout`

Requires a bearer token. Logout is stateless on the backend; the frontend clears the persisted token.

## AI Endpoints

All AI endpoints require:

```text
Authorization: Bearer <access_token>
```

### `POST /ai/polish-notes`

Converts rough notes into professional academic writing.

```json
{
  "rough_notes": "frontend used React and backend used FastAPI",
  "audience": "academic evaluator",
  "tone": "formal academic"
}
```

### `POST /ai/improve-grammar`

Improves grammar while preserving meaning.

```json
{
  "text": "The system are developed for generate reports fast."
}
```

### `POST /ai/chapter-summaries`

Generates one summary per chapter.

```json
{
  "summary_words": 120,
  "chapters": [
    {
      "title": "System Design",
      "content": "The system contains a React frontend, FastAPI backend, and PostgreSQL database."
    }
  ]
}
```

### `POST /ai/abstract`

Generates an academic abstract.

```json
{
  "title": "DocuGen AI",
  "project_notes": "DocuGen AI automates report formatting and document generation.",
  "word_count": 180
}
```

### `POST /ai/acknowledgements`

Generates a formal acknowledgement section.

```json
{
  "project_title": "DocuGen AI",
  "author_name": "Student User",
  "institution": "Engineering College",
  "mentors": ["Project Guide"],
  "tone": "sincere and formal"
}
```

## Template Endpoints

All template endpoints require a bearer token.

### `POST /templates/upload`

Multipart form upload:

```text
file=<template.docx>
```

The backend analyzes the DOCX with `python-docx` and saves a reusable formatting profile containing:

- font styles
- margins
- heading styles
- line spacing
- table styles
- generation-ready `formatting_options`

### `GET /templates`

Returns saved template profiles for the current user.

### `GET /templates/{template_id}`

Returns one saved formatting profile.

## Reusing a Template During DOCX Generation

Pass `template_id` to `POST /reports/generate-docx`.

```json
{
  "title": "Smart Attendance System",
  "template_id": 1,
  "sections": [
    {
      "heading": "Introduction",
      "paragraphs": ["This chapter introduces the system."]
    }
  ]
}
```

When `template_id` is present, the generator applies the saved profile's margins, font family, heading size, body size, and line spacing.

## Screenshot/Image Endpoints

All image endpoints require a bearer token.

### `POST /reports/images/upload`

Multipart form upload:

```text
file=<screenshot.png>
caption=Login screen
section_heading=Implementation
```

The backend:

- validates image type
- auto-resizes large screenshots
- maintains aspect ratio
- stores caption and target section heading
- returns image metadata and an `id`

Supported formats: PNG, JPG, JPEG, BMP, GIF.

### `GET /reports/images`

Returns uploaded images for the current user.

## Inserting Uploaded Images Into DOCX

Pass uploaded image IDs to `POST /reports/generate-docx`.

```json
{
  "title": "Smart Attendance System",
  "image_ids": [1, 2],
  "sections": [
    {
      "heading": "Implementation",
      "paragraphs": ["This section describes the implementation."]
    }
  ]
}
```

Images are inserted under the matching `section_heading`. If no matching section is found, the image is placed in the final report section. Captions are added below images automatically.

## PDF Export

### `POST /reports/generate-pdf`

Accepts the same payload as `POST /reports/generate-docx`, generates a DOCX internally, converts it to PDF, and streams the PDF download.

The converter attempts, in order:

1. LibreOffice/`soffice` headless conversion
2. `docx2pdf` when Microsoft Word automation is available
3. `pypandoc` when Pandoc and a PDF engine are available

LibreOffice or Word automation is recommended for best DOCX formatting preservation.

Temporary conversion directories and intermediate DOCX files are cleaned up after the response is sent.

FastAPI interactive documentation will be available at:

```text
http://localhost:8000/docs
```
