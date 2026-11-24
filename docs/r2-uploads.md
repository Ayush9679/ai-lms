# Private Cloudflare R2 uploads

## Current flows

The production `origin/main` course-thumbnail client uses the direct upload flow: `POST /api/v1/uploads/presign`, a browser `PUT` to the returned URL, then `POST /api/v1/uploads/complete` with only the signed upload token. R2 bucket CORS applies to the browser PUT and signed GETs. The backend checks ownership, object length, declared MIME metadata, and a bounded file signature before persisting the R2 key. The bucket stays private; reads use short-lived signed GET URLs. The legacy authenticated multipart endpoint remains available for compatibility, and the Render API origin still must be included in `CORS_ORIGINS` for API requests.

No live browser upload or production R2 smoke test was run for this change. Automated tests mock storage. A DevTools status/body from the failed production request is required to attribute the original live failure; source inspection alone cannot prove whether the failure is R2 CORS, signature mismatch, HTTP validation, storage, or browser networking.

## R2 bucket CORS

For the direct browser-to-R2 flow, configure an explicit private-bucket CORS rule with:

```json
[
  {
    "AllowedOrigins": [
      "https://ai-lms-lovat.vercel.app",
      "http://localhost:3000"
    ],
    "AllowedMethods": ["PUT", "GET", "HEAD"],
    "AllowedHeaders": ["Content-Type", "Content-Length", "If-None-Match"],
    "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"],
    "MaxAgeSeconds": 3600
  }
]
```

Add the exact Vercel preview origins only if previews need direct uploads. Do not use `*` for origins. The presigned PUT binds the MIME type, byte length and `If-None-Match: *`; current botocore output signs `content-length`, `content-type`, `host`, and `if-none-match`. The browser must send the signed headers unchanged; it controls `Content-Length`, so the file size must exactly match the grant. Browser GET requests use short-lived signed object URLs. CORS does not make objects public.

The Render API has its own separate CORS setting. Set `CORS_ORIGINS` to explicit frontend origins, including `https://ai-lms-lovat.vercel.app` and the local origin used for development.

## Limits and failure state

Images use `MAX_IMAGE_SIZE_MB` and allow JPEG, PNG, WEBP, and GIF. Their object signatures are checked at completion. Videos currently use a single presigned PUT up to `MAX_VIDEO_SIZE_MB` (configured as 2048 MB), not multipart/resumable upload. A failed request must be retried from byte zero. Duration is still teacher-entered; the backend does not probe video metadata. An upload is marked ready only after the R2 object is verified and its database update commits.

Cancellation keeps an earlier verified lesson video ready when one exists; an explicit failed PUT can be reported with `failed: true` on `/uploads/cancel`, which leaves `video_status=failed`. A new presign replaces the prior grant. Failed verification invalidates that grant and does not publish the object key.
