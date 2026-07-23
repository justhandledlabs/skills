---
name: pipeline-reporter-free
description: Generate pipeline reports from CRM CSV exports. Use when the user says "analyze pipeline", "generate pipeline report", "forecast from CSV", "sales report", or asks for a sales pipeline summary, weighted forecast, stage forecast, rep performance, opportunity analysis, or CRM export review from deal/opportunity CSV data. This is the single-report, no-CRM-connection version; for 12-month forecasting, CRM API connections, PDF export, and scheduled reports, use pipeline-reporter-pro.
license: MIT
metadata:
  version: 1.0.0
  author: JustHandled Labs
  triggers:
  - analyze pipeline
  - generate pipeline report
  - forecast from CSV
  - sales report
---
# Pipeline Reporter

Generate a Markdown pipeline report from a CRM export CSV containing deal or opportunity rows. The report must include pipeline summary, forecast by stage, and rep performance.

## Accepted Input

Accept a CSV file or pasted CSV data with opportunity-level records.

Standard column mapping:

- `deal_name`: opportunity or deal name
- `amount`: deal value
- `stage`: current sales stage
- `owner`: rep, account executive, or deal owner
- `close_date`: expected close date

Common aliases may be mapped automatically:

| Standard Field | Acceptable Aliases |
|---|---|
| `deal_name` | `deal`, `opportunity`, `opportunity_name`, `name`, `account_name` |
| `amount` | `value`, `deal_value`, `arr`, `mrr`, `revenue`, `forecast_amount` |
| `stage` | `pipeline_stage`, `sales_stage`, `status`, `deal_stage` |
| `owner` | `rep`, `sales_rep`, `account_executive`, `ae`, `deal_owner` |
| `close_date` | `expected_close_date`, `forecast_close_date`, `close`, `close_dt` |

If the CSV uses different names, infer only obvious mappings and show the mapping used before the report.

## Missing Columns

Handle missing columns gracefully:

- If `amount` is missing, ask the user for the value column before calculating totals or weighted pipeline.
- If `stage` is missing, ask the user for the stage/status column before forecasting.
- If both `amount` and `stage` are present but `owner` is missing, continue with pipeline and stage analysis, then ask whether to provide the owner column for rep performance.
- If `deal_name` is missing, continue with row counts and aggregate analysis using row numbers as deal identifiers.
- If `close_date` is missing, continue with current pipeline analysis and label date-based forecast sections as unavailable.
- If multiple plausible columns exist for a required field, ask the user to choose the mapping instead of guessing.

Do not fabricate missing values. Make partial reports explicit with a short `Missing / Assumed Fields` section.

## Stage Probabilities

Use explicit probability weights for weighted pipeline. If the CSV includes a probability column such as `probability`, `probability_percent`, `win_probability`, or `weighted_probability`, use it after normalizing percentages to decimals.

If no probability column exists, apply these default stage weights:

| Stage Contains | Probability |
|---|---:|
| `closed won`, `won` | 100% |
| `commit`, `contract`, `legal`, `procurement`, `negotiation` | 80% |
| `proposal`, `quote`, `pricing` | 60% |
| `qualified`, `solution`, `demo`, `evaluation`, `technical validation` | 40% |
| `discovery`, `needs analysis`, `meeting scheduled` | 25% |
| `prospecting`, `lead`, `new`, `identified` | 10% |
| `closed lost`, `lost`, `disqualified` | 0% |
| Unknown or unmatched stage | 0% until the user confirms a probability |

For unknown stages, include the stage in `Needs Confirmation` and ask the user for its probability if a precise weighted forecast is required.

## Calculations

Parse `amount` as currency/number by removing currency symbols, commas, and whitespace. Treat blank or unparsable amounts as missing and exclude them from financial totals, while counting the affected rows.

Weighted amount formula:

```text
weighted_amount = amount * probability
```

Where probability is a decimal from 0 to 1. Examples:

- `$10,000` at `60%` = `$6,000`
- `10000` at `0.6` = `$6,000`
- Closed won = amount * 1.0
- Closed lost = amount * 0.0

Required report calculations:

- Total raw pipeline: sum of valid `amount`
- Total weighted pipeline: sum of `weighted_amount`
- Deal count: total rows and valid financial rows
- Average deal size: total raw pipeline / valid financial rows
- Stage forecast: count, raw amount, weighted amount, average deal size, share of weighted pipeline by stage
- Rep performance: count, raw amount, weighted amount, average deal size, stage mix, close-date risk when `close_date` exists

When `close_date` exists, group forecast by month or quarter if useful. Flag overdue open deals where `close_date` is before the current date and the stage is not closed won/lost.

## Workflow

1. Read the CSV with a real CSV parser when tool access is available; otherwise carefully parse pasted tabular data.
2. Detect and display the column mapping.
3. Check for missing required fields and either ask for missing mappings or proceed with an explicit partial-report note.
4. Normalize amounts, stages, owners, dates, and probability values.
5. Assign stage probabilities from a probability column or the default table.
6. Calculate raw and weighted pipeline.
7. Produce the Markdown report.
8. Run quality checks before returning.

## Output Format

Return a Markdown report:

```markdown
# Pipeline Report

## Column Mapping

| Standard Field | CSV Column | Status |
|---|---|---|
| deal_name | <column or unavailable> | <mapped / missing / inferred> |

## Executive Summary

- Total deals: <count>
- Valid financial deals: <count>
- Total raw pipeline: $<amount>
- Total weighted pipeline: $<amount>
- Average deal size: $<amount>
- Largest stage by weighted pipeline: <stage>
- Top rep by weighted pipeline: <owner or unavailable>

## Forecast by Stage

| Stage | Probability | Deals | Raw Pipeline | Weighted Pipeline | Weighted Share |
|---|---:|---:|---:|---:|---:|

## Rep Performance

| Owner | Deals | Raw Pipeline | Weighted Pipeline | Avg Deal Size | Notes |
|---|---:|---:|---:|---:|---|

## Close-Date Outlook

<Monthly/quarterly forecast, overdue deal notes, or "Close-date analysis unavailable because close_date was not provided.">

## Risks and Follow-Ups

- <Missing fields, unknown stages, overdue deals, concentration risks, or data quality issues.>
```

Keep the report concise and practical. Prefer tables for summary data and bullets for recommendations.

## Quality Checks

Before returning, verify:

- The report shows the column mapping used.
- Missing columns are handled with a prompt or an explicit partial-report note.
- Weighted pipeline uses `amount * probability`.
- Probability values are decimals internally and percentages only in display.
- Closed won is weighted at 100% and closed lost/disqualified at 0%.
- Unknown stages are not assigned arbitrary probabilities.
- Rep performance is included when `owner` is available, and gracefully marked unavailable when it is not.
- The final answer includes pipeline summary, forecast by stage, and rep performance unless the CSV is missing fields required for those sections.
