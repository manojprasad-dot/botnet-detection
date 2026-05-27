# KOVIRX Brand Assets

The source logo concept board has been separated into individual PNG assets so the UI can use clean, purpose-specific versions instead of cropping a full multi-logo sheet at runtime.

## Files

- `backend/app/static/brand/kovirx-logo-sheet.png`: original multi-variation source sheet
- `backend/app/static/brand/kovirx-horizontal-dark-clean.png`: preferred dashboard logo with shield and wordmark only
- `backend/app/static/brand/kovirx-horizontal-dark.png`: dark horizontal variant from the source sheet
- `backend/app/static/brand/kovirx-horizontal-light.png`: light horizontal variant from the source sheet
- `backend/app/static/brand/kovirx-horizontal-light-compact.png`: compact light horizontal variant
- `backend/app/static/brand/kovirx-shield-primary.png`: standalone shield from the top-left variation
- `backend/app/static/brand/kovirx-shield-dark.png`: standalone shield from the middle-left variation
- `backend/app/static/brand/kovirx-shield-compact.png`: standalone compact shield from the bottom-left variation

## UI Usage

The command center currently uses `kovirx-horizontal-dark-clean.png` in the header. The tagline remains rendered as real HTML text so it stays sharp and readable at every screen size.
