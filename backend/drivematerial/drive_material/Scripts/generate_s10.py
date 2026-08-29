import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S10_fund_dispersion.csv"

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
# TRANSFER SEEDS
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

if (
    transfer_seeds["nameOrig"].nunique()
    < 100
):
    raise ValueError(
        "Not enough legitimate sender accounts."
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
# GENERATE S10
# ============================================================

synthetic_rows = []


for scenario_number in range(
    1,
    TARGET_SCENARIOS + 1
):

    # --------------------------------------------------------
    # Select ONE sender
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
    # Create 5 DIFFERENT destinations
    # --------------------------------------------------------

    destinations = []

    for _ in range(
        TRANSACTIONS_PER_SCENARIO
    ):

        destination = (
            "C_SYN_" +
            str(
                np.random.randint(
                    100000000,
                    999999999
                )
            )
        )

        destinations.append(
            destination
        )


    # Ensure destinations are unique.

    if len(
        set(destinations)
    ) != TRANSACTIONS_PER_SCENARIO:

        continue


    # --------------------------------------------------------
    # Scenario ID
    # --------------------------------------------------------

    scenario_id = (
        f"S10_{scenario_number:05d}"
    )


    # --------------------------------------------------------
    # Short transaction window
    # --------------------------------------------------------

    base_step = np.random.randint(
        1,
        700
    )


    # --------------------------------------------------------
    # Sender balance
    # --------------------------------------------------------

    # Give the sender enough balance to support
    # the complete dispersion pattern.

    seed_balance = float(
        seed["oldbalanceOrg"]
    )

    total_available = max(
        seed_balance,
        50000
    )


    # ========================================================
    # CREATE 5 OUTGOING TRANSACTIONS
    # ========================================================

    scenario_amounts = []

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
            amount_median * 0.35
        )

        amount = (
            base_amount *
            np.random.uniform(
                0.45,
                0.90
            )
        )

        # Keep individual transactions below
        # legitimate high-value threshold.

        amount = min(
            amount,
            amount_95th * 0.80
        )

        amount = round(
            amount,
            2
        )

        if amount <= 1:
            continue


        scenario_amounts.append(
            amount
        )


        # ----------------------------------------------------
        # Transaction step
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
            f"S10_{len(synthetic_rows)+1:06d}"
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

            # These balances are calculated
            # cumulatively below after all
            # scenario amounts are generated.

            "oldbalanceOrg":
                0.0,

            "newbalanceOrig":
                0.0,

            "nameDest":
                destinations[position],

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
                "FUND_DISPERSION",

            "fraud_reason":
                "One account rapidly distributed funds across multiple independent destinations",

            "severity":
                "HIGH",


            # -----------------------------
            # Graph features
            # -----------------------------

            "dispersion_position":
                position + 1,

            "destinations_in_scenario":
                TRANSACTIONS_PER_SCENARIO,

            "common_sender":
                sender
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
# CALCULATE CUMULATIVE SENDER BALANCES
# ============================================================

for scenario_id, indices in (
    synthetic.groupby(
        "scenario_id"
    ).groups.items()
):

    indices = list(indices)

    # Start with enough balance for
    # all transactions in this scenario.

    total_amount = synthetic.loc[
        indices,
        "amount"
    ].sum()

    old_balance = max(
        total_amount * 4,
        50000
    )

    remaining_balance = old_balance

    for idx in indices:

        amount = float(
            synthetic.loc[
                idx,
                "amount"
            ]
        )

        synthetic.loc[
            idx,
            "oldbalanceOrg"
        ] = round(
            remaining_balance,
            2
        )

        remaining_balance -= amount

        synthetic.loc[
            idx,
            "newbalanceOrig"
        ] = round(
            remaining_balance,
            2
        )


# ============================================================
# BALANCE USAGE FEATURE
# ============================================================

synthetic[
    "balance_usage_ratio"
] = (
    synthetic["amount"] /
    synthetic["oldbalanceOrg"]
)

synthetic[
    "balance_usage_ratio"
] = synthetic[
    "balance_usage_ratio"
].round(4)


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("S10 VALIDATION")
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
# DISPERSION VALIDATION
# ============================================================

scenario_sender_counts = (
    synthetic
    .groupby("scenario_id")[
        "nameOrig"
    ]
    .nunique()
)

scenario_destination_counts = (
    synthetic
    .groupby("scenario_id")[
        "nameDest"
    ]
    .nunique()
)

print(
    "Minimum senders per scenario:",
    scenario_sender_counts.min()
)

print(
    "Maximum senders per scenario:",
    scenario_sender_counts.max()
)

print(
    "Minimum destinations per scenario:",
    scenario_destination_counts.min()
)

print(
    "Maximum destinations per scenario:",
    scenario_destination_counts.max()
)


# ============================================================
# TIME WINDOW
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
    "Maximum scenario step window:",
    scenario_steps[
        "step_window"
    ].max()
)


# ============================================================
# AMOUNT
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
# TOTAL DISPERSION AMOUNT
# ============================================================

scenario_totals = (
    synthetic
    .groupby("scenario_id")[
        "amount"
    ]
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
    synthetic["isFraud"] == 1
).all()

assert (
    synthetic["type"] ==
    "TRANSFER"
).all()

assert (
    synthetic["scenario_type"] ==
    "FUND_DISPERSION"
).all()

assert (
    synthetic[
        "scenario_id"
    ].nunique()
    == TARGET_SCENARIOS
)

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

# Every scenario has exactly ONE sender.

assert (
    scenario_sender_counts == 1
).all()

# Every scenario has exactly FIVE destinations.

assert (
    scenario_destination_counts ==
    TRANSACTIONS_PER_SCENARIO
).all()

# Transactions occur in a short window.

assert (
    scenario_steps[
        "step_window"
    ] <= 5
).all()

# Individual transaction should not use
# more than 30% of available balance.

assert (
    synthetic[
        "balance_usage_ratio"
    ] < 0.30
).all()

# Individual amount below legitimate 95th percentile.

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
            "scenario_id",
            "dispersion_position",
            "destinations_in_scenario",
            "balance_usage_ratio"
        ]
    ]
)