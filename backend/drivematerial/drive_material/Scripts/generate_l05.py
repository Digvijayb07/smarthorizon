import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"

OUTPUT_FILE = (
    "data/synthetic_L05_legitimate_multiple_small_transactions.csv"
)

TARGET_ROWS = 3500

TRANSACTIONS_PER_SCENARIO = 7

TARGET_SCENARIOS = (
    TARGET_ROWS // TRANSACTIONS_PER_SCENARIO
)

RANDOM_SEED = 105

np.random.seed(RANDOM_SEED)


# ============================================================
# LOAD BASE DATASET
# ============================================================

df = pd.read_csv(
    INPUT_FILE
)

print(
    "Base dataset:",
    df.shape
)


# ============================================================
# LEGITIMATE TRANSACTIONS
# ============================================================

legitimate = df[
    df["isFraud"] == 0
].copy()

print(
    "Legitimate transactions:",
    len(legitimate)
)


# ============================================================
# LEGITIMATE AMOUNT STATISTICS
# ============================================================

amount_25th = legitimate[
    "amount"
].quantile(0.25)

amount_75th = legitimate[
    "amount"
].quantile(0.75)

print(
    "Legitimate amount 25th percentile:",
    round(
        amount_25th,
        2
    )
)

print(
    "Legitimate amount 75th percentile:",
    round(
        amount_75th,
        2
    )
)


# ============================================================
# SMALL LEGITIMATE SEED TRANSACTIONS
# ============================================================
#
# We use legitimate transactions below the 75th percentile.
#
# These are only SEEDS.
# The repeated transactions themselves are synthetic.
# ============================================================

small_transactions = legitimate[
    legitimate["amount"] <= amount_75th
].copy()

print(
    "Small legitimate seed transactions:",
    len(small_transactions)
)


# ============================================================
# ELIGIBLE SENDERS
# ============================================================
#
# We do NOT require the sender to already have multiple
# transactions.
#
# We are creating the repeated activity synthetically.
# ============================================================

eligible_senders = (
    small_transactions[
        "nameOrig"
    ]
    .dropna()
    .unique()
)

print(
    "Eligible senders:",
    len(eligible_senders)
)


# ============================================================
# GENERATE SCENARIOS
# ============================================================

synthetic_rows = []

scenario_number = 1

failed_attempts = 0

MAX_FAILED_ATTEMPTS = 5000


