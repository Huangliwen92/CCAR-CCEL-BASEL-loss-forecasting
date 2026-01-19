# CCAR-9Q: Supervisory Stress Testing Framework

## Objective
This repository provides a quantitative framework for **Comprehensive Capital Analysis and Review (CCAR)**, specifically focusing on the 9-quarter planning horizon. 

The goal is to evaluate capital adequacy under **Supervisory Stress Scenarios** (Base, Adverse, and Severely Adverse). We model the "Peak-to-Trough" impact on capital by projecting:
* **PD/LGD/EAD:** Credit risk parameters.
* **NCOs:** Net Charge-Offs.
* **CET1 Ratio:** Common Equity Tier 1 capital health.

---

## The 9-Quarter Planning Horizon
The engine projects portfolio health from the **Jump-off date** through 9 subsequent quarters:
1. **Initial Shock (Q1-Q3):** Macroeconomic variables (Unemployment, GDP) deteriorate.
2. **Peak Stress (Q4-Q7):** Defaults and losses reach their maximum.
3. **Stabilization (Q8-Q9):** Assessment of capital recovery.

---

## Repository Structure

| Directory | Description |
| :--- | :--- |
| `src/models` | Satellite models linking macro variables to risk. |
| `src/projections` | The engine that "rolls" the portfolio forward. |
| `scenarios/` | Fed-provided CSV files for stress paths. |
| `notebooks/` | EDA and visualization of loss curves. |

---

## Methodology Reference

This framework is built to align with US regulatory expectations and standard financial engineering practices:

* **SR 11-7:** Guidance on **Model Risk Management**. This repository includes placeholders for effective challenge, backtesting, and sensitivity analysis.
* **12 CFR Part 225:** Adheres to the Federal Reserve regulations regarding **Capital Plan** requirements and annual stress testing cycles.
* **Vasicek Single Factor Model:** The core mathematical engine used for translating macroeconomic shocks into **Point-in-Time (PIT)** default probabilities.
ccar.load_scenario('scenarios/severely_adverse.csv')
results = ccar.run_projection('data/loan_tape.csv')

print(f"Minimum CET1: {results.min_cet1_ratio}%")
