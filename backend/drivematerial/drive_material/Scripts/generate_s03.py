import pandas as pd
import numpy as np

# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S03_account_draining.csv"

TARGET_ROWS = 4000
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

# We need transactions where the sender has
# meaningful available balance.

seed_data = legit[
    (legit["oldbalanceOrg"] > 0) &
    (legit["nameOrig"].notna())
].copy()

print(
    "Transactions with available balance:",
    len(seed_data)
)

if len(seed_data) == 0:
    raise ValueError(
        "No suitable transactions found."
    )

# ============================================================
# GENERATE S03
# ============================================================

synthetic_rows = []

scenario_number = 1

while len(synthetic_rows) < TARGET_ROWS:

    # --------------------------------------------------------
    # Select legitimate transaction as account seed
    # --------------------------------------------------------

    seed = seed_data.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    sender = seed["nameOrig"]

    # --------------------------------------------------------
    # Create realistic account balance
    # --------------------------------------------------------

    original_balance = float(
        seed["oldbalanceOrg"]
    )

    # Make sure the balance is meaningful
    original_balance = max(
        original_balance,
        50000
    )

    # --------------------------------------------------------
    # Drain ratio
    # --------------------------------------------------------

    # S03 = transaction consumes most
    # of the available account balance.

    drain_ratio = np.random.uniform(
        0.80,
        0.98
    )

    suspicious_amount = (
        original_balance *
        drain_ratio
    )

    suspicious_amount = round(
        suspicious_amount,
        2
    )

    # Remaining balance
    remaining_balance = (
        original_balance -
        suspicious_amount
    )

    # --------------------------------------------------------
    # Transaction type
    # --------------------------------------------------------

    transaction_type = np.random.choice(
        [
            "TRANSFER",
            "CASH_OUT"
        ],
        p=[
            0.55,
            0.45
        ]
    )

    # --------------------------------------------------------
    # Destination
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
            f"S03_{len(synthetic_rows)+1:06d}",

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
                original_balance,
                2
            ),

        "newbalanceOrig":
            round(
                remaining_balance,
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
            f"S03_{scenario_number:05d}",

        "scenario_type":
            "ACCOUNT_DRAINING",

        "fraud_reason":
            "Transaction drains an unusually large proportion of the account balance",

        "severity":
            "CRITICAL"
    }

    synthetic_rows.append(row)

    scenario_number += 1

# ============================================================
# DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)

synthetic = synthetic.head(
    TARGET_ROWS
)

# ============================================================
# DERIVED VALIDATION METRIC
# ============================================================

synthetic["drain_ratio"] = (
    synthetic["amount"] /
    synthetic["oldbalanceOrg"]
)

# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 55)
print("S03 VALIDATION")
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

print(
    "Average drain ratio:",
    round(
        synthetic["drain_ratio"].mean() * 100,
        2
    ),
    "%"
)

print(
    "Minimum drain ratio:",
    round(
        synthetic["drain_ratio"].min() * 100,
        2
    ),
    "%"
)

print(
    "Maximum drain ratio:",
    round(
        synthetic["drain_ratio"].max() * 100,
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
    synthetic["oldbalanceOrg"] > 0
).all()

assert (
    synthetic["newbalanceOrig"] >= 0
).all()

assert (
    synthetic["scenario_type"] ==
    "ACCOUNT_DRAINING"
).all()

assert (
    synthetic["scenario_id"]
    .nunique()
    == TARGET_ROWS
)

# Every transaction must drain >= 80%
assert (
    synthetic["drain_ratio"] >= 0.80
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
            "oldbalanceOrg",
            "newbalanceOrig",
            "nameDest",
            "isFraud",
            "scenario_id",
            "scenario_type",
            "severity",
            "drain_ratio"
        ]
    ].head(10)
)