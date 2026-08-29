import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S08_destination_concentration.csv"

TARGET_SCENARIOS = 700
TRANSACTIONS_PER_SCENARIO = 5

TARGET_ROWS = (
    TARGET_SCENARIOS *
    TRANSACTIONS_PER_SCENARIO
)

RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Base dataset:", df.shape)


# ============================================================
# LEGITIMATE DATA
# ============================================================

legit = df[
    df["isFraud"] == 0
].copy()

print(
    "Legitimate transactions:",
    len(legit)
)


# ============================================================
# LEGITIMATE TRANSFER SEEDS
# ============================================================

transfer_seeds = legit[
    (legit["type"] == "TRANSFER") &
    (legit["amount"] > 0) &
    (legit["nameOrig"].notna()) &
    (legit["oldbalanceOrg"] >= 0)
].copy()

print(
    "Legitimate transfer seeds:",
    len(transfer_seeds)
)

print(
    "Unique legitimate senders:",
    transfer_seeds[
        "nameOrig"
    ].nunique()
)


if len(transfer_seeds) < 100:

    raise ValueError(
        "Not enough legitimate transfer seeds."
    )


# ============================================================
# AMOUNT STATISTICS
# ============================================================

amount_75th = legit[
    "amount"
].quantile(0.75)

amount_95th = legit[
    "amount"
].quantile(0.95)

amount_median = legit[
    "amount"
].median()

print(
    "Legitimate amount 75th percentile:",
    round(amount_75th, 2)
)

print(
    "Legitimate amount 95th percentile:",
    round(amount_95th, 2)
)


# ============================================================
# GENERATE S08
# ============================================================

synthetic_rows = []


for scenario_number in range(
    1,
    TARGET_SCENARIOS + 1
):

    # --------------------------------------------------------
    # Select 5 DIFFERENT sender accounts
    # --------------------------------------------------------

    seeds = transfer_seeds.sample(
        n=TRANSACTIONS_PER_SCENARIO,
        replace=False,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    )

    senders = seeds[
        "nameOrig"
    ].tolist()

    # Make absolutely sure senders are unique.

    if len(set(senders)) != (
        TRANSACTIONS_PER_SCENARIO
    ):
        continue


    # --------------------------------------------------------
    # Create ONE common destination
    # --------------------------------------------------------

    destination = (
        "C_SYN_" +
        str(
            np.random.randint(
                100000000,
                999999999
            )
        )
    )


    # --------------------------------------------------------
    # Common scenario ID
    # --------------------------------------------------------

    scenario_id = (
        f"S08_{scenario_number:05d}"
    )


    # --------------------------------------------------------
    # Base step for the concentration window
    # --------------------------------------------------------

    base_step = np.random.randint(
        1,
        700
    )


    # ========================================================
    # CREATE 5 TRANSFERS TO SAME DESTINATION
    # ========================================================

    scenario_amounts = []

    for position, (_, seed) in enumerate(
        seeds.iterrows(),
        start=1
    ):

        sender = seed[
            "nameOrig"
        ]

        # ----------------------------------------------------
        # Transaction amount
        # ----------------------------------------------------

        seed_amount = float(
            seed["amount"]
        )

        base_amount = max(
            seed_amount,
            amount_median * 0.5
        )

        amount = (
            base_amount *
            np.random.uniform(
                0.65,
                1.20
            )
        )

        # Keep amounts below the high-value
        # threshold so S08 is about concentration.

        amount = min(
            amount,
            amount_95th * 0.90
        )

        amount = round(
            amount,
            2
        )

        if amount <= 1:
            continue


        # ----------------------------------------------------
        # Sender balance
        # ----------------------------------------------------

        old_balance = max(
            float(seed["oldbalanceOrg"]),
            amount * np.random.uniform(
                3.5,
                5.0
            ),
            50000
        )

        new_balance = (
            old_balance -
            amount
        )

        balance_usage = (
            amount /
            old_balance
        )

        # Prevent S03-style account draining.

        if balance_usage >= 0.30:
            continue


        # ----------------------------------------------------
        # Short time window
        # ----------------------------------------------------

        step = (
            base_step +
            np.random.randint(
                0,
                6
            )
        )


        # ----------------------------------------------------
        # Record ID
        # ----------------------------------------------------

        record_id = (
            f"S08_{len(synthetic_rows)+1:06d}"
        )


        # ----------------------------------------------------
        # Create row
        # ----------------------------------------------------

        row = {

            # -----------------------------
            # PaySim fields
            # -----------------------------

            "record_id":
                record_id,

            "step":
                step,

            "type":
                "TRANSFER",

            "amount":
                amount,

            "nameOrig":
                sender,

            "oldbalanceOrg":
                round(
                    old_balance,
                    2
                ),

            "newbalanceOrig":
                round(
                    new_balance,
                    2
                ),

            "nameDest":
                destination,

            "oldbalanceDest":
                0.0,

            "newbalanceDest":
                round(
                    amount,
                    2
                ),

            "isFraud":
                1,

            "isFlaggedFraud":
                0,


            # -----------------------------
            # Investigator metadata
            # -----------------------------

            "scenario_id":
                scenario_id,

            "scenario_type":
                "DESTINATION_CONCENTRATION",

            "fraud_reason":
                "Multiple independent accounts transferred funds to the same destination within a short time window",

            "severity":
                "HIGH",


            # -----------------------------
            # Concentration features
            # -----------------------------

            "chain_position":
                position,

            "senders_in_scenario":
                TRANSACTIONS_PER_SCENARIO,

            "common_destination":
                destination,

            "balance_usage_ratio":
                round(
                    balance_usage,
                    4
                )
        }

        synthetic_rows.append(
            row
        )


