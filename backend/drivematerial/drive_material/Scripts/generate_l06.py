import os
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_L06_legitimate_transfer_cashout.csv"

TARGET_ROWS = 3500
TARGET_SCENARIOS = 1750

RANDOM_SEED = 106

np.random.seed(RANDOM_SEED)


# ============================================================
# LOAD BASE DATASET
# ============================================================

df = pd.read_csv(INPUT_FILE)

print(f"Base dataset: {df.shape}")


# ============================================================
# BASIC VALIDATION
# ============================================================

required_columns = [
    "step",
    "type",
    "amount",
    "nameOrig",
    "oldbalanceOrg",
    "newbalanceOrig",
    "nameDest",
    "oldbalanceDest",
    "newbalanceDest",
    "isFraud",
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# ============================================================
# LEGITIMATE TRANSACTIONS
# ============================================================

legitimate = df[
    df["isFraud"] == 0
].copy()

print(
    f"Legitimate transactions: "
    f"{len(legitimate)}"
)


# ============================================================
# STATISTICS
# ============================================================

legitimate_amounts = legitimate["amount"]

amount_25th = legitimate_amounts.quantile(0.25)
amount_50th = legitimate_amounts.quantile(0.50)
amount_75th = legitimate_amounts.quantile(0.75)
amount_95th = legitimate_amounts.quantile(0.95)

print(
    f"Legitimate amount 25th percentile: "
    f"{amount_25th:.2f}"
)

print(
    f"Legitimate amount median: "
    f"{amount_50th:.2f}"
)

print(
    f"Legitimate amount 75th percentile: "
    f"{amount_75th:.2f}"
)

print(
    f"Legitimate amount 95th percentile: "
    f"{amount_95th:.2f}"
)


# ============================================================
# SELECT LEGITIMATE TRANSFER SEEDS
# ============================================================

transfer_seeds = legitimate[
    (legitimate["type"] == "TRANSFER") &
    (legitimate["oldbalanceOrg"] > 0) &
    (legitimate["oldbalanceDest"] >= 0)
].copy()

print(
    f"Legitimate transfer seeds: "
    f"{len(transfer_seeds)}"
)


if len(transfer_seeds) == 0:
    raise ValueError(
        "No legitimate TRANSFER seeds available."
    )


# ============================================================
# GENERATION
#
# Each legitimate scenario contains:
#
#     TRANSFER
#         ↓
#     CASH_OUT
#
# The behaviour is intentionally NORMAL:
#
# - moderate transfer amount
# - reasonable balance usage
# - short time gap
# - no extreme amount
# - no extreme account draining
#
# This acts as a counterexample to S06.
# ============================================================

synthetic_rows = []

scenario_counter = 1
record_counter = 1


while len(synthetic_rows) < TARGET_ROWS:

    # --------------------------------------------------------
    # Select legitimate transfer seed
    # --------------------------------------------------------

    seed = transfer_seeds.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    sender = seed["nameOrig"]

    transfer_step = int(seed["step"])

    old_sender_balance = float(
        seed["oldbalanceOrg"]
    )

    old_destination_balance = float(
        seed["oldbalanceDest"]
    )

    original_destination = seed["nameDest"]


    # --------------------------------------------------------
    # Generate a NORMAL transfer amount
    #
    # Keep amount mostly around normal legitimate range.
    # --------------------------------------------------------

    upper_amount = min(
        amount_75th,
        old_sender_balance * 0.15
    )

    lower_amount = max(
        1000.0,
        amount_25th * 0.5
    )

    if upper_amount <= lower_amount:
        continue

    transfer_amount = np.random.uniform(
        lower_amount,
        upper_amount
    )

    transfer_amount = round(
        transfer_amount,
        2
    )


    if transfer_amount <= 0:
        continue


    # --------------------------------------------------------
    # Sender balance after transfer
    # --------------------------------------------------------

    new_sender_balance = (
        old_sender_balance -
        transfer_amount
    )

    if new_sender_balance < 0:
        continue


    # --------------------------------------------------------
    # Generate legitimate destination
    # --------------------------------------------------------

    destination = original_destination


    # --------------------------------------------------------
    # Destination balance after receiving transfer
    # --------------------------------------------------------

    destination_balance_after_transfer = (
        old_destination_balance +
        transfer_amount
    )


    # --------------------------------------------------------
    # CASH_OUT amount
    #
    # Only a portion of received money is cashed out.
    # This avoids making the scenario look like account draining.
    # --------------------------------------------------------

    cashout_ratio = np.random.uniform(
        0.20,
        0.65
    )

    cashout_amount = (
        transfer_amount *
        cashout_ratio
    )

    cashout_amount = round(
        cashout_amount,
        2
    )


    if cashout_amount <= 0:
        continue


    if cashout_amount >= destination_balance_after_transfer:
        continue


    # --------------------------------------------------------
    # CASH_OUT step
    #
    # Keep the two transactions close in time,
    # but not always immediately consecutive.
    # --------------------------------------------------------

    step_gap = np.random.randint(
        1,
        6
    )

    cashout_step = (
        transfer_step +
        step_gap
    )


    # --------------------------------------------------------
    # Destination balance after CASH_OUT
    # --------------------------------------------------------

    destination_balance_after_cashout = (
        destination_balance_after_transfer -
        cashout_amount
    )


    # --------------------------------------------------------
    # Balance usage
    # --------------------------------------------------------

    sender_usage_ratio = (
        transfer_amount /
        max(old_sender_balance, 1.0)
    )

    destination_usage_ratio = (
        cashout_amount /
        max(
            destination_balance_after_transfer,
            1.0
        )
    )


    # --------------------------------------------------------
    # Generate scenario ID
    # --------------------------------------------------------

    scenario_id = (
        f"L06_{scenario_counter:06d}"
    )


    # ========================================================
    # TRANSACTION 1 — TRANSFER
    # ========================================================

    transfer_row = seed.copy()

    transfer_row["record_id"] = (
        f"L06_{record_counter:06d}"
    )

    transfer_row["step"] = transfer_step

    transfer_row["type"] = "TRANSFER"

    transfer_row["amount"] = transfer_amount

    transfer_row["nameOrig"] = sender

    transfer_row["oldbalanceOrg"] = (
        old_sender_balance
    )

    transfer_row["newbalanceOrig"] = (
        new_sender_balance
    )

    transfer_row["nameDest"] = destination

    transfer_row["oldbalanceDest"] = (
        old_destination_balance
    )

    transfer_row["newbalanceDest"] = (
        destination_balance_after_transfer
    )

    transfer_row["isFraud"] = 0

    transfer_row["scenario_id"] = scenario_id

    transfer_row["scenario_type"] = (
        "LEGITIMATE_TRANSFER_CASHOUT"
    )

    transfer_row["severity"] = "NONE"

    transfer_row["is_legitimate_counterexample"] = 1

    transfer_row["chain_position"] = 1

    transfer_row["chain_role"] = "TRANSFER"

    transfer_row["step_gap_from_previous"] = 0

    transfer_row["cashout_ratio"] = (
        cashout_ratio
    )

    transfer_row["sender_balance_usage_ratio"] = (
        sender_usage_ratio
    )

    transfer_row["destination_balance_usage_ratio"] = (
        destination_usage_ratio
    )

    transfer_row["scenario_total_amount"] = (
        transfer_amount +
        cashout_amount
    )

    synthetic_rows.append(
        transfer_row
    )

    record_counter += 1


    # ========================================================
    # TRANSACTION 2 — CASH_OUT
    # ========================================================

    cashout_row = seed.copy()

    cashout_row["record_id"] = (
        f"L06_{record_counter:06d}"
    )

    cashout_row["step"] = cashout_step

    cashout_row["type"] = "CASH_OUT"

    cashout_row["amount"] = cashout_amount

    cashout_row["nameOrig"] = destination

    cashout_row["oldbalanceOrg"] = (
        destination_balance_after_transfer
    )

    cashout_row["newbalanceOrg"] = (
        destination_balance_after_cashout
    )

    # Cash-out destination is synthetic.
    cashout_row["nameDest"] = (
        f"CASHOUT_L06_{scenario_counter:06d}"
    )

    cashout_row["oldbalanceDest"] = 0.0

    cashout_row["newbalanceDest"] = 0.0

    cashout_row["isFraud"] = 0

    cashout_row["scenario_id"] = scenario_id

    cashout_row["scenario_type"] = (
        "LEGITIMATE_TRANSFER_CASHOUT"
    )

    cashout_row["severity"] = "NONE"

    cashout_row["is_legitimate_counterexample"] = 1

    cashout_row["chain_position"] = 2

    cashout_row["chain_role"] = "CASH_OUT"

    cashout_row["step_gap_from_previous"] = (
        step_gap
    )

    cashout_row["cashout_ratio"] = (
        cashout_ratio
    )

    cashout_row["sender_balance_usage_ratio"] = (
        sender_usage_ratio
    )

    cashout_row["destination_balance_usage_ratio"] = (
        destination_usage_ratio
    )

    cashout_row["scenario_total_amount"] = (
        transfer_amount +
        cashout_amount
    )

    synthetic_rows.append(
        cashout_row
    )

    record_counter += 1


    # --------------------------------------------------------
    # Next scenario
    # --------------------------------------------------------

    scenario_counter += 1


# ============================================================
# CREATE DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)


# ============================================================
# LIMIT EXACTLY TO TARGET ROWS
# ============================================================

synthetic = synthetic.iloc[
    :TARGET_ROWS
].copy()


# ============================================================
# RE-CREATE RECORD IDs
# ============================================================

synthetic["record_id"] = [
    f"L06_{i:06d}"
    for i in range(
        1,
        len(synthetic) + 1
    )
]


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("L06 VALIDATION")
print("=" * 60)

print(
    f"Rows: {len(synthetic)}"
)

print(
    f"Fraud labels: "
    f"{synthetic['isFraud'].value_counts().to_dict()}"
)

print(
    f"Transaction types: "
    f"{synthetic['type'].value_counts().to_dict()}"
)

print(
    f"Rows: {len(synthetic)}"
)

print(
    f"Fraud labels: "
    f"{synthetic['isFraud'].value_counts().to_dict()}"
)

print(
    f"Transaction types: "
    f"{synthetic['type'].value_counts().to_dict()}"
)

print(
    f"Unique accounts: "
    f"{pd.concat([synthetic['nameOrig'], synthetic['nameDest']]).nunique()}"
)

print(
    f"Unique scenarios: "
    f"{synthetic['scenario_id'].nunique()}"
)

print(
    f"Unique scenarios: "
    f"{synthetic['scenario_id'].nunique()}"
)


transactions_per_scenario = (
    synthetic
    .groupby("scenario_id")
    .size()
)

print(
    f"Average transactions per scenario: "
    f"{transactions_per_scenario.mean():.1f}"
)

print(
    f"Minimum transactions per scenario: "
    f"{transactions_per_scenario.min()}"
)

print(
    f"Maximum transactions per scenario: "
    f"{transactions_per_scenario.max()}"
)


print(
    f"Average individual amount: "
    f"{synthetic['amount'].mean():.2f}"
)

print(
    f"Median individual amount: "
    f"{synthetic['amount'].median():.2f}"
)

print(
    f"Maximum individual amount: "
    f"{synthetic['amount'].max():.2f}"
)


scenario_totals = (
    synthetic
    .groupby("scenario_id")["amount"]
    .sum()
)

print(
    f"Average combined scenario amount: "
    f"{scenario_totals.mean():.2f}"
)

print(
    f"Minimum combined scenario amount: "
    f"{scenario_totals.min():.2f}"
)

print(
    f"Maximum combined scenario amount: "
    f"{scenario_totals.max():.2f}"
)


print(
    f"Average cash-out ratio: "
    f"{synthetic['cashout_ratio'].mean() * 100:.2f} %"
)

print(
    f"Minimum cash-out ratio: "
    f"{synthetic['cashout_ratio'].min() * 100:.2f} %"
)

print(
    f"Maximum cash-out ratio: "
    f"{synthetic['cashout_ratio'].max() * 100:.2f} %"
)


print(
    f"Average sender balance usage: "
    f"{synthetic['sender_balance_usage_ratio'].mean() * 100:.2f} %"
)


# ============================================================
# ASSERTIONS
# ============================================================

assert len(synthetic) == TARGET_ROWS

assert (
    synthetic["isFraud"] == 0
).all()

assert (
    synthetic["is_legitimate_counterexample"] == 1
).all()

assert (
    synthetic["scenario_type"]
    == "LEGITIMATE_TRANSFER_CASHOUT"
).all()

assert (
    synthetic["type"]
    .isin(["TRANSFER", "CASH_OUT"])
).all()

assert (
    synthetic["amount"] > 0
).all()

assert (
    synthetic["cashout_ratio"] >= 0.20
).all()

assert (
    synthetic["cashout_ratio"] <= 0.65
).all()

assert (
    synthetic["sender_balance_usage_ratio"] < 0.20
).all()


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    "data",
    exist_ok=True
)

synthetic.to_csv(
    OUTPUT_FILE,
    index=False
)


print()
print(
    f"Saved: {OUTPUT_FILE}"
)

print(
    f"Final shape: {synthetic.shape}"
)


# ============================================================
# SAMPLE
# ============================================================

print()
print("Sample scenario:")

first_scenario = (
    synthetic["scenario_id"]
    .iloc[0]
)

print(
    synthetic[
        synthetic["scenario_id"]
        == first_scenario
    ].to_string(index=False)
)