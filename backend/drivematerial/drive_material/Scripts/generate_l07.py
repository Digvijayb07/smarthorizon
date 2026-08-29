import os
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_L07_legitimate_dormant_reactivation.csv"

TARGET_ROWS = 3500
TARGET_SCENARIOS = 700

RANDOM_SEED = 107

np.random.seed(RANDOM_SEED)


# ============================================================
# LOAD BASE DATASET
# ============================================================

df = pd.read_csv(INPUT_FILE)

print(f"Base dataset: {df.shape}")


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "step",
    "type",
    "amount",
    "nameOrig",
    "nameDest",
    "oldbalanceOrg",
    "newbalanceOrig",
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
# AMOUNT STATISTICS
# ============================================================

amounts = legitimate["amount"]

amount_25th = amounts.quantile(0.25)
amount_median = amounts.quantile(0.50)
amount_75th = amounts.quantile(0.75)

print(
    f"Legitimate amount 25th percentile: "
    f"{amount_25th:.2f}"
)

print(
    f"Legitimate amount median: "
    f"{amount_median:.2f}"
)

print(
    f"Legitimate amount 75th percentile: "
    f"{amount_75th:.2f}"
)


# ============================================================
# FIND ACCOUNTS WITH HISTORICAL ACTIVITY
#
# We use legitimate accounts that have activity at different
# steps. This lets us construct a realistic "dormant period"
# followed by legitimate reactivation.
# ============================================================

account_activity = (
    legitimate
    .groupby("nameOrig")["step"]
    .agg(
        first_step="min",
        last_step="max",
        transaction_count="count"
    )
    .reset_index()
)


# We need accounts with enough historical activity.

candidate_accounts = account_activity[
    account_activity["transaction_count"] >= 2
].copy()


print(
    f"Candidate accounts: "
    f"{len(candidate_accounts)}"
)


if len(candidate_accounts) == 0:
    raise ValueError(
        "No suitable legitimate accounts found."
    )


# ============================================================
# GENERATION
#
# Each scenario contains 5 legitimate transactions after a
# long dormant period.
#
# Example:
#
# Previous activity
#       |
#       | 50-150 steps of inactivity
#       |
#       ↓
# TRANSFER
# PAYMENT
# TRANSFER
# PAYMENT
# CASH_OUT
#
# The account becomes active again, but behaviour remains
# normal and low-risk.
# ============================================================

synthetic_rows = []

scenario_counter = 1
record_counter = 1


while len(synthetic_rows) < TARGET_ROWS:

    # --------------------------------------------------------
    # Select an account
    # --------------------------------------------------------

    account = candidate_accounts.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    sender = account["nameOrig"]

    last_activity_step = int(
        account["last_step"]
    )


    # --------------------------------------------------------
    # Dormant period
    # --------------------------------------------------------

    dormant_gap = np.random.randint(
        50,
        151
    )

    first_reactivation_step = (
        last_activity_step +
        dormant_gap
    )


    # --------------------------------------------------------
    # Number of transactions
    #
    # 5 transactions per scenario gives:
    #
    # 700 scenarios × 5 = 3500 rows
    # --------------------------------------------------------

    transaction_count = 5


    # --------------------------------------------------------
    # Choose a reasonable starting balance
    #
    # We intentionally keep balance usage low.
    # --------------------------------------------------------

    historical_transactions = legitimate[
        legitimate["nameOrig"] == sender
    ]

    if len(historical_transactions) == 0:
        continue


    historical_seed = (
        historical_transactions
        .sample(
            n=1,
            random_state=np.random.randint(
                0,
                1_000_000
            )
        )
        .iloc[0]
    )


    starting_balance = max(
        float(historical_seed["oldbalanceOrg"]),
        amount_75th * 2
    )


    # --------------------------------------------------------
    # Scenario ID
    # --------------------------------------------------------

    scenario_id = (
        f"L07_{scenario_counter:06d}"
    )


    # --------------------------------------------------------
    # Generate 5 transactions
    # --------------------------------------------------------

    current_step = (
        first_reactivation_step
    )

    current_balance = starting_balance


    for position in range(
        1,
        transaction_count + 1
    ):

        # ----------------------------------------------------
        # Small normal step gap
        # ----------------------------------------------------

        if position == 1:

            step_gap = 0

        else:

            step_gap = np.random.randint(
                1,
                8
            )

            current_step += step_gap


        # ----------------------------------------------------
        # Select transaction type
        # ----------------------------------------------------

        transaction_type = np.random.choice(
            [
                "TRANSFER",
                "PAYMENT",
                "CASH_OUT"
            ],
            p=[
                0.50,
                0.35,
                0.15
            ]
        )


        # ----------------------------------------------------
        # Generate conservative amount
        #
        # Keep each transaction below roughly 10% of balance.
        # ----------------------------------------------------

        maximum_amount = min(
            amount_75th,
            current_balance * 0.10
        )

        minimum_amount = max(
            500.0,
            amount_25th * 0.25
        )

        if maximum_amount <= minimum_amount:

            maximum_amount = (
                minimum_amount * 1.5
            )


        transaction_amount = np.random.uniform(
            minimum_amount,
            maximum_amount
        )

        transaction_amount = round(
            transaction_amount,
            2
        )


        if transaction_amount <= 0:
            continue


        if transaction_amount >= current_balance:
            continue


        # ----------------------------------------------------
        # Sender balance
        # ----------------------------------------------------

        old_balance = current_balance

        new_balance = (
            old_balance -
            transaction_amount
        )


        # ----------------------------------------------------
        # Destination
        # ----------------------------------------------------

        if transaction_type == "CASH_OUT":

            destination = (
                f"CASHOUT_L07_{scenario_counter:06d}"
            )

            old_destination_balance = 0.0
            new_destination_balance = 0.0

        else:

            destination = (
                f"C_L07_{np.random.randint(100000000, 999999999)}"
            )

            old_destination_balance = 0.0

            new_destination_balance = (
                transaction_amount
            )


        # ----------------------------------------------------
        # Balance usage
        # ----------------------------------------------------

        balance_usage_ratio = (
            transaction_amount /
            max(old_balance, 1.0)
        )


        # ----------------------------------------------------
        # Create row
        # ----------------------------------------------------

        row = historical_seed.copy()

        row["record_id"] = (
            f"L07_{record_counter:06d}"
        )

        row["step"] = int(current_step)

        row["type"] = transaction_type

        row["amount"] = transaction_amount

        row["nameOrig"] = sender

        row["oldbalanceOrg"] = old_balance

        row["newbalanceOrig"] = new_balance

        row["nameDest"] = destination

        row["oldbalanceDest"] = (
            old_destination_balance
        )

        row["newbalanceDest"] = (
            new_destination_balance
        )

        row["isFraud"] = 0

        row["scenario_id"] = scenario_id

        row["scenario_type"] = (
            "LEGITIMATE_DORMANT_REACTIVATION"
        )

        row["severity"] = "NONE"

        row["is_legitimate_counterexample"] = 1

        row["previous_activity_step"] = (
            last_activity_step
        )

        row["dormant_gap"] = (
            dormant_gap
        )

        row["reactivation_position"] = (
            position
        )

        row["balance_usage_ratio"] = (
            balance_usage_ratio
        )

        row["scenario_transaction_count"] = (
            transaction_count
        )

        row["scenario_total_amount"] = 0.0

        synthetic_rows.append(row)

        record_counter += 1

        current_balance = new_balance


        # ----------------------------------------------------
        # Stop once we have exactly TARGET_ROWS
        # ----------------------------------------------------

        if len(synthetic_rows) >= TARGET_ROWS:
            break


    scenario_counter += 1


