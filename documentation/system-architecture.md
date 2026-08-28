# System Architecture

## Component View

```mermaid
flowchart TD
    Browser["React + Vite browser application"] -->|"HTTPS JSON / multipart + Bearer JWT"| API["FastAPI REST API"]
    API --> Auth["Authentication and ownership dependencies"]
    API --> Workflow["Workflow and report services"]
    Workflow --> Vision["OpenCV, Pillow, MediaPipe"]
    Workflow --> Models["Optional exported Keras models"]
    Workflow --> Rules["Eligibility, scoring, routine rules"]
    Auth --> Mongo[("MongoDB")]
    Workflow --> Mongo
    Workflow --> Storage["Private temporary storage"]
    API --> Logs["Structured operational logs"]
```

The browser never receives physical storage paths. MongoDB owns workflow
metadata; private local storage owns temporary image and PDF bytes. Model
registries load each configured model once per API worker.

## Workflow

```mermaid
flowchart LR
    A["Account"] --> P["Complete profile"] --> U["Consented upload"]
    U --> Q["Quality report"] --> F["One usable face"] --> X["Preprocessing"]
    X --> S["Skin-type estimate"] --> C["Visible observations"]
    C --> E["Eligibility filters"] --> R["Ranked products"]
    R --> T["Morning/night routine"] --> Z["Versioned final report"]
    Z --> PDF["Temporary PDF"]
    Z --> FB["Optional feedback"]
```

Backend services enforce every transition by owner ID, upload status, parent
report ID, completion state, consent, and expiry. React guards improve the user
experience but are not the authorization boundary.

## Data Flow And Trust Boundaries

```mermaid
flowchart TD
    Input["Untrusted browser input"] --> Validate["Pydantic and file validation"]
    Validate --> Owner["JWT-derived owner"]
    Owner --> Services["Domain services"]
    Services --> DB[("Private database")]
    Services --> Temp["Confined temporary roots"]
    Temp --> Cleanup["Startup or scheduled cleanup"]
    Services --> Public["Response schemas without paths, hashes, or image bytes"]
```

- Browser input, filenames, MIME headers, identifiers, and query values are
  untrusted.
- The JWT `sub` selects ownership; request bodies cannot choose a user ID.
- File paths are generated and resolved beneath configured roots.
- Admin catalogue and feedback-review operations require `is_admin`.
- Public catalogue reads expose only active catalogue records.

## Report Relationships

One upload can have one quality, face-detection, preprocessing, skin-type,
visible-concern, eligibility, recommendation, and routine report. A final report
can have multiple versions, each referencing a fingerprint of its immutable
source versions. Feedback can reference a final report or product but remains
owned by its submitting user.

## Storage Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Uploaded
    Uploaded --> Crop
    Crop --> Preprocessed
    Uploaded --> Expired: configured TTL
    Crop --> Expired: configured TTL
    Preprocessed --> Expired: configured TTL
    Expired --> Deleted: cleanup command
```

Metadata reports can remain after temporary bytes expire. Final reports never
embed facial images. PDF exports are regenerated and expire independently.

## Security Boundaries

The production boundary requires HTTPS, restricted CORS, private MongoDB,
managed secrets, writable private temporary storage, and a reverse proxy. The
included process-local limiter is suitable for a single college deployment, not
a distributed abuse-prevention system.

