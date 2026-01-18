"""
Utilities for vintage construction, transition estimation, smoothing, and GLM helpers.
"""

import pandas as pd
import numpy as np
from typing import Dict

def load_sample_data(path: str = 'data/sample_vintage_data.csv') -> pd.DataFrame:
    """Load sample CSV into a DataFrame with parsed dates."""
    return pd.read_csv(path, parse_dates=['origination_date', 'observation_date'])

def compute_age_months(df: pd.DataFrame, orig_col: str = 'origination_date', obs_col: str = 'observation_date') -> pd.DataFrame:
    """Compute age in months between origination and observation date (integer months)."""
    df = df.copy()
    df['age_months'] = (df[obs_col].dt.to_period('M') - df[orig_col].dt.to_period('M')).apply(lambda x: x.n)
    return df

def build_vintage_pivot(df: pd.DataFrame, vintage_col: str = 'origination_date', age_col: str = 'age_months', state_col: str = 'delinquency_bucket', value_col: str = 'balance') -> pd.DataFrame:
    """Return vintage x age pivot table with balances per state."""
    if age_col not in df.columns:
        df = compute_age_months(df, orig_col=vintage_col, obs_col='observation_date')
    grouped = df.groupby([vintage_col, age_col, state_col])[value_col].sum().reset_index()
    pivot = grouped.pivot_table(index=[vintage_col, age_col], columns=state_col, values=value_col, fill_value=0)
    pivot.index.names = [vintage_col, age_col]
    pivot.columns.name = state_col
    return pivot

def compute_empirical_transitions(df: pd.DataFrame, id_col: str = 'loan_id', age_col: str = 'age_months', state_col: str = 'delinquency_bucket') -> Dict[int, pd.DataFrame]:
    """Compute empirical transition counts between state at age a and state at age a+1.

    Returns a dict: {age: DataFrame (from_state rows x to_state cols with counts)}
    Expects one row per (id, age).
    """
    if age_col not in df.columns:
        df = compute_age_months(df)
    df2 = df[[id_col, age_col, state_col]].copy().sort_values([id_col, age_col])
    df2['next_age'] = df2[age_col] + 1
    df_next = df2[[id_col, 'next_age', state_col]].rename(columns={'next_age': age_col, state_col: 'to_state'})
    df_next = df_next.set_index([id_col, age_col])
    df_curr = df2.set_index([id_col, age_col])
    joined = df_curr.join(df_next, how='inner').reset_index()
    trans = {}
    for age, grp in joined.groupby(age_col):
        table = pd.crosstab(grp[state_col], grp['to_state'])
        trans[int(age)] = table
    return trans

def row_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Row-normalize numeric dataframe to probabilities. Rows that sum to zero become zero-filled."""
    df = df.copy().astype(float)
    row_sums = df.sum(axis=1)
    nonzero = row_sums != 0
    df.loc[nonzero] = df.loc[nonzero].div(row_sums[nonzero], axis=0)
    df.loc[~nonzero] = 0
    return df

def laplace_smoothing(counts: pd.DataFrame, alpha: float = 1.0) -> pd.DataFrame:
    """Apply Laplace (add-alpha) smoothing to a contingency table of counts and return probabilities."""
    counts_s = counts + alpha
    probs = row_normalize(counts_s)
    return probs

def shrink_toward_pool(age_tables: Dict[int, pd.DataFrame], pool_weight: float = 0.5) -> Dict[int, pd.DataFrame]:
    """Shrink each age-specific probability matrix toward the pooled (across ages) probability matrix.

    pool is computed from concatenating counts across ages.
    pool_weight: 0..1 weight on the pooled estimate (higher -> more shrinkage)
    """
    # build pooled counts
    all_states = set()
    for tbl in age_tables.values():
        all_states.update(tbl.index.tolist())
        all_states.update(tbl.columns.tolist())
    all_states = sorted(all_states)
    pooled = pd.DataFrame(0, index=all_states, columns=all_states, dtype=float)
    for tbl in age_tables.values():
        tbl2 = tbl.reindex(index=all_states, columns=all_states, fill_value=0)
        pooled += tbl2
    pooled_probs = row_normalize(pooled)
    # compute prob tables per age
    out = {}
    for age, tbl in age_tables.items():
        tbl2 = tbl.reindex(index=all_states, columns=all_states, fill_value=0)
        probs = row_normalize(tbl2)
        shrunk = (1 - pool_weight) * probs + pool_weight * pooled_probs
        out[age] = shrunk
    return out

def ensure_probability_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure non-negativity and rows sum to 1 (if a row sums to zero, leave zeros)."""
    df = df.clip(lower=0)
    return row_normalize(df)