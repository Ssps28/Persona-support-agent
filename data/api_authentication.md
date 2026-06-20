# API Authentication Troubleshooting Guide

## Overview
CloudSuite's REST API uses Bearer Token authentication. This guide covers common authentication errors and how to resolve them.

## Authentication Method
All API requests must include an `Authorization` header in the following format:

```
Authorization: Bearer <your_api_key>
```

API keys can be generated from Settings > Developer > API Keys. Each workspace can have up to 10 active API keys at a time.

## Common Error Codes

### 401 Unauthorized
This means the request was made without a valid Bearer token, or the token is malformed.
Causes:
- Missing `Authorization` header entirely
- Token has extra whitespace or line breaks copied accidentally
- Using an expired or revoked API key
- Using a key generated in a different workspace than the one being queried

Resolution:
- Regenerate the key from Settings > Developer > API Keys
- Confirm the header format exactly matches `Bearer <key>` with a single space
- Verify the key has not been revoked (revoked keys show a strikethrough in the dashboard)

### 403 Forbidden
The token is valid, but lacks permission for the requested resource.
Causes:
- API key was generated with "Read Only" scope but the request is a POST/PUT/DELETE
- The associated user account does not have admin rights for the requested workspace resource

Resolution:
- Check key scope under Settings > Developer > API Keys > [Key Name] > Permissions
- Regenerate with "Read/Write" scope if write access is required

### 429 Too Many Requests
Rate limit exceeded. CloudSuite enforces:
- 100 requests per minute for Free and Starter plans
- 1,000 requests per minute for Business and Enterprise plans

Resolution:
- Implement exponential backoff in your client (wait 2^n seconds between retries)
- Check the `X-RateLimit-Remaining` response header to track quota proactively
- Contact sales for a custom rate limit if your integration requires sustained higher throughput

## Token Expiration Policy
API keys do not expire automatically unless:
- They are manually revoked by an admin
- The workspace subscription is downgraded below the plan tier that supports API access (Free tier does not include API access)
- 12 months of inactivity (no requests made using that key)

## Testing Your Authentication
Use this cURL command to verify your key works:

```bash
curl -X GET https://api.cloudsuite.io/v1/account \
  -H "Authorization: Bearer YOUR_API_KEY"
```

A successful response returns a 200 status code with your account JSON payload. A 401 confirms the key itself is the problem; a 403 confirms it's a permissions/scope problem.

## Webhook Signature Verification
For webhook payloads, CloudSuite signs each request with HMAC-SHA256 in the `X-CloudSuite-Signature` header. Verify this signature server-side before trusting webhook payloads to prevent spoofed requests.

## Related Articles
- Generating and Managing API Keys
- Webhook Configuration Guide
- Rate Limits and Plan Tiers
