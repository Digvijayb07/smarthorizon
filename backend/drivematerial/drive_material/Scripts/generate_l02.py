import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_L02_legitimate_repeated_transfers.csv"

TARGET_SCENARIOS = 800
TRANSACTIONS_PER_SCENARIO = 5

TARGET_ROWS = (
    TARGET_SCENARIOS *
    TRANSACTIONS_PER_SCENARIO
)

RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


# ============================================================
# LOAD BASE DATASET
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Base dataset:", df.shape)


# ============================================================
# LEGITIMATE TRANSFERS
# ============================================================

legit = df[
    df["isFraud"] == 0
].copy()

print(
    "Legitimate transactions:",
    len(legit)
)


transfer_seeds = legit[
    (legit["type"] == "TRANSFER") &
    (legit["amount"] > 0) &
    (legit["nameOrig"].notna()) &
    (legit["nameDest"].notna())
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


if transfer_seeds[
    "nameOrig"
].nunique() < TARGET_SCENARIOS:

    raise ValueError(
        "Not enough legitimate sender accounts."
    )


# ============================================================
# AMOUNT STATISTICS
# ============================================================

amount_25th = legit[
    "amount"
].quantile(0.25)

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
    "Legitimate amount 25th percentile:",
    round(amount_25th, 2)
)

print(
    "Legitimate amount 75th percentile:",
    round(amount_75th, 2)
)

print(
    "Legitimate amount 95th percentile:",
    round(amount_95th, 2)
)


# ============================================================
# GENERATE L02
# ============================================================

synthetic_rows = []


for scenario_number in range(
    1,
    TARGET_SCENARIOS + 1
):

    # --------------------------------------------------------
    # Select one legitimate sender
    # --------------------------------------------------------

    seed = transfer_seeds.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    sender = seed[
        "nameOrig"
    ]


    # --------------------------------------------------------
    # Select a normal legitimate destination
    # --------------------------------------------------------

    destination_seed = transfer_seeds.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    destination = destination_seed[
        "nameDest"
    ]


    # Avoid same sender and destination.

    if sender == destination:

        continue


    # --------------------------------------------------------
    # Scenario ID
    # --------------------------------------------------------

    scenario_id = (
        f"L02_{scenario_number:05d}"
    )


    # --------------------------------------------------------
    # Normal time spacing
    #
    # Unlike S01, transactions are separated
    # by a meaningful time interval.
    # --------------------------------------------------------

    base_step = np.random.randint(
        1,
        500
    )


    step_gaps = np.random.randint(
        10,
        51,
        size=TRANSACTIONS_PER_SCENARIO
    )


    # --------------------------------------------------------
    # Sender starting balance
    # --------------------------------------------------------

    seed_balance = float(
        seed["oldbalanceOrg"]
    )

    remaining_balance = max(
        seed_balance,
        50000
    )


    # --------------------------------------------------------
    # Generate five repeated transfers
    # --------------------------------------------------------

    for position in range(
        TRANSACTIONS_PER_SCENARIO
    ):

        # ----------------------------------------------------
        # Amount
        # ----------------------------------------------------

        seed_amount = float(
            seed["amount"]
        )

        base_amount = max(
            seed_amount,
            amount_median * 0.30
        )

        amount = (
            base_amount *
            np.random.uniform(
                0.70,
                1.10
            )
        )

        # Keep amounts in a normal legitimate range.

        amount = min(
            amount,
            amount_75th * 1.20
        )

        # Make sure account can afford it.

        amount = min(
            amount,
            remaining_balance * 0.15
        )

        amount = round(
            amount,
            2
        )

        if amount <= 1:
            continue


        # ----------------------------------------------------
        # Step
        # ----------------------------------------------------

        if position == 0:

            step = base_step

        else:

            step = (
                step +
                int(step_gaps[position])
            )


        # ----------------------------------------------------
        # Balance update
        # ----------------------------------------------------

        old_balance = remaining_balance

        new_balance = (
            old_balance -
            amount
        )

        balance_usage = (
            amount /
            old_balance
        )


        # ----------------------------------------------------
        # Record ID
        # ----------------------------------------------------

        record_id = (
            f"L02_{len(synthetic_rows)+1:06d}"
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
                0,

            "isFlaggedFraud":
                0,


            # -----------------------------
            # Investigator metadata
            # -----------------------------

            "scenario_id":
                scenario_id,

            "scenario_type":
                "LEGITIMATE_REPEATED_TRANSFER",

            "fraud_reason":
                "Repeated transfers occurring over a normal time interval with moderate amounts and consistent behavior",

            "severity":
                "NONE",


            # -----------------------------
            # Behavioral metadata
            # -----------------------------

            "transaction_position":
                position + 1,

            "transactions_in_scenario":
                TRANSACTIONS_PER_SCENARIO,

            "step_gap_from_previous":
                (
                    0
                    if position == 0
                    else step_gaps[position]
                ),

            "balance_usage_ratio":
                round(
                    balance_usage,
                    4
                ),

            "is_legitimate_counterexample":
                1
        }

        synthetic_rows.append(
            row
        )

        remaining_balance = new_balance


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
print("L02 VALIDATION")
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
        synthetic[
            "scenario_id"
        ].nunique(),
        2
    )
)


