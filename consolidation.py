"""
BAL_BILAN — source file consolidation & pre/post-activity comparison (genericized)

Real workflow this supports: each season produces two extracts of the same
order book at different points in time —
  1. a pre-activities extract (orders as placed by sales teams)
  2. a post-activities extract (same orders after cancellations, code changes,
     and quantity adjustments have been pushed into the ERP system)

This script consolidates both into clean tables and produces a line-item-level
comparison, matched on item code (falling back to a "previous code" field when
an item's identifier changed between the two extracts — e.g. a style/material/
colour recode).

Table/column names below are genericized; the real script uses the source
system's actual schema.
"""

import pandas as pd
import numpy as np


def load_extract(path: str, sheet_name: str, qty_cols: list[str]) -> pd.DataFrame:
    """Load one season's raw extract and coerce quantity columns to numeric."""
    df = pd.read_excel(path, sheet_name=sheet_name, dtype=str)
    for col in qty_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def aggregate_pre_activities(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse to one row per item code, summing channel quantities."""
    agg = df.groupby("ItemCode", as_index=False).agg({
        "Description": "first",
        "Category": "first",
        "Line": "first",
        "WHLS_Qty": "sum",
        "RTL_Qty": "sum",
        "VIC_Qty": "sum",
        "TotalQty": "sum",
        "FirstFeedback": "first",
        "FinalStatus": "first",
        "CarryOver": "first",
        "DeliveryGroup": "first",
    })
    return agg.rename(columns={
        "WHLS_Qty": "PRE_WHLS", "RTL_Qty": "PRE_RTL",
        "VIC_Qty": "PRE_VIC", "TotalQty": "PRE_TOTAL",
        "FirstFeedback": "PRE_FirstFeedback", "FinalStatus": "PRE_FinalStatus",
        "CarryOver": "PRE_CarryOver", "DeliveryGroup": "PRE_DeliveryGroup",
    })


def aggregate_post_activities(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse the post-activities extract, building a match key that falls
    back to the item's previous code when a code change occurred."""
    df = df.copy()
    df["MatchKey"] = np.where(
        df["PreviousCode"].fillna("").str.strip() != "",
        df["PreviousCode"],
        df["ItemCode"],
    )
    agg = df.groupby("MatchKey", as_index=False).agg({
        "ItemCode": "first",
        "Description": "first",
        "RTL_Qty": "sum",
        "WHLS_Qty": "sum",
        "VIC_Qty": "sum",
        "TotalQty": "sum",
        "FirstFeedback": "first",
        "FinalStatus": "first",
        "DeliveryGroup": "first",
        "PreviousCode": "first",
    })
    return agg.rename(columns={
        "ItemCode": "POST_ItemCode", "Description": "POST_Description",
        "RTL_Qty": "POST_RTL", "WHLS_Qty": "POST_WHLS",
        "VIC_Qty": "POST_VIC", "TotalQty": "POST_TOTAL",
        "FirstFeedback": "POST_FirstFeedback", "FinalStatus": "POST_FinalStatus",
        "DeliveryGroup": "POST_DeliveryGroup", "PreviousCode": "POST_OldCodeRef",
    })


def build_comparison(pre_agg: pd.DataFrame, post_agg: pd.DataFrame) -> pd.DataFrame:
    """Outer-join pre/post on item code <-> match key, flag status, compute deltas."""
    comp = pd.merge(
        pre_agg, post_agg,
        left_on="ItemCode", right_on="MatchKey",
        how="outer", indicator=True,
    )

    def status(row):
        if row["_merge"] == "both":
            has_code_change = pd.notna(row["POST_OldCodeRef"]) and str(row["POST_OldCodeRef"]).strip() != ""
            return "CODE CHANGED" if has_code_change else "MATCHED"
        elif row["_merge"] == "left_only":
            return "PRE-ACTIVITIES ONLY (cancelled / not yet actioned)"
        else:
            return "POST-ACTIVITIES ONLY (new / bulk insertion)"

    comp["MatchStatus"] = comp.apply(status, axis=1)
    comp["ItemCode_Final"] = comp["ItemCode"].fillna(comp["POST_ItemCode"])

    for col in ["PRE_WHLS", "PRE_RTL", "PRE_VIC", "PRE_TOTAL",
                "POST_WHLS", "POST_RTL", "POST_VIC", "POST_TOTAL"]:
        comp[col] = comp[col].fillna(0)

    comp["Delta_TOTAL"] = comp["POST_TOTAL"] - comp["PRE_TOTAL"]
    comp["Delta_WHLS"] = comp["POST_WHLS"] - comp["PRE_WHLS"]
    comp["Delta_RTL"] = comp["POST_RTL"] - comp["PRE_RTL"]
    comp["Delta_VIC"] = comp["POST_VIC"] - comp["PRE_VIC"]
    comp["Status_Changed"] = comp["PRE_FinalStatus"].fillna("") != comp["POST_FinalStatus"].fillna("")

    return comp.drop(columns=["_merge", "MatchKey"])


if __name__ == "__main__":
    pre = load_extract("pre_activities.xlsx", "RECAP",
                        qty_cols=["WHLS_Qty", "RTL_Qty", "VIC_Qty", "TotalQty"])
    post = load_extract("post_activities.xlsx", "recap",
                         qty_cols=["RTL_Qty", "WHLS_Qty", "VIC_Qty", "TotalQty"])

    pre_agg = aggregate_pre_activities(pre)
    post_agg = aggregate_post_activities(post)
    comparison = build_comparison(pre_agg, post_agg)

    print(comparison["MatchStatus"].value_counts())
    comparison.to_excel("season_comparison.xlsx", index=False)
