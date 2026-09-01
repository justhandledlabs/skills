# Security and authorized-use boundaries

uBrowser controls a real local Chromium instance. Treat that as access to whatever the selected profile can reach.

## Persistent profiles

- The upstream default profile may preserve cookies, local storage, IndexedDB, preferences, and authenticated state across restarts.
- Use a dedicated profile for browser automation rather than a personal everyday profile.
- Protect the profile directory with normal operating-system access controls.
- Do not copy, upload, publish, or attach the profile directory.
- Remove the dedicated profile only when the user explicitly requests it and understands that saved sessions will be lost.

## Authorized targets

Use the runtime only on sites, accounts, and data the user is authorized to access. Do not use it to bypass authentication, authorization, CAPTCHAs, anti-bot controls, rate limits, robots policies, or contractual restrictions.

## Credentials and private data

- Prefer the site's normal interactive sign-in flow.
- Do not place secrets in prompts, logs, screenshots, fixtures, or marketplace support messages.
- Redact console and network output before sharing it because requests may expose tokens, identifiers, or personal data.
- Stop when a workflow would submit a purchase, publish content, message another person, accept terms, change prices, connect payments, or otherwise represent the user without specific authorization.

## Resource blocking

The upstream runtime can block images, fonts, media, or stylesheets for speed. That may alter layout and behavior. Disable such optimization when validating visual presentation, accessibility, responsive behavior, or any workflow where layout affects the result.
