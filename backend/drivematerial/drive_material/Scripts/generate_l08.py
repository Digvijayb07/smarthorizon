import os
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 108
TARGET_ROWS = 4000

TRANSACTIONS_PER_SCENARIO = 5
TARGET_SCENARIOS = TARGET_ROWS // TRANSACTIONS_PER_SCENARIO

OUTPUT_FILE = (
    "data/synthetic_L08_legitimate_destination_concentration.csv"
)

np.random.seed(SEED)


# ============================================================
# LOAD BASE DATASET
# ============================================================

df = pd.read_csv(
    "data/paysim_base_128k.csv"
)

print(f"Base dataset: {df.shape}")


# ============================================================
# REQUIRED COLUMNS
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
    "isFlaggedFraud",
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
# LEGITIMATE TRANSFERS
# ============================================================

transfer_seeds = legitimate[
    legitimate["type"] == "TRANSFER"
].copy()

print(
    f"Legitimate transfer seeds: "
    f"{len(transfer_seeds)}"
)


# ============================================================
# AMOUNT STATISTICS
# ============================================================

amount_25th = legitimate[
    "amount"
].quantile(0.25)

amount_median = legitimate[
    "amount"
].median()

amount_75th = legitimate[
    "amount"
].quantile(0.75)

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
# DESTINATION POOL
# ============================================================
#
# IMPORTANT:
# We do NOT require a destination to already have
# 5 historical transactions.
#
# The previous version did:
#
# destination_counts >= 5
#
# which resulted in zero candidates in your dataset.
#
# Instead, every legitimate transfer destination is eligible.
# ============================================================

eligible_destinations = (
    transfer_seeds[
        "nameDest"
    ]
    .dropna()
    .drop_duplicates()
    .tolist()
)

if len(eligible_destinations) == 0:
    raise ValueError(
        "No legitimate transfer destinations found."
    )

print(
    f"Eligible legitimate destinations: "
    f"{len(eligible_destinations)}"
)


# ============================================================
# SENDER POOL
# ============================================================

eligible_senders = (
    transfer_seeds[
        "nameOrig"
    ]
    .dropna()
    .drop_duplicates()
    .tolist()
)

print(
    f"Eligible legitimate senders: "
    f"{len(eligible_senders)}"
)

if len(eligible_senders) < TRANSACTIONS_PER_SCENARIO:
    raise ValueError(
        "Not enough legitimate senders."
    )


# ============================================================
# GENERATION
# ============================================================

synthetic_rows = []

scenario_number = 1


