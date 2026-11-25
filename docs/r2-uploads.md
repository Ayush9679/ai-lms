# Private Cloudflare R2 uploads

## Current flows

The Next.js client uses the FastAPI direct-upload flow: `POST /api/v1/uploads/presign`, a browser PUT to the returned URL(s), then `POST /api/v1/uploads/complete`. Only an authenticated teacher who owns the lesson can start or finalize its upload. The backend verifies object length, declared MIME metadata, and a bounded file signature before saving its `r2://` object key; lesson video state becomes `ready` only after that verification and the database commit. The bucket stays private and reads use short-lived signed GET URLs.

Lesson videos are MP4 only; lesson PDFs are PDF only. Both have a 2048 MB server-side size limit. Files up to 64 MiB use a single presigned PUT; larger files use 64 MiB multipart chunks with up to two retries per chunk, cancellation/abort, ETag collection and multipart completion. The single PUT signs `Content-Type` and `host` only. Content length is validated after upload from R2 metadata and is not included in the signature. Multipart upload-part requests need no signed content-type header.

The backend uses Botocore's `request_checksum_calculation="when_required"` and `response_checksum_validation="when_required"` settings. The project pins boto3 1.36.0, whose Botocore dependency supports these options and prevents automatically generated `x-amz-checksum-*` values from being added to signed upload requests. Upload URLs are valid for 3600 seconds; signed download URLs retain a 900-second default.

## R2 bucket CORS

For the production Vercel app and local Next.js development, set this policy on the private bucket:

```json
[
  {
    "AllowedOrigins": [
      "https://ai-lms-lovat.vercel.app",
      "http://localhost:3000"
    ],
    "AllowedMethods": ["PUT", "GET", "HEAD"],
    "AllowedHeaders": ["Content-Type", "Range"],
    "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"],
    "MaxAgeSeconds": 3600
  }
]
```

Add exact Vercel preview origins only if previews need direct uploads. Do not use `*` for origins. `ETag` must be exposed so browser JavaScript can read each multipart part's tag for completion. `Content-Length` is included for browser reads but is not a request header required by the presigned PUT. CORS does not make objects public.

The application API has a separate CORS policy. Set `CORS_ORIGINS` to the exact frontend origins, including `https://ai-lms-lovat.vercel.app` and `http://localhost:3000`.

## Limits and failure state

Images use `MAX_IMAGE_SIZE_MB` and allow JPEG, PNG, WEBP, and GIF. Their object signatures are checked at completion. `MAX_VIDEO_SIZE_MB=2048` controls lesson video and PDF direct-upload limits. `MAX_UPLOAD_SIZE_MB` still limits the legacy server-proxied endpoint. An upload that reaches `/uploads/complete` is made ready only after R2 metadata and file-signature checks succeed and the DB transaction commits.

Cancellation calls R2 multipart abort for chunked files. It keeps an earlier verified lesson video ready when one exists; failed uploads set `video_status=failed`. A new presign replaces the prior grant. Failed verification invalidates that grant and does not publish the object key.

## Backend credentials

Configure these only in the backend's production environment, never as `NEXT_PUBLIC_*` values and never in the browser:

- `R2_ACCOUNT_ID` (or `STORAGE_ACCOUNT_ID`)
- `R2_ACCESS_KEY_ID` (or `STORAGE_ACCESS_KEY_ID`)
- `R2_SECRET_ACCESS_KEY` (or `STORAGE_SECRET_ACCESS_KEY`)
- `R2_BUCKET` (or `STORAGE_BUCKET`)

The service constructs `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` and uses region `auto`. The R2 API token needs **Object Read & Write** permissions scoped to this bucket. Read is used for HEAD/range validation and signed downloads; write is needed for puts, multipart operations and cleanup. Production dashboard values and token permissions were not accessible from this repository, so they must be confirmed in the host's environment settings and Cloudflare dashboard.