# ============================================================
# STEP GAP VALIDATION
# ============================================================

scenario_steps = (
    synthetic
    .groupby("scenario_id")[
        "step"
    ]
    .agg(
        min_step="min",
        max_step="max"
    )
)

scenario_steps[
    "step_window"
] = (
    scenario_steps[
        "max_step"
    ] -
    scenario_steps[
        "min_step"
    ]
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
    "Minimum scenario step window:",
    scenario_steps[
        "step_window"
    ].min()
)

print(
    "Maximum scenario step window:",
    scenario_steps[
        "step_window"
    ].max()
)


# ============================================================
# AMOUNT VALIDATION
# ============================================================

print(
    "Average amount:",
    round(
        synthetic[
            "amount"
        ].mean(),
        2
    )
)

print(
    "Median amount:",
    round(
        synthetic[
            "amount"
        ].median(),
        2
    )
)

print(
    "Maximum amount:",
    round(
        synthetic[
            "amount"
        ].max(),
        2
    )
)


# ============================================================
# BALANCE USAGE
# ============================================================

print(
    "Average balance usage:",
    round(
        synthetic[
            "balance_usage_ratio"
        ].mean() * 100,
        2
    ),
    "%"
)

print(
    "Maximum balance usage:",
    round(
        synthetic[
            "balance_usage_ratio"
        ].max() * 100,
        2
    ),
    "%"
)


# ============================================================
# VALIDATION ASSERTIONS
# ============================================================

assert len(synthetic) == TARGET_ROWS

assert (
    synthetic["isFraud"] == 0
).all()

assert (
    synthetic["type"] ==
    "TRANSFER"
).all()

assert (
    synthetic[
        "scenario_type"
    ] ==
    "LEGITIMATE_REPEATED_TRANSFER"
).all()

assert (
    synthetic[
        "is_legitimate_counterexample"
    ] == 1
).all()

assert (
    synthetic[
        "scenario_id"
    ].nunique()
    == TARGET_SCENARIOS
)

scenario_counts = (
    synthetic
    .groupby("scenario_id")
    .size()
)

assert (
    scenario_counts ==
    TRANSACTIONS_PER_SCENARIO
).all()

# Each scenario should have one sender.

sender_counts = (
    synthetic
    .groupby("scenario_id")[
        "nameOrig"
    ]
    .nunique()
)

assert (
    sender_counts == 1
).all()

# Each scenario should use one destination.

destination_counts = (
    synthetic
    .groupby("scenario_id")[
        "nameDest"
    ]
    .nunique()
)

assert (
    destination_counts == 1
).all()

# The scenario should NOT be a rapid burst.
# Minimum total window should be greater than
# the 3-step S01 pattern.

assert (
    scenario_steps[
        "step_window"
    ] >= 40
).all()

# Amounts should remain moderate.

assert (
    synthetic["amount"] <
    amount_95th
).all()

# No transaction should consume most of
# the sender's balance.

assert (
    synthetic[
        "balance_usage_ratio"
    ] < 0.20
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
        synthetic[
            "scenario_id"
        ] == sample_scenario
    ][
        [
            "record_id",
            "step",
            "type",
            "amount",
            "nameOrig",
            "nameDest",
            "isFraud",
            "scenario_id",
            "transaction_position",
            "step_gap_from_previous",
            "balance_usage_ratio"
        ]
    ]
)