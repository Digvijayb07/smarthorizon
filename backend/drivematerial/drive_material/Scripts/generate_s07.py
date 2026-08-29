import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S07_dormant_account.csv"

TARGET_ROWS = 3500
RANDOM_SEED = 42

# Minimum inactivity gap between legitimate transactions
MIN_DORMANT_GAP = 50

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
# AMOUNT STATISTICS
# ============================================================

amount_95th = legit[
    "amount"
].quantile(0.95)

amount_median = legit[
    "amount"
].median()

print(
    "Legitimate amount median:",
    round(
        amount_median,
        2
    )
)

print(
    "Legitimate amount 95th percentile:",
    round(
        amount_95th,
        2
    )
)

# ============================================================
# BUILD DORMANT ACCOUNT SEEDS
# ============================================================

dormant_candidates = legit[
    [
        "nameOrig",
        "step",
        "amount",
        "oldbalanceOrg",
        "newbalanceOrig"
    ]
].copy()

dormant_candidates = dormant_candidates[
    dormant_candidates["nameOrig"].notna()
]

dormant_candidates = dormant_candidates[
    dormant_candidates["oldbalanceOrg"] >= 0
]

print(
    "Dormant account seed transactions:",
    len(dormant_candidates)
)

print(
    "Unique seed accounts:",
    dormant_candidates["nameOrig"].nunique()
)

if len(dormant_candidates) == 0:
    raise ValueError(
        "No suitable legitimate account seeds found."
    )


# ============================================================
# GENERATE S07
# ============================================================

synthetic_rows = []


while len(synthetic_rows) < TARGET_ROWS:
    

    # --------------------------------------------------------
    # Select a real dormant-period candidate
    # --------------------------------------------------------

    seed = dormant_candidates.sample(
    n=1,
    random_state=np.random.randint(
        0,
        1_000_000
    )
    ).iloc[0]

    sender = seed["nameOrig"]

    # The real transaction represents the last
    # observed activity before dormancy.

    last_observed_step = int(
        seed["step"]
    )

    previous_step = last_observed_step

    # Synthetic dormant period.
    dormant_period = np.random.randint(
        50,
        151
    )

    suspicious_step = (
        last_observed_step +
        dormant_period
    )

    total_dormant_gap = (
        suspicious_step -
        last_observed_step
    )

    historical_gap = 0

    # --------------------------------------------------------
    # Create suspicious transaction after dormancy
    # --------------------------------------------------------

    # --------------------------------------------------------
    # Generate moderate / high but not extreme amount
    # --------------------------------------------------------

    # S07 should be primarily about timing.
    # Keep amount below legitimate 95th percentile.

    base_amount = max(
        float(seed["amount"]),
        amount_median * 0.5
    )

    suspicious_amount = (
        base_amount *
        np.random.uniform(
            1.2,
            2.0
        )
    )

    suspicious_amount = min(
        suspicious_amount,
        amount_95th * 0.90
    )

    suspicious_amount = round(
        suspicious_amount,
        2
    )

    if suspicious_amount <= 1:

        continue


    # --------------------------------------------------------
    # Create sufficient balance
    # --------------------------------------------------------

    # We deliberately keep balance usage low so this
    # does not become an S03 account-draining scenario.

    old_balance = max(
        float(seed["oldbalanceOrg"]),
        suspicious_amount * 4,
        50000
    )

    new_balance = (
        old_balance -
        suspicious_amount
    )

    balance_usage = (
        suspicious_amount /
        old_balance
    )

    # Do not allow this scenario to become account draining.

    if balance_usage >= 0.30:

        continue


    # --------------------------------------------------------
    # New destination
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
    # Scenario ID
    # --------------------------------------------------------

    scenario_number = (
        len(synthetic_rows) + 1
    )

    scenario_id = (
        f"S07_{scenario_number:05d}"
    )


    # --------------------------------------------------------
    # Create row
    # --------------------------------------------------------

    row = {

        # -----------------------------
        # PaySim fields
        # -----------------------------

        "record_id":
            f"S07_{scenario_number:06d}",

        "step":
            suspicious_step,

        "type":
            np.random.choice(
                [
                    "TRANSFER",
                    "CASH_OUT",
                    "PAYMENT"
                ],
                p=[
                    0.50,
                    0.30,
                    0.20
                ]
            ),

        "amount":
            suspicious_amount,

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
                suspicious_amount,
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
            "DORMANT_ACCOUNT_SUDDEN_ACTIVITY",

        "fraud_reason":
            "Suspicious transaction occurred after an unusually long period of account inactivity",

        "severity":
            "HIGH",

        # -----------------------------
        # Behavioral features
        # -----------------------------

        "previous_activity_step":
            previous_step,

        "last_observed_step":
            last_observed_step,

        "dormant_gap":
            total_dormant_gap,

        "historical_gap":
            historical_gap,

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
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("S07 VALIDATION")
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
    "Unique accounts:",
    synthetic[
        "nameOrig"
    ].nunique()
)

print(
    "Unique scenarios:",
    synthetic[
        "scenario_id"
    ].nunique()
)

print(
    "Average dormant gap:",
    round(
        synthetic[
            "dormant_gap"
        ].mean(),
        2
    ),
    "steps"
)

print(
    "Minimum dormant gap:",
    synthetic[
        "dormant_gap"
    ].min(),
    "steps"
)

print(
    "Maximum dormant gap:",
    synthetic[
        "dormant_gap"
    ].max(),
    "steps"
)

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
# VALIDATION CHECKS
# ============================================================

assert len(synthetic) == TARGET_ROWS

assert (
    synthetic["isFraud"] == 1
).all()

assert (
    synthetic["scenario_type"] ==
    "DORMANT_ACCOUNT_SUDDEN_ACTIVITY"
).all()

assert (
    synthetic["scenario_id"]
    .nunique()
    == TARGET_ROWS
)

# Every scenario must have a long inactivity period.

assert (
    synthetic["dormant_gap"] >=
    MIN_DORMANT_GAP
).all()

# The transaction must not drain the account.

assert (
    synthetic["balance_usage_ratio"] < 0.30
).all()

# Amount should stay below the normal high-value boundary.

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
            "balance_usage_ratio"
        ]
    ].head(10)
)