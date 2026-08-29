import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_L03_legitimate_high_value_history.csv"

TARGET_ROWS = 4000
SCENARIOS = 800
TRANSACTIONS_PER_SCENARIO = 5

np.random.seed(103)


# ============================================================
# LOAD BASE DATASET
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Base dataset:", df.shape)

# Only legitimate transactions
legitimate = df[df["isFraud"] == 0].copy()

print("Legitimate transactions:", len(legitimate))


# ============================================================
# SELECT LEGITIMATE TRANSFER SEEDS
# ============================================================

transfers = legitimate[
    legitimate["type"] == "TRANSFER"
].copy()

print("Legitimate transfer seeds:", len(transfers))

if len(transfers) == 0:
    raise ValueError("No legitimate TRANSFER transactions found.")


# ============================================================
# STATISTICS
# ============================================================

amount_75th = transfers["amount"].quantile(0.75)
amount_95th = transfers["amount"].quantile(0.95)
amount_99th = transfers["amount"].quantile(0.99)

print("Legitimate transfer 75th percentile:", round(amount_75th, 2))
print("Legitimate transfer 95th percentile:", round(amount_95th, 2))
print("Legitimate transfer 99th percentile:", round(amount_99th, 2))


# ============================================================
# HIGH-VALUE LEGITIMATE SEEDS
# ============================================================

high_value_seeds = transfers[
    transfers["amount"] >= amount_95th
].copy()

print("High-value legitimate seeds:", len(high_value_seeds))

if len(high_value_seeds) == 0:
    raise ValueError("No high-value legitimate seeds found.")


# ============================================================
# GENERATE SCENARIOS
# ============================================================

synthetic_rows = []

for scenario_number in range(1, SCENARIOS + 1):

    # --------------------------------------------------------
    # Select one legitimate high-value transaction
    # --------------------------------------------------------

    seed = high_value_seeds.sample(
        n=1,
        random_state=np.random.randint(0, 1_000_000)
    ).iloc[0]

    sender = seed["nameOrig"]

    original_step = int(seed["step"])

    original_amount = float(seed["amount"])

    old_balance = float(seed["oldbalanceOrg"])

    # --------------------------------------------------------
    # Create normal historical pattern
    #
    # Transactions are separated by realistic time gaps.
    # --------------------------------------------------------

    step_offsets = np.cumsum(
        np.random.randint(
            15,
            61,
            size=TRANSACTIONS_PER_SCENARIO
        )
    )

    # Keep scenario inside PaySim step range
    if original_step + step_offsets[-1] > 744:
        original_step = max(
            1,
            744 - int(step_offsets[-1])
        )

    # --------------------------------------------------------
    # Normal transaction amounts
    #
    # One transaction is high-value.
    # Other transactions remain moderate.
    # --------------------------------------------------------

    amounts = []

    for position in range(TRANSACTIONS_PER_SCENARIO):

        if position == TRANSACTIONS_PER_SCENARIO - 1:

            # Legitimate high-value transaction
            amount = original_amount * np.random.uniform(
                0.95,
                1.05
            )

            amount = min(
                amount,
                amount_99th
            )

        else:

            # Normal historical transactions
            amount = np.random.uniform(
                amount_75th * 0.30,
                amount_75th * 0.90
            )

        amounts.append(round(amount, 2))

    # --------------------------------------------------------
    # Generate transactions
    # --------------------------------------------------------

    remaining_balance = max(
        old_balance,
        sum(amounts) * 1.5
    )

    for position in range(TRANSACTIONS_PER_SCENARIO):

        amount = amounts[position]

        # Make sure account can afford transaction
        amount = min(
            amount,
            remaining_balance * 0.30
        )

        if amount <= 1:
            continue

        step = (
            original_step +
            int(step_offsets[position])
        )

        old_bal = remaining_balance
        new_bal = old_bal - amount

        # Use legitimate-style destination
        destination = seed["nameDest"]

        row = {

            # ------------------------------------------------
            # Original PaySim fields
            # ------------------------------------------------

            "record_id":
                f"L03_{len(synthetic_rows)+1:06d}",

            "step":
                step,

            "type":
                "TRANSFER",

            "amount":
                round(amount, 2),

            "nameOrig":
                sender,

            "oldbalanceOrg":
                round(old_bal, 2),

            "newbalanceOrig":
                round(new_bal, 2),

            "nameDest":
                destination,

            "oldbalanceDest":
                0.0,

            "newbalanceDest":
                round(amount, 2),

            "isFraud":
                0,

            "isFlaggedFraud":
                0,

            # ------------------------------------------------
            # Investigator metadata
            # ------------------------------------------------

            "scenario_id":
                f"L03_{scenario_number:05d}",

            "scenario_type":
                "LEGITIMATE_HIGH_VALUE_HISTORY",

            "fraud_reason":
                "High-value transaction consistent with normal historical account behavior",

            "severity":
                "NONE",

            "is_legitimate_counterexample":
                1,

            "transaction_position":
                position + 1,

            "transaction_count_in_scenario":
                TRANSACTIONS_PER_SCENARIO,

            "historical_pattern":
                "NORMAL",

            "balance_usage_ratio":
                round(
                    amount / max(old_bal, 1),
                    4
                )
        }

        synthetic_rows.append(row)

        remaining_balance = new_bal

        if len(synthetic_rows) >= TARGET_ROWS:
            break

    if len(synthetic_rows) >= TARGET_ROWS:
        break


# ============================================================
# DATAFRAME
# ============================================================

synthetic = pd.DataFrame(synthetic_rows)


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("L03 VALIDATION")
print("=" * 60)

print("Rows:", len(synthetic))

print(
    "Fraud labels:",
    synthetic["isFraud"].value_counts().to_dict()
)

print(
    "Transaction types:",
    synthetic["type"].value_counts().to_dict()
)

print(
    "Unique accounts:",
    synthetic["nameOrig"].nunique()
)

print(
    "Unique scenarios:",
    synthetic["scenario_id"].nunique()
)

print(
    "Average amount:",
    round(synthetic["amount"].mean(), 2)
)

print(
    "Median amount:",
    round(synthetic["amount"].median(), 2)
)

print(
    "Minimum amount:",
    round(synthetic["amount"].min(), 2)
)

print(
    "Maximum amount:",
    round(synthetic["amount"].max(), 2)
)

print(
    "Percentage above legitimate 95th percentile:",
    round(
        (
            synthetic["amount"] >= amount_95th
        ).mean() * 100,
        2
    ),
    "%"
)

print(
    "Average balance usage:",
    round(
        synthetic["balance_usage_ratio"].mean() * 100,
        2
    ),
    "%"
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
    == "LEGITIMATE_HIGH_VALUE_HISTORY"
).all()

assert (
    synthetic["balance_usage_ratio"] < 1
).all()


# ============================================================
# SAVE
# ============================================================

synthetic.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved:", OUTPUT_FILE)
print("Final shape:", synthetic.shape)

print()
print("Sample:")
print(
    synthetic[
        [
            "record_id",
            "step",
            "type",
            "amount",
            "nameOrig",
            "nameDest",
            "isFraud",
            "scenario_id",
            "scenario_type",
            "historical_pattern",
            "balance_usage_ratio"
        ]
    ].head(10)
)