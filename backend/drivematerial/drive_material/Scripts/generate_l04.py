import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_L04_legitimate_dormant_reactivation.csv"

TARGET_ROWS = 4000
SCENARIOS = 800
TRANSACTIONS_PER_SCENARIO = 5

np.random.seed(104)


# ============================================================
# LOAD BASE DATASET
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Base dataset:", df.shape)

legitimate = df[
    df["isFraud"] == 0
].copy()

print("Legitimate transactions:", len(legitimate))


# ============================================================
# STATISTICS
# ============================================================

amount_25th = legitimate["amount"].quantile(0.25)
amount_50th = legitimate["amount"].quantile(0.50)
amount_75th = legitimate["amount"].quantile(0.75)

print(
    "Legitimate amount 25th percentile:",
    round(amount_25th, 2)
)

print(
    "Legitimate amount median:",
    round(amount_50th, 2)
)

print(
    "Legitimate amount 75th percentile:",
    round(amount_75th, 2)
)


# ============================================================
# SELECT DORMANT ACCOUNT SEEDS
#
# We use legitimate accounts whose last observed activity
# occurs early enough to allow a synthetic dormant period.
# ============================================================

account_last_activity = (
    legitimate
    .groupby("nameOrig")["step"]
    .max()
    .reset_index()
)

account_last_activity.columns = [
    "nameOrig",
    "last_activity_step"
]

# Need enough room for:
# dormant gap + several normal transactions
dormant_candidates = account_last_activity[
    account_last_activity["last_activity_step"] <= 500
].copy()

print(
    "Dormant account candidates:",
    len(dormant_candidates)
)

print(
    "Unique dormant accounts:",
    dormant_candidates["nameOrig"].nunique()
)

if len(dormant_candidates) == 0:
    raise ValueError(
        "No suitable dormant account candidates found."
    )


# ============================================================
# GENERATE SCENARIOS
# ============================================================

synthetic_rows = []

scenario_number = 0