while scenario_number <= TARGET_SCENARIOS:

    # --------------------------------------------------------
    # Select ONE common destination
    # --------------------------------------------------------

    destination = np.random.choice(
        eligible_destinations
    )

    # --------------------------------------------------------
    # Select FIVE DIFFERENT legitimate senders
    # --------------------------------------------------------

    senders = np.random.choice(
        eligible_senders,
        size=TRANSACTIONS_PER_SCENARIO,
        replace=False
    )

    # Avoid sender being the same as destination.
    senders = [
        sender
        for sender in senders
        if sender != destination
    ]

    if len(senders) != TRANSACTIONS_PER_SCENARIO:
        continue

    # --------------------------------------------------------
    # Scenario ID
    # --------------------------------------------------------

    scenario_id = (
        f"L08_{scenario_number:06d}"
    )

    # --------------------------------------------------------
    # Starting step
    # --------------------------------------------------------

    start_step = np.random.randint(
        1,
        700
    )

    previous_step = start_step

    scenario_rows = []


    # ========================================================
    # CREATE FIVE TRANSACTIONS
    # ========================================================

    for position, sender in enumerate(
        senders,
        start=1
    ):

        # ----------------------------------------------------
        # Find a legitimate transaction from this sender
        # ----------------------------------------------------

        sender_history = transfer_seeds[
            transfer_seeds["nameOrig"] == sender
        ]

        if len(sender_history) == 0:
            scenario_rows = []
            break

        seed = sender_history.sample(
            n=1,
            random_state=np.random.randint(
                0,
                1_000_000
            )
        ).iloc[0]


        # ----------------------------------------------------
        # NORMAL TIME GAP
        # ----------------------------------------------------

        if position == 1:

            step_gap = 0

        else:

            step_gap = np.random.randint(
                5,
                31
            )

        current_step = (
            previous_step +
            step_gap
        )

        current_step = min(
            current_step,
            743
        )


        # ----------------------------------------------------
        # NORMAL LEGITIMATE AMOUNT
        # ----------------------------------------------------

        amount = np.random.uniform(
            amount_25th,
            amount_75th
        )

        amount = round(
            float(amount),
            2
        )


        # ----------------------------------------------------
        # SENDER BALANCE
        # ----------------------------------------------------

        old_balance_org = max(
            float(seed["oldbalanceOrg"]),
            amount * 2.0
        )

        # Keep balance usage low.
        max_allowed_amount = (
            old_balance_org * 0.15
        )

        amount = min(
            amount,
            max_allowed_amount
        )

        amount = round(
            amount,
            2
        )

        if amount <= 1:
            scenario_rows = []
            break

        new_balance_org = (
            old_balance_org -
            amount
        )


        # ----------------------------------------------------
        # DESTINATION BALANCE
        # ----------------------------------------------------

        old_balance_dest = max(
            float(seed["oldbalanceDest"]),
            amount * 7.0
        )
        new_balance_dest = (
            old_balance_dest +
            amount
        )


        # ----------------------------------------------------
        # CREATE ROW
        # ----------------------------------------------------

        row = seed.copy()

        row["step"] = current_step

        row["type"] = "TRANSFER"

        row["amount"] = round(
            amount,
            2
        )

        row["nameOrig"] = sender

        row["oldbalanceOrg"] = round(
            old_balance_org,
            2
        )

        row["newbalanceOrig"] = round(
            new_balance_org,
            2
        )

        # ----------------------------------------------------
        # SAME DESTINATION
        # ----------------------------------------------------

        row["nameDest"] = destination

        row["oldbalanceDest"] = round(
            old_balance_dest,
            2
        )

        row["newbalanceDest"] = round(
            new_balance_dest,
            2
        )


        # ----------------------------------------------------
        # LEGITIMATE LABELS
        # ----------------------------------------------------

        row["isFraud"] = 0

        row["isFlaggedFraud"] = 0


        # ----------------------------------------------------
        # SCENARIO METADATA
        # ----------------------------------------------------

        row["scenario_id"] = scenario_id

        row["scenario_type"] = (
            "LEGITIMATE_DESTINATION_CONCENTRATION"
        )

        row["severity"] = "NONE"

        row["is_legitimate_counterexample"] = 1

        row["concentration_position"] = position

        row["senders_in_scenario"] = (
            TRANSACTIONS_PER_SCENARIO
        )

        row["step_gap_from_previous"] = (
            step_gap
        )

        row["destination_balance_usage_ratio"] = round(
            amount /
            max(
                old_balance_dest + amount,
                1
            ),
            6
        )

        row["scenario_total_amount"] = 0.0

        scenario_rows.append(row)

        previous_step = current_step


    # ========================================================
    # ACCEPT ONLY COMPLETE SCENARIOS
    # ========================================================

    if len(scenario_rows) != TRANSACTIONS_PER_SCENARIO:
        continue


    # ========================================================
    # TOTAL SCENARIO AMOUNT
    # ========================================================

    scenario_total = sum(
        float(row["amount"])
        for row in scenario_rows
    )

    for row in scenario_rows:

        row["scenario_total_amount"] = round(
            scenario_total,
            2
        )


    # ========================================================
    # STORE SCENARIO
    # ========================================================

    synthetic_rows.extend(
        scenario_rows
    )

    scenario_number += 1


# ============================================================
# CREATE DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)


# ============================================================
# RECORD IDS
# ============================================================

