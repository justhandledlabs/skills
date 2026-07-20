---
name: outreach-writer-free
description: Generate personalized B2B cold emails from lead profiles. Use when the user says "write a cold email", "outreach to", "generate email", "draft prospecting email", or asks to create prospecting outreach from a company name, prospect name, title, and optional trigger event using PAS, MEDDIC, Challenger, or auto-detected positioning. This writes a single email; for multi-lead campaigns and Day 1/3/7 sequences from a CSV, use outreach-writer-pro.
metadata:
  version: 1.0.0
  author: JustHandled Labs
  triggers:
  - write a cold email
  - outreach to
  - generate email
  - draft prospecting email
---
# Outreach Writer

Draft concise, personalized cold emails from lead profiles. The output must include 3 subject lines, one email body under 150 words, and one follow-up suggestion.

For framework details, read [references/frameworks.md](references/frameworks.md) when the user selects PAS, MEDDIC, Challenger, asks how the framework was chosen, or provides a sparse lead profile that needs auto-detection.

## Accepted Inputs

Accept a lead profile with:

- Company name
- Prospect name
- Prospect title
- Optional trigger event, such as hiring, funding, product launch, expansion, technology change, job post, public quote, or recent company news
- Optional offer, product, value proposition, pain hypothesis, proof point, tone, CTA, and selected framework

If company name, prospect name, or title is missing, ask for the missing field before drafting. If the trigger event is missing, write the email from role/company context and label the personalized detail as profile-derived instead of event-derived.

## Framework Selection

Use the framework requested by the user when provided:

- `PAS`: Use when the profile includes a clear operational pain, inefficiency, missed revenue, risk, or manual process.
- `MEDDIC`: Use when the profile suggests enterprise sales, multi-stakeholder buying, budget ownership, measurable KPIs, procurement, or revenue/process metrics.
- `Challenger`: Use when the strongest angle is a useful commercial insight, market shift, hidden cost, or reframing of the prospect's status quo.

If no framework is selected, auto-detect:

1. Choose Challenger when there is a strong trigger event or market insight.
2. Choose MEDDIC when the prospect is a senior buyer and the offer depends on measurable business impact.
3. Choose PAS when the pain is obvious and the offer is direct.
4. If uncertain, use PAS and state `Framework: PAS (auto-detected)`.

## Personalization Rules

Every email must include at least one specific personalized detail from the lead profile. Specific details include:

- Prospect name and title tied to why they care
- Company name tied to a stated business model, segment, product, team, or initiative
- Trigger event with date or context, such as hiring, launch, funding, expansion, or technology change
- A role-specific pain hypothesis connected to the prospect's responsibilities

Do not count generic praise as personalization. Avoid lines like `I love your company`, `big fan of what you do`, or `congrats on the growth` unless they are attached to a concrete event or detail.

If the profile does not contain a usable detail beyond name, company, and title, ask for one of: target pain, recent trigger, company initiative, or offer.

## Workflow

1. Parse the lead profile:
   - Company
   - Prospect name
   - Title
   - Trigger event
   - Offer/value proposition
   - Persona pain and likely business priority
2. Select or confirm the framework.
3. Identify one specific personalized detail and write it down mentally before drafting.
4. Draft 3 subject lines:
   - Keep each under 8 words when practical.
   - Avoid spammy punctuation, hype, and fake urgency.
   - Include one subject that references the company or trigger.
5. Draft the email body:
   - Stay under 150 words.
   - Use plain text.
   - Keep paragraphs short.
   - Include the personalized detail in the first 1-2 sentences.
   - Make one clear pain/value connection.
   - End with a low-friction CTA.
6. Add one follow-up suggestion:
   - Mention timing, such as `3 business days later`.
   - Include the angle to use, not a full second email unless requested.
7. Run the quality checks before returning.

## Output Format

Return this Markdown shape:

```markdown
Framework: <PAS | MEDDIC | Challenger> (<selected by user | auto-detected>)

Personalized detail used: <specific detail>

Subject lines:
1. <subject>
2. <subject>
3. <subject>

Email body:
Hi <Prospect name>,

<email body under 150 words>

Follow-up suggestion:
<timing plus angle for the follow-up>
```

## Quality Checks

Before answering, verify:

- The output includes exactly 3 subject lines.
- The email body is under 150 words.
- The email body includes at least one specific personalized detail.
- The personalized detail is not generic praise.
- The output includes one follow-up suggestion.
- The selected framework is PAS, MEDDIC, or Challenger.
- Claims are grounded in the provided lead profile; do not invent company facts, metrics, customer names, or trigger events.
