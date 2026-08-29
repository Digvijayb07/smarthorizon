# ============================================================
# L10 - LEGITIMATE FUND DISPERSION
# ============================================================
#
# Legitimate counterpart of S10 FUND DISPERSION.
#
# Pattern:
#
#              -> B
#             /
#            -> C
#           /
# A -------> D
#           \
#            -> E
#             \
#              -> F
#
# One legitimate sender distributes funds to multiple
# destinations.
#
# This is NOT fraud.
#
# Purpose:
# Teach the model that sending money to many destinations
# does not automatically mean suspicious fund dispersion.
# ============================================================

import os
import numpy as np
import pandas as pd


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

BASE_FILE = "data/paysim_base_128k.csv"

OUTPUT_FILE = (
    "data/synthetic_L10_legitimate_fund_dispersion.csv"
)

TARGET_ROWS = 3500

TRANSACTIONS_PER_SCENARIO = 5

TARGET_SCENARIOS = (
    TARGET_ROWS // TRANSACTIONS_PER_SCENARIO
)

SEED = 1010

np.random.seed(SEED)


# ------------------------------------------------------------
# LOAD BASE DATASET
# ------------------------------------------------------------

df = pd.read_csv(BASE_FILE)

print(f"Base dataset: {df.shape}")

df.columns = df.columns.str.strip()


# ------------------------------------------------------------
# REQUIRED COLUMNS
# ------------------------------------------------------------

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
    col
    for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# ------------------------------------------------------------
# LEGITIMATE TRANSACTIONS
# ------------------------------------------------------------

legitimate = df[
    df["isFraud"] == 0
].copy()

print(
    f"Legitimate transactions: "
    f"{len(legitimate)}"
)


# ------------------------------------------------------------
# LEGITIMATE TRANSFER SEEDS
# ------------------------------------------------------------

transfer_seeds = legitimate[
    legitimate["type"].astype(str) == "TRANSFER"
].copy()

if len(transfer_seeds) == 0:
    raise ValueError(
        "No legitimate TRANSFER transactions found."
    )

print(
    f"Legitimate transfer seeds: "
    f"{len(transfer_seeds)}"
)


# ------------------------------------------------------------
# AMOUNT STATISTICS
# ------------------------------------------------------------

amount_25th = float(
    legitimate["amount"].quantile(0.25)
)

amount_median = float(
    legitimate["amount"].median()
)

amount_75th = float(
    legitimate["amount"].quantile(0.75)
)

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


# ------------------------------------------------------------
# GENERATE SCENARIOS
# ------------------------------------------------------------

synthetic_rows = []

record_counter = 1