synthetic["record_id"] = [
    f"L08_{i:06d}"
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
print("L08 VALIDATION")
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


# ============================================================
# TRANSACTIONS PER SCENARIO
# ============================================================

transactions_per_scenario = (
    synthetic
    .groupby("scenario_id")
    .size()
)

print(
    "Average transactions per scenario: "
    f"{transactions_per_scenario.mean():.1f}"
)

print(
    "Minimum transactions per scenario: "
    f"{transactions_per_scenario.min()}"
)

print(
    "Maximum transactions per scenario: "
    f"{transactions_per_scenario.max()}"
)


# ============================================================
# DESTINATION CONCENTRATION
# ============================================================

destinations_per_scenario = (
    synthetic
    .groupby("scenario_id")["nameDest"]
    .nunique()
)

print(
    "Average destinations per scenario: "
    f"{destinations_per_scenario.mean():.1f}"
)

print(
    "Maximum destinations per scenario: "
    f"{destinations_per_scenario.max()}"
)


# ============================================================
# SENDER DIVERSITY
# ============================================================

senders_per_scenario = (
    synthetic
    .groupby("scenario_id")["nameOrig"]
    .nunique()
)

print(
    "Average senders per scenario: "
    f"{senders_per_scenario.mean():.1f}"
)

print(
    "Minimum senders per scenario: "
    f"{senders_per_scenario.min()}"
)

print(
    "Maximum senders per scenario: "
    f"{senders_per_scenario.max()}"
)


# ============================================================
# STEP WINDOW
# ============================================================

step_windows = (
    synthetic
    .groupby("scenario_id")["step"]
    .agg(
        lambda x:
        x.max() - x.min()
    )
)

print(
    "Average scenario step window: "
    f"{step_windows.mean():.2f}"
)

print(
    "Maximum scenario step window: "
    f"{step_windows.max()}"
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
    f"Maximum amount: "
    f"{synthetic['amount'].max():.2f}"
)


# ============================================================
# BALANCE USAGE
# ============================================================

print(
    "Average destination balance usage: "
    f"{synthetic['destination_balance_usage_ratio'].mean() * 100:.2f} %"
)

print(
    "Maximum destination balance usage: "
    f"{synthetic['destination_balance_usage_ratio'].max() * 100:.2f} %"
)


# ============================================================
# ASSERTIONS
# ============================================================

assert len(synthetic) == TARGET_ROWS

assert synthetic[
    "isFraud"
].eq(0).all()

assert synthetic[
    "isFlaggedFraud"
].eq(0).all()

assert synthetic[
    "scenario_type"
].eq(
    "LEGITIMATE_DESTINATION_CONCENTRATION"
).all()

assert synthetic[
    "is_legitimate_counterexample"
].eq(1).all()

assert synthetic[
    "type"
].eq("TRANSFER").all()

assert synthetic[
    "scenario_id"
].nunique() == TARGET_SCENARIOS

assert (
    transactions_per_scenario ==
    TRANSACTIONS_PER_SCENARIO
).all()

# Exactly one common destination.
assert (
    destinations_per_scenario == 1
).all()

# Exactly five different senders.
assert (
    senders_per_scenario ==
    TRANSACTIONS_PER_SCENARIO
).all()

assert (
    synthetic["amount"] > 1
).all()

# No extreme destination balance drain.
assert (
    synthetic[
        "destination_balance_usage_ratio"
    ] < 0.20
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
    synthetic["scenario_id"].iloc[0]
)

sample_scenario = synthetic[
    synthetic["scenario_id"] ==
    first_scenario
]

print(
    sample_scenario[
        [
            "record_id",
            "step",
            "type",
            "amount",
            "nameOrig",
            "nameDest",
            "scenario_id",
            "scenario_type",
            "concentration_position",
            "senders_in_scenario",
            "step_gap_from_previous",
            "destination_balance_usage_ratio",
            "scenario_total_amount",
        ]
    ].to_string(index=False)
)