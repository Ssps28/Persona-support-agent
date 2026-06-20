# Data Export and Backup Guide

## Exporting Your Data
CloudSuite allows full workspace data export at any time from Settings > Data > Export Workspace. Exports are generated as a ZIP file containing CSV files for each data type (tickets, contacts, projects, custom fields) and are emailed as a download link once ready.

## Export Processing Time
- Small workspaces (under 10,000 records): typically ready within 5 minutes
- Large workspaces (100,000+ records): can take up to 2 hours
- You will receive an email notification when the export is ready; the download link is valid for 7 days

## Automated Backups
Business and Enterprise plans include automated nightly backups, retained for 30 days. These are for disaster recovery purposes and are not self-service downloadable — restoring from an automated backup requires a support request specifying the desired restore date.

## API-Based Export
For programmatic export, use the `/v1/export` endpoint, which supports filtering by date range and data type. This is recommended for customers needing recurring exports (e.g., nightly syncs to an internal data warehouse) rather than manually triggering exports from the UI each time.

## GDPR / Data Deletion Requests
Full account and data deletion requests (right to erasure) must go through Settings > Data > Delete Workspace, which requires Owner-level confirmation and a 14-day grace period before permanent deletion. This grace period exists so accidental deletions can be reversed; during this window, contact support to halt the deletion process.

## Related Articles
- Billing Policy and FAQ
- Managing Workspace Admin Permissions