# ============================================================
# CREATE DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)


# ============================================================
# EXACT ROW COUNT
# ============================================================

synthetic = synthetic.iloc[
    :TARGET_ROWS
].copy()


# ============================================================
# CALCULATE SCENARIO TOTALS
# ============================================================

scenario_totals = (
    synthetic
    .groupby("scenario_id")["amount"]
    .sum()
)


synthetic["scenario_total_amount"] = (
    synthetic["scenario_id"]
    .map(scenario_totals)
)


# ============================================================
# REBUILD RECORD IDs
# ============================================================

synthetic["record_id"] = [
    f"L07_{i:06d}"
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
print("L07 VALIDATION")
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
    f"Unique accounts: "
    f"{pd.concat([synthetic['nameOrig'], synthetic['nameDest']]).nunique()}"
)

print(
    f"Unique scenarios: "
    f"{synthetic['scenario_id'].nunique()}"
)


scenario_sizes = (
    synthetic
    .groupby("scenario_id")
    .size()
)

print(
    f"Average transactions per scenario: "
    f"{scenario_sizes.mean():.1f}"
)

print(
    f"Minimum transactions per scenario: "
    f"{scenario_sizes.min()}"
)

print(
    f"Maximum transactions per scenario: "
    f"{scenario_sizes.max()}"
)


# ============================================================
# DORMANT GAP
# ============================================================

print(
    f"Average dormant gap: "
    f"{synthetic['dormant_gap'].mean():.2f} steps"
)

print(
    f"Minimum dormant gap: "
    f"{synthetic['dormant_gap'].min()} steps"
)

print(
    f"Maximum dormant gap: "
    f"{synthetic['dormant_gap'].max()} steps"
)


# ============================================================
# AMOUNT STATISTICS
# ============================================================

print(
    f"Average amount: "
    f"{synthetic['amount'].mean():.2f}"
)

print(
    f"Median amount: "
    f"{synthetic['amount'].median():.2f}"
)

print(
    f"Minimum amount: "
    f"{synthetic['amount'].min():.2f}"
)

print(
    f"Maximum amount: "
    f"{synthetic['amount'].max():.2f}"
)


# ============================================================
# BALANCE USAGE
# ============================================================

print(
    f"Average balance usage: "
    f"{synthetic['balance_usage_ratio'].mean() * 100:.2f} %"
)

print(
    f"Maximum balance usage: "
    f"{synthetic['balance_usage_ratio'].max() * 100:.2f} %"
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
    == "LEGITIMATE_DORMANT_REACTIVATION"
).all()

assert (
    synthetic["dormant_gap"] >= 50
).all()

assert (
    synthetic["dormant_gap"] <= 150
).all()

assert (
    synthetic["amount"] > 0
).all()

assert (
    synthetic["balance_usage_ratio"] < 0.15
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
    ][
        [
            "record_id",
            "step",
            "type",
            "amount",
            "nameOrig",
            "scenario_id",
            "scenario_type",
            "previous_activity_step",
            "dormant_gap",
            "reactivation_position",
            "balance_usage_ratio",
        ]
    ].to_string(index=False)
)