for scenario_number in range(
    1,
    TARGET_SCENARIOS + 1
):

    scenario_id = (
        f"L10_{scenario_number:06d}"
    )

    # --------------------------------------------------------
    # CREATE ONE SENDER
    # --------------------------------------------------------

    sender = (
        f"LD{scenario_number:06d}_S"
    )

    # --------------------------------------------------------
    # CREATE FIVE DESTINATIONS
    # --------------------------------------------------------

    destinations = [
        f"LD{scenario_number:06d}_D{i}"
        for i in range(1, 6)
    ]

    # --------------------------------------------------------
    # SCENARIO START
    # --------------------------------------------------------

    scenario_start_step = int(
        np.random.randint(
            10,
            900
        )
    )

    # --------------------------------------------------------
    # NORMAL STEP GAPS
    #
    # Legitimate dispersion happens over a small,
    # realistic time window.
    # --------------------------------------------------------

    steps = []

    current_step = scenario_start_step

    for position in range(
        TRANSACTIONS_PER_SCENARIO
    ):

        if position > 0:

            gap = int(
                np.random.randint(
                    1,
                    4
                )
            )

            current_step += gap

        steps.append(current_step)

    # --------------------------------------------------------
    # SENDER BALANCE
    #
    # Keep enough balance so the total dispersion uses only
    # a small percentage of the sender's funds.
    # --------------------------------------------------------

    sender_balance = np.random.uniform(
        amount_75th * 5,
        amount_75th * 10
    )

    sender_balance = round(
        sender_balance,
        2
    )

    # --------------------------------------------------------
    # GENERATE FIVE LEGITIMATE AMOUNTS
    # --------------------------------------------------------

    amounts = []

    for position in range(
        TRANSACTIONS_PER_SCENARIO
    ):

        # Normal legitimate transaction amount
        amount = np.random.uniform(
            max(
                100.0,
                amount_25th * 0.75
            ),
            min(
                amount_75th * 0.75,
                amount_median * 1.5
            )
        )

        # Slight natural variation
        amount *= np.random.uniform(
            0.85,
            1.15
        )

        amount = round(
            amount,
            2
        )

        amounts.append(amount)

    # --------------------------------------------------------
    # Prevent total amount from using too much balance
    # --------------------------------------------------------

    total_amount = sum(amounts)

    max_allowed_total = (
        sender_balance * 0.15
    )

    if total_amount > max_allowed_total:

        scale = (
            max_allowed_total /
            total_amount
        )

        amounts = [
            round(
                amount * scale,
                2
            )
            for amount in amounts
        ]

    # Ensure no amount becomes zero
    amounts = [
        max(
            1.0,
            amount
        )
        for amount in amounts
    ]

    scenario_total_amount = round(
        sum(amounts),
        2
    )

    # --------------------------------------------------------
    # CREATE TRANSACTIONS
    # --------------------------------------------------------

    remaining_sender_balance = (
        sender_balance
    )

    for position in range(
        TRANSACTIONS_PER_SCENARIO
    ):

        destination = destinations[position]

        amount = amounts[position]

        old_balance_org = (
            remaining_sender_balance
        )

        new_balance_org = (
            old_balance_org - amount
        )

        # ----------------------------------------------------
        # Destination starts with a normal balance.
        # ----------------------------------------------------

        old_balance_dest = round(
            np.random.uniform(
                amount_75th * 1.5,
                amount_75th * 5
            ),
            2
        )

        new_balance_dest = (
            old_balance_dest + amount
        )

        # ----------------------------------------------------
        # Balance usage
        # ----------------------------------------------------

        sender_balance_usage = (
            amount /
            old_balance_org
        )

        destination_balance_usage = (
            amount /
            max(
                old_balance_dest,
                1
            )
        )

        # ----------------------------------------------------
        # Step gap
        # ----------------------------------------------------

        if position == 0:

            step_gap = 0

        else:

            step_gap = (
                steps[position]
                - steps[position - 1]
            )

        # ----------------------------------------------------
        # Create row
        # ----------------------------------------------------

        row = {

            "record_id":
                f"L10_{record_counter:06d}",

            "step":
                steps[position],

            "type":
                "TRANSFER",

            "amount":
                round(amount, 2),

            "nameOrig":
                sender,

            "oldbalanceOrg":
                round(
                    old_balance_org,
                    2
                ),

            "newbalanceOrig":
                round(
                    new_balance_org,
                    2
                ),

            "nameDest":
                destination,

            "oldbalanceDest":
                round(
                    old_balance_dest,
                    2
                ),

            "newbalanceDest":
                round(
                    new_balance_dest,
                    2
                ),

            "isFraud":
                0,

            "isFlaggedFraud":
                0,

            "scenario_id":
                scenario_id,

            "scenario_type":
                "LEGITIMATE_FUND_DISPERSION",

            "severity":
                "NONE",

            "is_legitimate_counterexample":
                1,

            "dispersion_position":
                position + 1,

            "destinations_in_scenario":
                TRANSACTIONS_PER_SCENARIO,

            "step_gap_from_previous":
                step_gap,

            "scenario_step_window":
                steps[-1] - steps[0],

            "scenario_total_amount":
                scenario_total_amount,

            "sender_balance_usage_ratio":
                round(
                    sender_balance_usage,
                    6
                ),

            "destination_balance_usage_ratio":
                round(
                    destination_balance_usage,
                    6
                ),

            "dispersion_pattern":
                "ONE_TO_MANY",

            "historical_pattern":
                "NORMAL",
        }

        synthetic_rows.append(row)

        remaining_sender_balance = (
            new_balance_org
        )

        record_counter += 1


# ------------------------------------------------------------
# DATAFRAME
# ------------------------------------------------------------

