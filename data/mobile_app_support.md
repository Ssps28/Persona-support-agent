# Mobile App Support

## Supported Platforms
CloudSuite mobile apps are available for iOS 15+ and Android 10+. The mobile app supports core ticket management, notifications, and basic reporting; advanced admin settings (billing, API keys, integrations) are web-only.

## Push Notifications Not Working
1. Confirm notification permissions are enabled in your device's system settings for the CloudSuite app
2. In-app, check Settings > Notifications > Push Notifications is toggled on
3. iOS users: ensure "Background App Refresh" is enabled, as this is required for the app to register for push tokens reliably
4. Android users: check that battery optimization is not restricting the app (Settings > Apps > CloudSuite > Battery > Unrestricted)

## App Crashes on Launch
1. Confirm you're on the latest app version from the App Store / Play Store
2. Try logging out and back in if the crash started after a recent password or permission change
3. Clear app cache (Android: Settings > Apps > CloudSuite > Storage > Clear Cache; this does not delete your account data)
4. If crashes persist after these steps, this likely indicates a device-specific compatibility issue requiring escalation with device model and OS version details

## Offline Mode
The mobile app caches your last-viewed tickets and projects for offline viewing, but creating or editing content requires an active connection. Changes attempted offline are queued and synced automatically once connectivity returns, though sync conflicts (if the same record was edited elsewhere) require manual resolution on next sync.

## Related Articles
- Two-Factor Authentication Recovery
- System Performance and Uptime
