# Password Reset Guide

## Overview
If you are unable to log in to your CloudSuite account because you forgot your password, follow this guide to regain access securely.

## Standard Password Reset (Self-Service)
1. Go to the login page at app.cloudsuite.io/login
2. Click "Forgot Password?" directly below the password field
3. Enter the email address associated with your account
4. Check your inbox for an email titled "Reset your CloudSuite password" — this arrives within 2-3 minutes
5. Click the reset link in the email. The link is valid for 30 minutes only
6. Enter a new password. Passwords must be at least 10 characters and include one number and one special character
7. You will be automatically logged in after a successful reset

## Troubleshooting: Reset Email Not Received
- Check your Spam/Junk folder first — emails from no-reply@cloudsuite.io are sometimes filtered
- Confirm you are using the exact email address registered on the account (check with your workspace admin if unsure)
- Wait at least 5 minutes before requesting a second email. Requesting multiple resets in quick succession can trigger a temporary cooldown of 15 minutes
- If using a corporate email, ask your IT department to allowlist the domain cloudsuite.io

## Account Lockout After Failed Attempts
After 5 consecutive failed login attempts, the account is temporarily locked for 20 minutes as a security measure. During lockout, password reset emails still work and will lift the lock immediately upon successful reset.

## Resetting Password When SSO Is Enabled
If your organization has Single Sign-On (SSO) enabled (Google Workspace, Okta, or Azure AD), the standard password reset will not work, since CloudSuite does not store a separate password for SSO accounts. In this case:
1. Reset your password through your organization's identity provider (e.g., Okta, Google Workspace admin)
2. Contact your workspace administrator if you do not have access to the identity provider directly

## Two-Factor Authentication (2FA) Recovery
If you have 2FA enabled and lost access to your authenticator device:
1. On the login screen, click "Use a backup code instead"
2. Enter one of the 10 backup codes provided when you first set up 2FA
3. If you have no backup codes remaining, you must contact support with proof of account ownership (billing receipt or domain verification) to manually disable 2FA

## Related Articles
- Setting Up Two-Factor Authentication
- Managing Workspace Admin Permissions
- Account Security Best Practices
