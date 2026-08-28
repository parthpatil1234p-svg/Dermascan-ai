# DermaScan AI Privacy Notice

Last updated: 8 August 2026

DermaScan AI is a college mini-project for general skincare guidance. It is not a
medical record system or diagnostic service.

## Data Collected

- Account data: full name, normalized email, optional age group and location,
  password hash, account status, and timestamps.
- Self-reported skin profile: skin behavior, sensitivity selection, known
  allergies, current products, budget, brands, avoided ingredients, fragrance
  preference, experience level, country, and optional notes.
- Temporary image data: one consented facial image plus temporary face crop and
  preprocessed derivative.
- Technical reports: quality, face-detection, preprocessing, model output,
  visible-observation, eligibility, recommendation, and routine records.
- Final reports: versioned guidance snapshots without facial-image bytes.
- Optional feedback: ratings, reason codes, optional comments, consent choices,
  moderation state, and private product-avoidance preferences.

Passwords are hashed with pwdlib's maintained Argon2-based recommended method.
Plain-text passwords are not stored. JWTs contain only `sub`, `iat`, and `exp`.

## Purpose

Data is used to authenticate the user, enforce workflow ownership, apply the
user's stated restrictions, create general skincare guidance, preserve report
history, and process optional feedback according to its separate consent flags.
Facial images are not used for training or research consent in this project.

## Storage And Retention

- Raw sanitized uploads, derived crops, preprocessed files, and generated PDF
  files expire after 30 minutes by default. Operators can tune these limits.
- Cleanup runs at backend startup and through
  `python -m app.scripts.cleanup_expired_data`; external scheduling is required
  for continuous cleanup.
- Account, profile, analysis metadata, and report snapshots remain in MongoDB
  for project use. A report archive action hides the report but is not erasure.
- Withdrawing feedback disables its analytics, research, improvement, catalogue,
  and product-avoidance effects. The withdrawn record remains for audit history.

## Browser Storage

The access token is stored in browser `localStorage` for session restoration.
This is simple for a college project but is exposed if malicious JavaScript runs
in the origin. A production system should prefer short-lived access tokens held
in memory plus Secure, HttpOnly, SameSite refresh cookies with CSRF protection.
Only the public active upload ID is kept in `sessionStorage` for refresh
continuity. Passwords, facial images, allergies, and full reports are not stored
in browser storage.

## Consent And User Controls

- Image-processing consent is explicit, separate, and not preselected.
- Feedback analytics and research-review consent are separate and optional.
- Users can update or delete their skin profile, delete their temporary upload,
  archive final reports, withdraw feedback, and remove product avoidance.
- Ownership checks use the JWT-authenticated user ID; client-supplied user IDs
  are not trusted.

## Sharing And Logging

The project has no public report-sharing URL and no third-party analytics SDK.
Operational logs exclude passwords, tokens, raw image bytes, allergy lists,
full questionnaire values, comments, and physical client-visible paths.

## Limitations

This repository does not implement account erasure, downloadable data export,
server-side JWT revocation, encrypted application-level fields, managed key
rotation, or a formal data-processing agreement. Deployment operators are
responsible for HTTPS, database access controls, encrypted backups, retention
policy, and applicable law.