synthetic = pd.DataFrame(
    synthetic_rows
)


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

print()
print("=" * 60)
print("L10 VALIDATION")
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
    f"Unique sender accounts: "
    f"{synthetic['nameOrig'].nunique()}"
)

print(
    f"Unique destinations: "
    f"{synthetic['nameDest'].nunique()}"
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


# ------------------------------------------------------------
# DESTINATION VALIDATION
# ------------------------------------------------------------

destinations_per_scenario = (
    synthetic
    .groupby("scenario_id")["nameDest"]
    .nunique()
)

print(
    f"Average destinations per scenario: "
    f"{destinations_per_scenario.mean():.1f}"
)

print(
    f"Minimum destinations per scenario: "
    f"{destinations_per_scenario.min()}"
)

print(
    f"Maximum destinations per scenario: "
    f"{destinations_per_scenario.max()}"
)


# ------------------------------------------------------------
# SENDER VALIDATION
# ------------------------------------------------------------

senders_per_scenario = (
    synthetic
    .groupby("scenario_id")["nameOrig"]
    .nunique()
)

print(
    f"Average senders per scenario: "
    f"{senders_per_scenario.mean():.1f}"
)

print(
    f"Minimum senders per scenario: "
    f"{senders_per_scenario.min()}"
)

print(
    f"Maximum senders per scenario: "
    f"{senders_per_scenario.max()}"
)


# ------------------------------------------------------------
# AMOUNT VALIDATION
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# SCENARIO TOTAL AMOUNT
# ------------------------------------------------------------

scenario_totals = (
    synthetic
    .groupby("scenario_id")[
        "scenario_total_amount"
    ]
    .first()
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


# ------------------------------------------------------------
# STEP WINDOW
# ------------------------------------------------------------

scenario_windows = (
    synthetic
    .groupby("scenario_id")["step"]
    .agg(
        lambda x: x.max() - x.min()
    )
)

print(
    f"Average scenario step window: "
    f"{scenario_windows.mean():.2f}"
)

print(
    f"Maximum scenario step window: "
    f"{scenario_windows.max()}"
)


# ------------------------------------------------------------
# BALANCE USAGE
# ------------------------------------------------------------

print(
    f"Average sender balance usage: "
    f"{synthetic['sender_balance_usage_ratio'].mean() * 100:.2f} %"
)

print(
    f"Maximum sender balance usage: "
    f"{synthetic['sender_balance_usage_ratio'].max() * 100:.2f} %"
)


# ------------------------------------------------------------
# ASSERTIONS
# ------------------------------------------------------------

assert len(synthetic) == TARGET_ROWS

assert synthetic[
    "isFraud"
].eq(0).all()

assert synthetic[
    "is_legitimate_counterexample"
].eq(1).all()

assert synthetic[
    "scenario_type"
].eq(
    "LEGITIMATE_FUND_DISPERSION"
).all()

assert synthetic[
    "type"
].eq("TRANSFER").all()

assert (
    synthetic["scenario_id"].nunique()
    == TARGET_SCENARIOS
)

assert (
    transactions_per_scenario.min()
    == TRANSACTIONS_PER_SCENARIO
)

assert (
    transactions_per_scenario.max()
    == TRANSACTIONS_PER_SCENARIO
)

assert (
    destinations_per_scenario.min()
    == TRANSACTIONS_PER_SCENARIO
)

assert (
    destinations_per_scenario.max()
    == TRANSACTIONS_PER_SCENARIO
)

assert (
    senders_per_scenario.min()
    == 1
)

assert (
    senders_per_scenario.max()
    == 1
)

assert (
    synthetic["amount"] > 0
).all()

assert (
    synthetic[
        "sender_balance_usage_ratio"
    ] < 1
).all()


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# SAMPLE
# ------------------------------------------------------------

print()
print("Sample scenario:")

print(
    synthetic[
        [
            "record_id",
            "step",
            "type",
            "amount",
            "nameOrig",
            "nameDest",
            "scenario_id",
            "scenario_type",
            "dispersion_position",
            "destinations_in_scenario",
            "step_gap_from_previous",
            "sender_balance_usage_ratio",
        ]
    ]
    .head(10)
    .to_string(index=False)
)