while len(synthetic_rows) < TARGET_ROWS:

    scenario_number += 1

    # --------------------------------------------------------
    # Select a legitimate dormant account
    # --------------------------------------------------------

    seed = dormant_candidates.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    sender = seed["nameOrig"]

    last_activity_step = int(
        seed["last_activity_step"]
    )

    # --------------------------------------------------------
    # Dormant period
    #
    # Long enough to resemble inactivity, but not extreme.
    # --------------------------------------------------------

    dormant_gap = np.random.randint(
        50,
        151
    )

    first_reactivation_step = (
        last_activity_step +
        dormant_gap
    )

    # Leave enough room for all five transactions.
    if (
        first_reactivation_step +
        (TRANSACTIONS_PER_SCENARIO - 1) * 50
        > 744
    ):
        continue

    # --------------------------------------------------------
    # Generate normal post-reactivation activity
    #
    # Transactions are spread out rather than occurring
    # in a rapid burst.
    # --------------------------------------------------------

    step_gaps = np.random.randint(
        15,
        51,
        size=TRANSACTIONS_PER_SCENARIO
    )

    steps = [
        first_reactivation_step
    ]

    for i in range(1, TRANSACTIONS_PER_SCENARIO):

        next_step = (
            steps[-1] +
            int(step_gaps[i])
        )

        steps.append(next_step)

    if steps[-1] > 744:
        continue

    # --------------------------------------------------------
    # Determine starting balance
    #
    # Keep transactions comfortably affordable.
    # --------------------------------------------------------

    starting_balance = np.random.uniform(
        amount_75th * 2.5,
        amount_75th * 6.0
    )

    remaining_balance = starting_balance

    # --------------------------------------------------------
    # Generate legitimate transaction sequence
    # --------------------------------------------------------

    for position in range(
        TRANSACTIONS_PER_SCENARIO
    ):

        # Normal transaction amount.
        amount = np.random.uniform(
            max(100, amount_25th * 0.5),
            amount_75th * 0.90
        )

        # Keep transaction below 15% of balance.
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

        old_balance = remaining_balance

        new_balance = (
            old_balance -
            amount
        )

        # ----------------------------------------------------
        # Normal transaction type
        # ----------------------------------------------------

        transaction_type = np.random.choice(
            [
                "TRANSFER",
                "PAYMENT",
                "CASH_OUT"
            ],
            p=[
                0.50,
                0.30,
                0.20
            ]
        )

        # ----------------------------------------------------
        # Destination
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
        # Destination balance
        # ----------------------------------------------------

        if transaction_type == "CASH_OUT":

            old_dest_balance = 0.0
            new_dest_balance = 0.0

        elif transaction_type == "PAYMENT":

            old_dest_balance = 0.0
            new_dest_balance = 0.0

        else:

            old_dest_balance = round(
                np.random.uniform(
                    amount * 0.5,
                    amount * 2.0
                ),
                2
            )

            new_dest_balance = round(
                old_dest_balance + amount,
                2
            )

        # ----------------------------------------------------
        # Create row
        # ----------------------------------------------------

        row = {

            # ------------------------------------------------
            # Original PaySim fields
            # ------------------------------------------------

            "record_id":
                f"L04_{len(synthetic_rows)+1:06d}",

            "step":
                int(steps[position]),

            "type":
                transaction_type,

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
                old_dest_balance,

            "newbalanceDest":
                new_dest_balance,

            "isFraud":
                0,

            "isFlaggedFraud":
                0,

            # ------------------------------------------------
            # Investigator metadata
            # ------------------------------------------------

            "scenario_id":
                f"L04_{scenario_number:05d}",

            "scenario_type":
                "LEGITIMATE_DORMANT_REACTIVATION",

            "fraud_reason":
                "Dormant account resumed normal activity without suspicious transaction intensity",

            "severity":
                "NONE",

            "is_legitimate_counterexample":
                1,

            "previous_activity_step":
                last_activity_step,

            "dormant_gap":
                dormant_gap,

            "transaction_position":
                position + 1,

            "transaction_count_in_scenario":
                TRANSACTIONS_PER_SCENARIO,

            "post_reactivation_pattern":
                "NORMAL",

            "balance_usage_ratio":
                round(
                    amount /
                    max(old_balance, 1),
                    4
                )
        }

        synthetic_rows.append(row)

        remaining_balance = new_balance

        if len(synthetic_rows) >= TARGET_ROWS:
            break

    if scenario_number > 10000:
        raise RuntimeError(
            "Unable to generate enough L04 scenarios."
        )


# ============================================================
# DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("L04 VALIDATION")
print("=" * 60)

print(
    "Rows:",
    len(synthetic)
)

print(
    "Fraud labels:",
    synthetic["isFraud"]
    .value_counts()
    .to_dict()
)

print(
    "Transaction types:",
    synthetic["type"]
    .value_counts()
    .to_dict()
)

print(
    "Unique accounts:",
    synthetic["nameOrig"]
    .nunique()
)

print(
    "Unique scenarios:",
    synthetic["scenario_id"]
    .nunique()
)

print(
    "Average dormant gap:",
    round(
        synthetic["dormant_gap"].mean(),
        2
    ),
    "steps"
)

print(
    "Minimum dormant gap:",
    synthetic["dormant_gap"].min(),
    "steps"
)

print(
    "Maximum dormant gap:",
    synthetic["dormant_gap"].max(),
    "steps"
)

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

print(
    "Average balance usage:",
    round(
        synthetic["balance_usage_ratio"].mean() * 100,
        2
    ),
    "%"
)

print(
    "Maximum balance usage:",
    round(
        synthetic["balance_usage_ratio"].max() * 100,
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
    == "LEGITIMATE_DORMANT_REACTIVATION"
).all()

assert (
    synthetic["post_reactivation_pattern"]
    == "NORMAL"
).all()

assert (
    synthetic["dormant_gap"] >= 50
).all()

assert (
    synthetic["dormant_gap"] <= 150
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
print(
    "Saved:",
    OUTPUT_FILE
)

print(
    "Final shape:",
    synthetic.shape
)

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
            "previous_activity_step",
            "dormant_gap",
            "post_reactivation_pattern",
            "balance_usage_ratio"
        ]
    ].head(10)
)