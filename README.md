# BAL_BILAN — Multi-Season Order Book Dashboard (Power BI)

A self-initiated Power BI dashboard built during my Supply Chain & Newness Planning
internship at a luxury fashion house, consolidating four seasons of pre-production
order data into a single interactive reporting tool — replacing a manual,
spreadsheet-only reconciliation process.

> **Note on data:** This repo contains no proprietary company data. The screenshots,
> DAX, and Power Query samples below use a synthetic dataset built to mirror the real
> workbook's structure (same shape, same logic, invented codes/quantities). Column and
> table names have been genericized where they reflected internal naming conventions.

---

## The problem

Each season, the "Newness" planning cycle produces two versions of the same order
book at different points in time:

- **Pre-activities extract** — orders as placed by sales teams during the showroom event
- **Post-activities extract** — the same orders after cancellations, code changes,
  and quantity adjustments have been pushed into the ERP system

Comparing the two — to see what got cancelled, what changed code, and where feedback
status shifted — was done by hand in Excel, season after season, with no persistent
view across seasons and no repeatable comparison logic.

## What I built

- A **multi-season data model** (4 seasons) consolidating the pre- and
  post-activities extracts into a single Power BI semantic model
- A **season-over-season comparison layer**, matching line items between the two
  extracts (including handling code changes, where an item's identifier changes
  between the two snapshots) and flagging status: matched / code-changed / dropped /
  newly added
- **DAX measures** for cancellation rate, value at risk, and status breakdowns by
  product category
- **Report pages**: an order book catalogue view, a cancellation deep-dive, a
  season timeline/milestone tracker, and a season-comparison summary
- Custom visuals (HTML Content, Smart Filter Pro) for richer card-based layouts
  than native Power BI visuals support

## How it replaced the manual workflow

| Before | After |
|---|---|
| Manual VLOOKUP/pivot comparison per season in Excel | Automated match logic in Power Query, re-run each season |
| No cross-season view — each season's file was standalone | Single model, filterable by season |
| Cancellation/status changes tracked informally in comments | Structured status field, calculated automatically |
| Refresh = re-doing the analysis from scratch | Refresh = re-run the same pipeline on new source files |

## Tech stack

- **Power BI Service** (web) — Power Query (M) for transformation, DAX for measures
- **Python/openpyxl/pandas** — source file consolidation and structural validation
  before load
- **Excel** — source system extracts (ERP order data)

---

## Sample DAX (genericized)

```dax
// Cancelled units as % of wholesale channel
% Cancelled WHLS =
DIVIDE(
    [Cancelled WHLS Units],
    [Total WHLS Units],
    0
)

Cancelled WHLS Units =
CALCULATE(
    DISTINCTCOUNT(OrderBook[ItemCode]),
    OrderBook[FinalStatus] = "OUT",
    OrderBook[WHLS_Qty] > 0
)

Season Sort =
IF(OrderBook[Season_Label] = "S1", 1,
IF(OrderBook[Season_Label] = "S2", 2, 3))
```

## Sample Power Query (genericized)

```m
// Keep only real sheet objects when folder-loading multiple season files
= Table.SelectRows(Source, each [Kind] = "Sheet")

// Trim hidden whitespace that broke season-over-season grouping
= Table.TransformColumns(PreviousStep, {{"FinalStatus", Text.Trim, type text}})
```

---

## Repo structure

```
/screenshots/          — report page exports (synthetic data)
/dax/                  — genericized measure definitions
/power-query/          — genericized M query snippets
README.md
```

## Limitations of this repo

- The synthetic dataset is illustrative only — it demonstrates structure and logic,
  not real business volumes or outcomes
- The original report used live organizational data sources and internal image/asset
  URLs that are not reproducible outside that environment