while len(synthetic_rows) < TARGET_ROWS:

    # --------------------------------------------------------
    # Safety condition
    # --------------------------------------------------------

    if failed_attempts >= MAX_FAILED_ATTEMPTS:

        raise RuntimeError(
            "Unable to generate enough L05 scenarios. "
            "Check the seed selection and balance conditions."
        )

    # --------------------------------------------------------
    # Select legitimate sender
    # --------------------------------------------------------

    sender = np.random.choice(
        eligible_senders
    )

    sender_rows = small_transactions[
        small_transactions[
            "nameOrig"
        ] == sender
    ]

    if len(sender_rows) == 0:

        failed_attempts += 1

        continue

    # --------------------------------------------------------
    # Select a legitimate seed transaction
    # --------------------------------------------------------

    seed = sender_rows.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    # --------------------------------------------------------
    # Starting step
    # --------------------------------------------------------

    base_step = int(
        seed["step"]
    )

    # --------------------------------------------------------
    # Starting balance
    # --------------------------------------------------------

    old_balance = float(
        seed["oldbalanceOrg"]
    )

    if old_balance <= 1:

        failed_attempts += 1

        continue

    # --------------------------------------------------------
    # Generate normal time spacing
    # --------------------------------------------------------
    #
    # Transactions are deliberately spread over time.
    #
    # This contrasts with S05 where the suspicious activity
    # consists of multiple small transactions intended to
    # form a suspicious aggregate pattern.
    #
    # Here the activity is normal repeated behavior.
    # --------------------------------------------------------

    step_offsets = np.sort(
        np.random.choice(
            np.arange(
                5,
                101
            ),
            size=TRANSACTIONS_PER_SCENARIO,
            replace=False
        )
    )

    # --------------------------------------------------------
    # Base transaction amount
    # --------------------------------------------------------

    base_amount = float(
        seed["amount"]
    )

    # Keep the base amount below the legitimate 75th
    # percentile.

    base_amount = min(
        base_amount,
        amount_75th * 0.80
    )

    if base_amount <= 1:

        failed_attempts += 1

        continue

    # --------------------------------------------------------
    # Generate amounts
    # --------------------------------------------------------

    scenario_amounts = []

    # Balance BEFORE each transaction
    scenario_balances = []

    remaining_balance = old_balance

    for i in range(
        TRANSACTIONS_PER_SCENARIO
    ):

        if remaining_balance <= 1:

            break

        # ----------------------------------------------------
        # Slight natural variation
        # ----------------------------------------------------

        amount = (
            base_amount *
            np.random.uniform(
                0.70,
                1.20
            )
        )

        # ----------------------------------------------------
        # Keep individual transaction small
        #
        # Maximum approximately 5% of available balance.
        # ----------------------------------------------------

        amount = min(
            amount,
            amount_75th * 0.80,
            remaining_balance * 0.05
        )

        if amount <= 1:

            break

        amount = round(
            amount,
            2
        )

        # ----------------------------------------------------
        # Store balance BEFORE transaction
        # ----------------------------------------------------

        scenario_balances.append(
            remaining_balance
        )

        # ----------------------------------------------------
        # Store amount
        # ----------------------------------------------------

        scenario_amounts.append(
            amount
        )

        # ----------------------------------------------------
        # Update balance
        # ----------------------------------------------------

        remaining_balance -= amount

    # --------------------------------------------------------
    # Require complete scenario
    # --------------------------------------------------------

    if len(
        scenario_amounts
    ) != TRANSACTIONS_PER_SCENARIO:

        failed_attempts += 1

        continue

    # ========================================================
    # COMBINED SCENARIO AMOUNT
    # ========================================================

    combined_amount = round(
        sum(
            scenario_amounts
        ),
        2
    )


    # ========================================================
    # CREATE TRANSACTION ROWS
    # ========================================================

    for i in range(
        TRANSACTIONS_PER_SCENARIO
    ):

        if len(
            synthetic_rows
        ) >= TARGET_ROWS:

            break

        # ----------------------------------------------------
        # Amount
        # ----------------------------------------------------

        amount = scenario_amounts[i]

        # ----------------------------------------------------
        # Correct balance BEFORE transaction
        # ----------------------------------------------------

        old_bal = scenario_balances[i]

        # ----------------------------------------------------
        # Correct balance AFTER transaction
        # ----------------------------------------------------

        new_bal = (
            old_bal - amount
        )

        # ----------------------------------------------------
        # Synthetic legitimate destination
        # ----------------------------------------------------

        destination = (
            "C_LEGIT_" +
            str(
                np.random.randint(
                    100000000,
                    999999999
                )
            )
        )

        # ----------------------------------------------------
        # Step gap
        # ----------------------------------------------------

        if i == 0:

            step_gap = 0

        else:

            step_gap = (
                int(
                    step_offsets[i]
                )
                -
                int(
                    step_offsets[i - 1]
                )
            )

        # ----------------------------------------------------
        # Balance usage ratio
        # ----------------------------------------------------

        if old_bal > 0:

            balance_usage = (
                amount /
                old_bal
            )

        else:

            balance_usage = 0


        # ====================================================
        # CREATE ROW
        # ====================================================

        row = {

            # -----------------------------------------------
            # Original PaySim fields
            # -----------------------------------------------

            "record_id":
                f"L05_{len(synthetic_rows)+1:06d}",

            "step":
                base_step +
                int(
                    step_offsets[i]
                ),

            "type":
                "TRANSFER",

            "amount":
                round(
                    amount,
                    2
                ),

            "nameOrig":
                sender,

            "oldbalanceOrg":
                round(
                    old_bal,
                    2
                ),

            "newbalanceOrig":
                round(
                    new_bal,
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


            # -----------------------------------------------
            # Investigator metadata
            # -----------------------------------------------

            "scenario_id":
                f"L05_{scenario_number:05d}",

            "scenario_type":
                "LEGITIMATE_MULTIPLE_SMALL_TRANSACTIONS",

            "fraud_reason":
                "None - repeated small transactions within normal behavioral range",

            "severity":
                "NONE",

            "is_legitimate_counterexample":
                1,

            "transaction_position":
                i + 1,

            "transaction_count_in_scenario":
                TRANSACTIONS_PER_SCENARIO,

            "combined_scenario_amount":
                combined_amount,

            "step_gap_from_previous":
                step_gap,

            "balance_usage_ratio":
                round(
                    balance_usage,
                    4
                ),

            "behavior_pattern":
                "NORMAL_REPEATED_ACTIVITY"
        }

        synthetic_rows.append(
            row
        )


    # ========================================================
    # NEXT SCENARIO
    # ========================================================

    scenario_number += 1

    failed_attempts = 0


# ============================================================
# CREATE DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)


# ============================================================
# VALIDATION HEADER
# ============================================================

print()
print(
    "=" * 60
)

print(
    "L05 VALIDATION"
)

print(
    "=" * 60
)


# ============================================================
# BASIC VALIDATION
# ============================================================

print(
    "Rows:",
    len(synthetic)
)

print(
    "Fraud labels:",
    synthetic[
        "isFraud"
    ]
    .value_counts()
    .to_dict()
)

print(
    "Transaction types:",
    synthetic[
        "type"
    ]
    .value_counts()
    .to_dict()
)

print(
    "Unique accounts:",
    synthetic[
        "nameOrig"
    ]
    .nunique()
)

print(
    "Unique scenarios:",
    synthetic[
        "scenario_id"
    ]
    .nunique()
)


# ============================================================
# SCENARIO STATISTICS
# ============================================================

scenario_counts = (
    synthetic
    .groupby(
        "scenario_id"
    )
    .size()
)

print(
    "Average transactions per scenario:",
    round(
        scenario_counts.mean(),
        2
    )
)

print(
    "Minimum transactions per scenario:",
    scenario_counts.min()
)

print(
    "Maximum transactions per scenario:",
    scenario_counts.max()
)


# ============================================================
# AMOUNT STATISTICS
# ============================================================

print(
    "Average individual amount:",
    round(
        synthetic[
            "amount"
        ].mean(),
        2
    )
)

print(
    "Median individual amount:",
    round(
        synthetic[
            "amount"
        ].median(),
        2
    )
)

print(
    "Maximum individual amount:",
    round(
        synthetic[
            "amount"
        ].max(),
        2
    )
)


# ============================================================
# COMBINED SCENARIO AMOUNT
# ============================================================

scenario_totals = (
    synthetic
    .groupby(
        "scenario_id"
    )[
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
# STEP GAP STATISTICS
# ============================================================

print(
    "Average step gap:",
    round(
        synthetic[
            "step_gap_from_previous"
        ].mean(),
        2
    )
)

print(
    "Minimum step gap:",
    synthetic[
        "step_gap_from_previous"
    ].min()
)

print(
    "Maximum step gap:",
    synthetic[
        "step_gap_from_previous"
    ].max()
)


# ============================================================
# BALANCE USAGE STATISTICS
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

assert (
    len(synthetic)
    ==
    TARGET_ROWS
)

assert (
    synthetic[
        "isFraud"
    ]
    ==
    0
).all()

assert (
    synthetic[
        "isFlaggedFraud"
    ]
    ==
    0
).all()

assert (
    synthetic[
        "is_legitimate_counterexample"
    ]
    ==
    1
).all()

assert (
    synthetic[
        "scenario_type"
    ]
    ==
    "LEGITIMATE_MULTIPLE_SMALL_TRANSACTIONS"
).all()

assert (
    synthetic[
        "behavior_pattern"
    ]
    ==
    "NORMAL_REPEATED_ACTIVITY"
).all()

assert (
    synthetic[
        "amount"
    ]
    <=
    amount_75th
).all()

assert (
    synthetic[
        "balance_usage_ratio"
    ]
    <
    1
).all()

assert (
    scenario_counts
    ==
    TRANSACTIONS_PER_SCENARIO
).all()

assert (
    synthetic[
        "newbalanceOrig"
    ]
    >=
    0
).all()


# ============================================================
# SAVE DATASET
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


# ============================================================
# SAMPLE SCENARIO
# ============================================================

print()
print(
    "Sample scenario:"
)

first_scenario = (
    synthetic[
        "scenario_id"
    ].iloc[0]
)

print(
    synthetic[
        synthetic[
            "scenario_id"
        ]
        ==
        first_scenario
    ][[
        "record_id",
        "step",
        "type",
        "amount",
        "nameOrig",
        "nameDest",
        "isFraud",
        "scenario_id",
        "scenario_type",
        "transaction_position",
        "transaction_count_in_scenario",
        "combined_scenario_amount",
        "step_gap_from_previous",
        "balance_usage_ratio"
    ]]
)