# ============================================================
# DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)


# ============================================================
# SAFETY CHECK
# ============================================================

if len(synthetic) != TARGET_ROWS:

    raise ValueError(
        f"Expected {TARGET_ROWS} rows, "
        f"but generated {len(synthetic)}."
    )


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("S08 VALIDATION")
print("=" * 60)

print(
    "Rows:",
    len(synthetic)
)

print(
    "Fraud labels:",
    synthetic[
        "isFraud"
    ].value_counts().to_dict()
)

print(
    "Transaction types:",
    synthetic[
        "type"
    ].value_counts().to_dict()
)

print(
    "Unique sender accounts:",
    synthetic[
        "nameOrig"
    ].nunique()
)

print(
    "Unique destinations:",
    synthetic[
        "nameDest"
    ].nunique()
)

print(
    "Unique scenarios:",
    synthetic[
        "scenario_id"
    ].nunique()
)

print(
    "Transactions per scenario:",
    round(
        len(synthetic) /
        synthetic["scenario_id"].nunique(),
        2
    )
)

# ------------------------------------------------------------
# Destination concentration
# ------------------------------------------------------------

destination_counts = (
    synthetic[
        "nameDest"
    ]
    .value_counts()
)

print(
    "Minimum transactions per destination:",
    destination_counts.min()
)

print(
    "Maximum transactions per destination:",
    destination_counts.max()
)

print(
    "Average transactions per destination:",
    round(
        destination_counts.mean(),
        2
    )
)


# ------------------------------------------------------------
# Time concentration
# ------------------------------------------------------------

scenario_steps = (
    synthetic
    .groupby("scenario_id")["step"]
    .agg(
        min_step="min",
        max_step="max"
    )
)

scenario_steps[
    "step_window"
] = (
    scenario_steps["max_step"] -
    scenario_steps["min_step"]
)

print(
    "Average scenario step window:",
    round(
        scenario_steps[
            "step_window"
        ].mean(),
        2
    )
)

print(
    "Maximum scenario step window:",
    scenario_steps[
        "step_window"
    ].max()
)


# ------------------------------------------------------------
# Amount
# ------------------------------------------------------------

print(
    "Average amount:",
    round(
        synthetic["amount"].mean(),
        2
    )
)

print(
    "Median amount:",
    round(
        synthetic["amount"].median(),
        2
    )
)

print(
    "Maximum amount:",
    round(
        synthetic["amount"].max(),
        2
    )
)


# ------------------------------------------------------------
# Combined destination amount
# ------------------------------------------------------------

scenario_totals = (
    synthetic
    .groupby("scenario_id")["amount"]
    .sum()
)

print(
    "Average combined scenario amount:",
    round(
        scenario_totals.mean(),
        2
    )
)

print(
    "Minimum combined scenario amount:",
    round(
        scenario_totals.min(),
        2
    )
)

print(
    "Maximum combined scenario amount:",
    round(
        scenario_totals.max(),
        2
    )
)


# ============================================================
# VALIDATION ASSERTIONS
# ============================================================

assert len(synthetic) == TARGET_ROWS

assert (
    synthetic["isFraud"] == 1
).all()

assert (
    synthetic["scenario_type"] ==
    "DESTINATION_CONCENTRATION"
).all()

assert (
    synthetic["scenario_id"]
    .nunique()
    == TARGET_SCENARIOS
)

assert (
    synthetic["type"] ==
    "TRANSFER"
).all()

# Every scenario has exactly 5 transactions.

scenario_counts = (
    synthetic
    .groupby("scenario_id")
    .size()
)

assert (
    scenario_counts ==
    TRANSACTIONS_PER_SCENARIO
).all()

# Every scenario has one destination.

dest_counts = (
    synthetic
    .groupby("scenario_id")["nameDest"]
    .nunique()
)

assert (
    dest_counts == 1
).all()

# Every scenario has 5 different senders.

sender_counts = (
    synthetic
    .groupby("scenario_id")["nameOrig"]
    .nunique()
)

assert (
    sender_counts ==
    TRANSACTIONS_PER_SCENARIO
).all()

# Transactions happen within a short window.

assert (
    scenario_steps["step_window"] <= 5
).all()

# No transaction should drain more than 30%.

assert (
    synthetic[
        "balance_usage_ratio"
    ] < 0.30
).all()

# Amount remains below legitimate 95th percentile.

assert (
    synthetic["amount"] <
    amount_95th
).all()


# ============================================================
# SAVE
# ============================================================

synthetic.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print(
    "Saved:",
    OUTPUT_FILE
)

print(
    "Final shape:",
    synthetic.shape
)

print()
print("Sample scenario:")

sample_scenario = (
    synthetic[
        "scenario_id"
    ].iloc[0]
)

print(
    synthetic[
        synthetic["scenario_id"] ==
        sample_scenario
    ][
        [
            "record_id",
            "step",
            "type",
            "amount",
            "nameOrig",
            "nameDest",
            "scenario_id",
            "chain_position",
            "senders_in_scenario",
            "balance_usage_ratio"
        ]
    ]
)