import pandas as pd
import numpy as np

# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S02_high_value.csv"

TARGET_ROWS = 4500
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Base dataset:", df.shape)

# ============================================================
# SELECT LEGITIMATE TRANSACTIONS
# ============================================================

legit = df[
    df["isFraud"] == 0
].copy()

print("Legitimate transactions:", len(legit))

# We use legitimate transactions with reasonably
# normal-sized amounts as the "normal behavior" seed.

amount_75th = legit["amount"].quantile(0.75)
amount_95th = legit["amount"].quantile(0.95)
amount_995th = legit["amount"].quantile(0.995)

print(
    "Legitimate amount 75th percentile:",
    round(amount_75th, 2)
)

print(
    "Legitimate amount 95th percentile:",
    round(amount_95th, 2)
)

print(
    "Legitimate amount 99.5th percentile:",
    round(amount_995th, 2)
)

# Avoid using already-large transactions as the
# normal seed.
seed_data = legit[
    legit["amount"] <= amount_75th
].copy()

print(
    "Normal seed transactions:",
    len(seed_data)
)

if len(seed_data) == 0:
    raise ValueError(
        "No suitable legitimate seed transactions found."
    )

# ============================================================
# GENERATE S02
# ============================================================

synthetic_rows = []

scenario_number = 1

while len(synthetic_rows) < TARGET_ROWS:

    # --------------------------------------------------------
    # Select a normal legitimate transaction
    # --------------------------------------------------------

    seed = seed_data.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    sender = seed["nameOrig"]

    seed_amount = float(seed["amount"])

    # --------------------------------------------------------
    # Generate unusually high amount
    # --------------------------------------------------------

    # Make the transaction several times larger
    # than the normal seed amount.

    multiplier = np.random.uniform(
        4.0,
        8.0
    )

    suspicious_amount = (
        seed_amount * multiplier
    )

    # Ensure it is genuinely high-value
    suspicious_amount = max(
        suspicious_amount,
        amount_95th * np.random.uniform(
            1.05,
            1.25
        )
    )

    # Keep within realistic upper range
    suspicious_amount = min(
        suspicious_amount,
        amount_995th
    )

    suspicious_amount = round(
        suspicious_amount,
        2
    )

    # --------------------------------------------------------
    # Select transaction type
    # --------------------------------------------------------

    transaction_type = np.random.choice(
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
    )

    # --------------------------------------------------------
    # Create sufficient synthetic balance
    # --------------------------------------------------------

    # We don't want S02 to accidentally become a
    # balance-inconsistency scenario.

    starting_balance = (
        suspicious_amount *
        np.random.uniform(
            1.2,
            2.0
        )
    )

    old_balance = starting_balance

    new_balance = (
        old_balance -
        suspicious_amount
    )

    # --------------------------------------------------------
    # Generate destination
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
    # Generate transaction
    # --------------------------------------------------------

    row = {

        # -----------------------------
        # PaySim fields
        # -----------------------------

        "record_id":
            f"S02_{len(synthetic_rows)+1:06d}",

        "step":
            int(seed["step"]) +
            np.random.randint(
                1,
                10
            ),

        "type":
            transaction_type,

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
            f"S02_{scenario_number:05d}",

        "scenario_type":
            "UNUSUAL_HIGH_VALUE",

        "fraud_reason":
            "Transaction amount is significantly higher than normal transaction behavior",

        "severity":
            "HIGH"
    }

    synthetic_rows.append(row)

    scenario_number += 1

# ============================================================
# CREATE DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)

# Exactly 4,500 rows
synthetic = synthetic.head(
    TARGET_ROWS
)

# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 55)
print("S02 VALIDATION")
print("=" * 55)

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
    "Minimum amount:",
    round(
        synthetic["amount"].min(),
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

# Percentage above legitimate 95th percentile

high_value_percentage = (
    synthetic["amount"] > amount_95th
).mean() * 100

print(
    "Above legitimate 95th percentile:",
    round(
        high_value_percentage,
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
    synthetic["amount"] > 0
).all()

assert (
    synthetic["scenario_type"] ==
    "UNUSUAL_HIGH_VALUE"
).all()

assert (
    synthetic["scenario_id"]
    .nunique()
    == TARGET_ROWS
)

# S02 should mostly be above the legitimate
# 95th percentile.
assert high_value_percentage > 90

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
            "severity"
        ]
    ].head(10)
)