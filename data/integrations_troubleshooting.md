# Third-Party Integration Troubleshooting

## Overview
CloudSuite supports native integrations with Slack, Salesforce, Zapier, and Google Workspace. This guide covers common integration sync issues.

## Slack Integration

### Notifications Not Appearing
1. Confirm the integration shows "Connected" under Settings > Integrations > Slack
2. Check that the target Slack channel hasn't been archived or renamed after the integration was set up — this breaks the webhook silently
3. Reinstall the Slack app from Settings > Integrations > Slack > Reinstall if the workspace's Slack admin recently rotated app credentials

### Common Error: "Invalid Webhook URL"
This occurs when the Slack workspace admin revokes app permissions outside of CloudSuite. Resolution: disconnect and reconnect the integration; this generates a fresh webhook URL.

## Salesforce Sync

### Sync Delays
Salesforce sync runs on a 15-minute polling interval by default (Business plan) or near real-time via webhooks (Enterprise plan only). If records aren't appearing within the expected window:
1. Check Settings > Integrations > Salesforce > Sync Logs for error entries
2. Common cause: field mapping mismatch — a custom Salesforce field referenced in CloudSuite no longer exists or was renamed
3. Confirm the Salesforce API user has not hit Salesforce's own API call limits (visible in Salesforce Setup > API Usage)

### Duplicate Records
Usually caused by mismatched deduplication keys. CloudSuite deduplicates Salesforce contacts by email address by default; if email fields are blank or inconsistently formatted, duplicates will be created. Configure a custom dedup key under Settings > Integrations > Salesforce > Field Mapping.

## Zapier Integration
CloudSuite exposes triggers (New Ticket, Ticket Resolved, New Contact) and actions (Create Ticket, Update Contact) via Zapier. 
- Zaps failing silently: check the Zapier task history for the specific run; CloudSuite returns descriptive error payloads that Zapier logs verbatim
- Rate limits apply per the API tier described in the API Authentication guide — high-frequency Zaps on Free/Starter plans may hit 429 errors

## Google Workspace SSO
Used for both login and calendar sync. If calendar events aren't syncing:
1. Confirm the connected Google account has calendar read/write scope granted (re-authenticate if scope was reduced)
2. Check that the calendar selected for sync under Settings > Integrations > Google Workspace > Calendar matches the one the user expects

## General Integration Debugging Steps
1. Check Settings > Integrations > [Service] > Sync Logs first — most issues leave a descriptive error there
2. Disconnect and reconnect the integration to force fresh OAuth tokens
3. Verify the connected account still has admin/appropriate permissions on the third-party platform itself
4. For persistent failures after reconnection, this typically indicates a platform-side API change and should be escalated to engineering

## Related Articles
- API Authentication Troubleshooting Guide
- Webhook Configuration Guide
- Managing Workspace Admin Permissions
