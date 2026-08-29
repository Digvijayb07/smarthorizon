import pandas as pd
import numpy as np

# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S01_rapid_transfers.csv"

TARGET_ROWS = 5000
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Base dataset:", df.shape)

# ============================================================
# BASIC CLEANING
# ============================================================

# Keep legitimate transactions only
legit = df[df["isFraud"] == 0].copy()

# We use legitimate TRANSFER transactions as seeds
seed_data = legit[
    (legit["type"] == "TRANSFER") &
    (legit["nameOrig"].notna())
].copy()

print("Legitimate transactions:", len(legit))
print("Transfer seed transactions:", len(seed_data))

if len(seed_data) == 0:
    raise ValueError("No legitimate TRANSFER transactions found.")

# ============================================================
# GENERATE RAPID TRANSFER BURSTS
# ============================================================

synthetic_rows = []

scenario_number = 1

while len(synthetic_rows) < TARGET_ROWS:

    # --------------------------------------------------------
    # Select one legitimate transaction as a seed
    # --------------------------------------------------------

    seed = seed_data.sample(
        n=1,
        random_state=np.random.randint(0, 1_000_000)
    ).iloc[0]

    sender = seed["nameOrig"]

    # --------------------------------------------------------
    # Number of transfers in this burst
    # --------------------------------------------------------

    burst_size = np.random.randint(3, 7)

    # --------------------------------------------------------
    # Starting time
    # --------------------------------------------------------

    base_step = int(seed["step"])

    # All transactions happen within 5 steps
    step_offsets = np.sort(
        np.random.randint(
            0,
            6,
            size=burst_size
        )
    )

    # --------------------------------------------------------
    # Determine synthetic starting balance
    # --------------------------------------------------------

    seed_balance = float(seed["oldbalanceOrg"])
    seed_amount = float(seed["amount"])

    # Create a sufficiently funded synthetic account
    minimum_balance = seed_amount * burst_size * 1.5

    starting_balance = max(
        seed_balance,
        minimum_balance,
        50000
    )

    remaining_balance = starting_balance

    # --------------------------------------------------------
    # Determine transaction amount
    # --------------------------------------------------------

    # Make transfers significantly larger than seed amount
    # ========================================================
    # Use realistic transaction amounts
    # ========================================================

    # Calculate realistic limits from legitimate transfers
    transfer_amounts = seed_data["amount"]

    amount_95th = transfer_amounts.quantile(0.95)
    amount_median = transfer_amounts.median()

    # --------------------------------------------------------
    # Generate burst
    # --------------------------------------------------------

    for i in range(burst_size):

        # ========================================================
        # Generate a realistic transaction amount
        # ========================================================

        # Sample an amount from the real legitimate
        # TRANSFER distribution.

        amount = np.random.choice(
            seed_data["amount"].values
        )

        # Small natural variation
        amount = amount * np.random.uniform(0.90, 1.10)

        # Keep within realistic limits
        amount = min(
            amount,
            seed_data["amount"].quantile(0.95)
        )

        amount = max(
            amount,
            seed_data["amount"].quantile(0.05)
        )

        mount = round(amount, 2)

        # Make sure the synthetic account can afford it
        amount = min(
            amount,
            remaining_balance * 0.20
        )

        if amount <= 1:
            continue

        old_balance = remaining_balance
        new_balance = old_balance - amount

        # Synthetic destination
        destination = (
            "C_SYN_" +
            str(np.random.randint(
                100000000,
                999999999
            ))
        )

        row = {

            # -----------------------------
            # Original PaySim fields
            # -----------------------------

            "record_id":
                f"S01_{len(synthetic_rows)+1:06d}",

            "step":
                base_step + int(step_offsets[i]),

            "type":
                "TRANSFER",

            "amount":
                round(amount, 2),

            "nameOrig":
                sender,

            "oldbalanceOrg":
                round(old_balance, 2),

            "newbalanceOrig":
                round(new_balance, 2),

            "nameDest":
                destination,

            "oldbalanceDest":
                0.0,

            "newbalanceDest":
                round(amount, 2),

            "isFraud":
                1,

            "isFlaggedFraud":
                0,

            # -----------------------------
            # Investigator metadata
            # -----------------------------

            "scenario_id":
                f"S01_{scenario_number:05d}",

            "scenario_type":
                "RAPID_REPEATED_TRANSFER",

            "fraud_reason":
                "Multiple high-value transfers from the same account within a short time window",

            "severity":
                "HIGH"
        }

        synthetic_rows.append(row)

        remaining_balance = new_balance

    scenario_number += 1

# ============================================================
# CREATE DATAFRAME
# ============================================================

synthetic = pd.DataFrame(synthetic_rows)

# Exactly TARGET_ROWS
synthetic = synthetic.head(TARGET_ROWS)

# ============================================================
# VALIDATION
# ============================================================

print(
    "Base legitimate transfer average:",
    round(seed_data["amount"].mean(), 2)
)

print(
    "Base legitimate transfer median:",
    round(seed_data["amount"].median(), 2)
)

print(
    "Base legitimate transfer 95th percentile:",
    round(seed_data["amount"].quantile(0.95), 2)
)

print()
print("=" * 50)
print("S01 VALIDATION")
print("=" * 50)

print("Rows:", len(synthetic))

print(
    "Fraud labels:",
    synthetic["isFraud"].value_counts().to_dict()
)

print(
    "Transaction types:",
    synthetic["type"].value_counts().to_dict()
)

print(
    "Unique accounts:",
    synthetic["nameOrig"].nunique()
)

print(
    "Unique scenarios:",
    synthetic["scenario_id"].nunique()
)

print(
    "Average amount:",
    round(synthetic["amount"].mean(), 2)
)

print(
    "Minimum amount:",
    round(synthetic["amount"].min(), 2)
)

print(
    "Maximum amount:",
    round(synthetic["amount"].max(), 2)
)

# ------------------------------------------------------------
# Validation checks
# ------------------------------------------------------------

assert len(synthetic) == TARGET_ROWS

assert (
    synthetic["type"] == "TRANSFER"
).all()

assert (
    synthetic["isFraud"] == 1
).all()

assert (
    synthetic["amount"] > 0
).all()

assert (
    synthetic["scenario_type"] ==
    "RAPID_REPEATED_TRANSFER"
).all()

# ============================================================
# SAVE
# ============================================================

synthetic.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved:", OUTPUT_FILE)
print("Final shape:", synthetic.shape)

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