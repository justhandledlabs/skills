---
name: lead-enricher-free
description: Build enriched B2B lead profiles from a company URL, company name plus domain, or LinkedIn company URL. Use when the user says "enrich this company", "find decision makers at", "who works at", "build a lead profile", or asks for company enrichment, decision-maker discovery, estimated business email patterns, recent buying signals, funding stage, company size, industry, or tech stack research. This enriches one company at a time; for batch lists, email verification, scoring, and CRM sync, use lead-enricher-pro.
license: MIT
metadata:
  version: 1.0.0
  author: JustHandled Labs
  triggers:
  - enrich this company
  - find decision makers at
  - who works at
  - build a lead profile
---
# Lead Enricher

Turn basic company information into a Markdown lead profile for GTM research. This free version uses public web research plus optional free-tier enrichment APIs when credentials are available.

## Accepted Inputs

Accept any of these:

- Company URL: `https://example.com`
- Company name plus domain: `Example Inc, example.com`
- LinkedIn company URL: `https://www.linkedin.com/company/example`

If the input is ambiguous, infer the most likely company and flag the identity confidence. Ask a clarifying question only when multiple companies share the same name and no domain or LinkedIn URL is available.

## Data Sources

Use the best available source path for the environment:

1. Public web research from the company site, careers page, blog, press page, job posts, Crunchbase-like snippets, LinkedIn snippets, and search results.
2. Clearbit free tier when `CLEARBIT_API_KEY` is available:
   - Company size
   - Industry/category
   - Location
   - Social profiles
   - Funding or company metadata when available
3. Hunter.io free tier when `HUNTER_API_KEY` is available:
   - Email pattern
   - Department/person hints
   - Verification status when available
4. BuiltWith when `BUILTWITH_API_KEY` is available, or public page inspection when not:
   - Analytics, CRM, CMS, ecommerce, CDN, marketing automation, and major frontend/backend technologies

Never invent exact facts. When an API is unavailable or a field is inferred from public snippets, mark it as simulated/free-tier or inferred.

## Workflow

1. Normalize the target:
   - Extract canonical domain from a URL or LinkedIn company page.
   - Record alternate names, parent/subsidiary signals, and the source used for identity.
2. Build the company profile:
   - Company name
   - Website/domain
   - Industry
   - Company size
   - Funding stage
   - Headquarters or primary market
   - One-sentence business description
3. Detect technology stack:
   - Prefer BuiltWith if available.
   - Otherwise inspect the website and public source hints for CMS, ecommerce, analytics, CRM, ads, email, chat, payment, CDN, hosting, and frontend framework.
   - Group unknowns under `Unknown / not detected`.
4. Find decision-maker targets:
   - Return at least 3 decision-maker rows every time.
   - Prefer actual people from public sources when available.
   - If actual people are not confidently found, return likely buyer roles instead and label person/name fields as `Not found`.
   - Include title, likely buying role, LinkedIn URL or search URL, estimated email or email pattern, confidence score, and source note.
5. Identify recent signals:
   - Hiring: new roles, careers page growth, departments hiring.
   - Funding/news: funding announcements, acquisitions, partnerships, executive changes.
   - Product launches: blog, changelog, press releases, launches, pricing/package changes.
   - If no signal is found, say `No recent public signal found` and assign low confidence.
6. Score confidence:
   - High: confirmed by company/API source or multiple recent public sources.
   - Medium: supported by one credible public source or consistent pattern.
   - Low: inferred, stale, or simulated because no free source confirmed it.

## Decision-Maker Requirements

Always include at least 3 titles. For B2B GTM, choose the most relevant titles from the company context. Common defaults:

- CEO / Founder / President
- VP Sales / Head of Sales / Chief Revenue Officer
- VP Marketing / Head of Growth / Chief Marketing Officer
- VP Operations / COO
- CTO / VP Engineering / Head of IT
- Head of Partnerships / Business Development

For each decision maker, include:

- `Name`
- `Title`
- `Buying role`
- `LinkedIn`
- `Estimated email`
- `Confidence`
- `Why this person/title matters`

Estimated emails must be clearly labeled as estimated unless verified by Hunter.io or another credible source. Prefer patterns such as `first.last@domain.com`, `first@domain.com`, or `flast@domain.com`; do not present guesses as deliverable verified addresses.

## Low-Confidence Flags

Flag a field as low confidence when:

- It is inferred from job posts, snippets, or generic industry assumptions.
- The source is older than 12 months.
- The API is unavailable and the field came from simulated/free-tier estimation.
- A person cannot be linked to a reliable profile.
- Email is pattern-based and unverified.

Use `[LOW CONFIDENCE]` inline next to the value and explain why in the source note.

## Output Shape

Return one Markdown lead profile:

```markdown
# Lead Profile: <Company>

## Snapshot

| Field | Value | Confidence | Source |
|---|---|---:|---|
| Website | <domain> | High | <source> |
| Industry | <industry> | Medium | <source> |
| Company size | <range> | Medium | <source> |
| Funding stage | <stage or Unknown> | Low | <source> |
| Headquarters | <location or Unknown> | Medium | <source> |

## What They Do

<1-3 sentence business description.>

## Tech Stack

| Category | Detected Tools | Confidence | Source |
|---|---|---:|---|
| Analytics | <tools or Unknown / not detected> | Low | <source> |
| CRM / Sales | <tools or Unknown / not detected> | Low | <source> |
| Marketing | <tools or Unknown / not detected> | Low | <source> |
| Website / App | <tools or Unknown / not detected> | Medium | <source> |

## Decision Makers

| Name | Title | Buying Role | LinkedIn | Estimated Email | Confidence |
|---|---|---|---|---|---:|
| <name or Not found> | <title> | <role> | <url or search URL> | <estimated/verified email or pattern> | <score>% |

## Recent Signals

| Signal | Detail | Date/Recency | Confidence | Source |
|---|---|---|---:|---|
| Hiring | <detail or No recent public signal found> | <date/unknown> | Low | <source> |
| Funding / News | <detail or No recent public signal found> | <date/unknown> | Low | <source> |
| Product / Launch | <detail or No recent public signal found> | <date/unknown> | Low | <source> |

## Outreach Angles

1. <angle tied to decision maker and signal>
2. <angle tied to tech stack or industry>
3. <angle tied to likely business priority>

## Confidence Notes

- <List every low-confidence or inferred field.>
- <Say which APIs were unavailable or simulated in v1.>
```

## Quality Checks

Before returning the profile, verify:

- The input company identity is clear enough to proceed.
- The profile has at least 3 decision-maker titles or people.
- Every estimated email is labeled estimated unless verified.
- Company size, funding stage, industry, tech stack, decision makers, and recent signals are present, even when the value is `Unknown`.
- Low-confidence fields are visibly flagged and explained.
- The final answer is Markdown and contains confidence scores.
