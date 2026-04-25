# Round 001 Integration Report - purchase_records

## Scope

This report covers the architect-level integration review for the `finance / purchase_records` tool.

Reviewed paths:

- `docs/rounds/round-001/requirements.md`
- `docs/rounds/round-001/test-plan.md`
- `docs/rounds/round-001/backend-report.md`
- `docs/rounds/round-001/frontend-report.md`
- `backend/app/modules/finance/purchase_records/`
- `backend/tests/finance/purchase_records/index_test.py`
- `frontend/src/tools/finance/purchase_records/`
- `frontend/tests/finance/purchase_records/index.spec.ts`

## Service Status

`docker compose ps` showed the required services running:

- `backend`: healthy on `localhost:8000`
- `frontend`: running on `localhost:15173`
- `db`: healthy on `localhost:15432`

HTTP reachability checks:

- `GET http://localhost:8000/api/v1/utils/health-check/` returned `200`
- `GET http://localhost:15173` returned `200`

## Backend Verification

Commands executed:

```bash
docker compose exec backend pytest tests/finance/purchase_records/index_test.py -q
docker compose exec backend alembic current
```

Results:

- Backend tests: `42 passed, 3 warnings`
- Alembic current: `b6a3b31a7cf9 (head)`

Warnings are the expected local default-secret warnings from `backend/app/core/config.py`.

## Frontend Verification

Command executed:

```bash
docker compose exec frontend bun run build
```

Result:

- Build passed.
- Generated purchase records chunk: `dist/assets/finance.purchase-records-XY1g0X37.js`
- No TypeScript errors.

Playwright command executed:

```bash
docker compose exec frontend bun run test -- tests/finance/purchase_records/index.spec.ts --reporter=line --timeout=15000
```

Result:

- Not completed.
- Outer command timed out after about 94 seconds with no Playwright test output.
- This matches the frontend report's current blocker: Playwright execution is blocked by the container/runtime test environment, not by a known application assertion failure.

## HTTP Integration Chain

I ran a real HTTP-level integration flow against `http://localhost:8000/api/v1` using a temporary normal user and the configured superuser.

Verified flow:

- Superuser login.
- Temporary normal user signup and login.
- `GET /users/me` for normal user.
- `POST /finance/purchase-records/ocr-preview` with screenshot file.
- Confirmed OCR preview did not create a purchase record.
- `POST /finance/purchase-records/` with multipart form and screenshot.
- Confirmed created record:
  - `status = draft`
  - `invoice_match_status = unmatched`
  - `subcategory = null` is allowed for `other_project`
  - screenshot metadata exists
- `GET /finance/purchase-records/{id}/screenshot` with Bearer token.
- Confirmed screenshot download returned the uploaded PNG bytes.
- Superuser list confirmed visibility of the normal user's normal record.
- Owner state transitions:
  - `draft -> submitted`
  - `submitted -> draft`
  - `draft -> submitted`
- Admin state transitions:
  - `submitted -> approved`
  - `approved -> submitted`
  - `submitted -> rejected`
- Owner edit while rejected:
  - amount updated
  - category changed to `transportation`
  - subcategory cleared with empty form value
- Owner resubmitted rejected record.
- Owner soft-deleted record.
- Deleted filter returned the deleted record.
- Owner restored the deleted record.
- Record was soft-deleted again at the end of the integration run.

Result:

- Main backend HTTP API chain passed.
- Screenshot is stored on disk and downloaded through the authenticated API.
- OCR preview returns only preview data and does not persist a purchase record.

Integration test record id:

- `3beb214c-f6e4-440d-9828-a00bd20a2e96`

The record was left soft-deleted as cleanup through public API behavior.

## Frontend/Backend Contract Review

Static contract review compared:

- `frontend/src/tools/finance/purchase_records/api.ts`
- `frontend/src/tools/finance/purchase_records/types.ts`
- `backend/app/modules/finance/purchase_records/router.py`
- `backend/app/modules/finance/purchase_records/models.py`

Confirmed aligned:

- API prefix: `/api/v1/finance/purchase-records`
- OCR preview:
  - frontend sends multipart `screenshot`
  - backend expects `screenshot: UploadFile`
- Create:
  - frontend sends multipart fields `purchase_date`, `amount`, `currency`, `order_name`, `category`, optional `subcategory`, optional `note`, `screenshot`
  - backend expects the same fields
- Update:
  - frontend sends optional multipart fields
  - `subcategory: null` is sent as an empty string, which backend interprets as clear-to-null
- State transition routes:
  - `submit`
  - `withdraw`
  - `approve`
  - `reject`
  - `unapprove`
- Delete and restore routes.
- Screenshot download:
  - frontend uses `fetch` with `Authorization: Bearer <token>`
  - backend requires authenticated access and returns `FileResponse`
- Type expectations:
  - `amount` serializes as string for frontend compatibility
  - status and invoice match status values match the documented constants

Noted but acceptable:

- Frontend sends a JSON `reason` body to `reject`.
- Backend currently ignores request bodies on `POST /reject`.
- HTTP integration confirmed this extra body does not break the endpoint.

## Verified Items

- Backend tests pass.
- Backend migration is at head.
- Frontend production build passes.
- Backend HTTP main chain passes.
- OCR preview does not create records.
- Screenshot binary is not stored in the database; API returns uploaded file bytes from local storage.
- Authenticated screenshot download works at HTTP level.
- Category/subcategory behavior matches requirements.
- Normal-user and admin state transitions work at HTTP level.
- Soft delete and restore work at HTTP level.
- Frontend route and API contract match backend routes.

## Not Verified

- Browser end-to-end interaction through Playwright.
  - Reason: `docker compose exec frontend bun run test -- tests/finance/purchase_records/index.spec.ts --reporter=line --timeout=15000` times out without Playwright output in the current container environment.
- Full UI-click workflow from browser:
  - upload screenshot
  - OCR prefill
  - modify fields
  - save draft
  - save and submit
  - withdraw
  - delete
  - deleted filter
  - restore
  - screenshot preview pop-up
  - Reason: same Playwright/runtime blocker.
- Real PaddleOCR recognition quality.
  - Reason: current environment validates OCR configuration and graceful fallback, not real model inference with deployed PaddleOCR model files.

## Risks / Follow-Up

- The frontend `reject` helper sends a `reason` field, but the backend does not persist or consume rejection reasons in this round. This is harmless for Round 001, but future rejection-reason requirements should add backend model/API support explicitly.
- Playwright runtime should be fixed before marking browser E2E coverage complete.
- Real OCR model deployment should be tested when PaddleOCR dependencies and `OCR_MODEL_DIR/det`, `rec`, `cls` model files are available in Docker.

## Conclusion

Round 001 `purchase_records` passes architect-level API integration review.

Accepted for this round:

- Backend module: passed.
- Frontend module: passed by build and contract review.
- HTTP backend integration chain: passed.

Remaining limitation:

- Browser Playwright E2E is not executed successfully in the current environment and remains a test-environment blocker.
