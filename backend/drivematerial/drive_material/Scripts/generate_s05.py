import pandas as pd
import numpy as np

# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S05_multiple_small_transactions.csv"

TARGET_ROWS = 3500
TARGET_SCENARIOS = 500
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Base dataset:", df.shape)

# ============================================================
# LEGITIMATE TRANSACTIONS
# ============================================================

legit = df[
    df["isFraud"] == 0
].copy()

print(
    "Legitimate transactions:",
    len(legit)
)

# ============================================================
# AMOUNT DISTRIBUTION
# ============================================================

amount_75th = legit["amount"].quantile(0.75)
amount_95th = legit["amount"].quantile(0.95)

print(
    "Legitimate amount 75th percentile:",
    round(amount_75th, 2)
)

print(
    "Legitimate amount 95th percentile:",
    round(amount_95th, 2)
)

# We deliberately use relatively small legitimate
# transaction amounts as building blocks.
small_transactions = legit[
    (legit["amount"] > 0) &
    (legit["amount"] <= amount_75th) &
    (legit["oldbalanceOrg"] > 0) &
    (legit["nameOrig"].notna())
].copy()

print(
    "Small legitimate seed transactions:",
    len(small_transactions)
)

if len(small_transactions) == 0:
    raise ValueError(
        "No suitable legitimate transactions found."
    )

# ============================================================
# ELIGIBLE SENDERS
# ============================================================

eligible_senders = (
    small_transactions[
        [
            "nameOrig",
            "oldbalanceOrg"
        ]
    ]
    .drop_duplicates("nameOrig")
)

print(
    "Eligible senders:",
    len(eligible_senders)
)

if len(eligible_senders) == 0:
    raise ValueError(
        "No eligible senders found."
    )

# ============================================================
# GENERATE S05 SCENARIOS
# ============================================================

synthetic_rows = []

scenario_number = 1

TARGET_SCENARIOS = 500

while scenario_number <= TARGET_SCENARIOS:

    # --------------------------------------------------------
    # Select a sender
    # --------------------------------------------------------

    sender = eligible_senders.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]["nameOrig"]

    # --------------------------------------------------------
    # Get sender's legitimate history
    # --------------------------------------------------------

    sender_transactions = small_transactions[
        small_transactions["nameOrig"] == sender
    ]

    if len(sender_transactions) == 0:
        continue

    seed = sender_transactions.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    base_step = int(seed["step"])

    # --------------------------------------------------------
    # Number of transactions
    # --------------------------------------------------------

    burst_size = 7

    # --------------------------------------------------------
    # Create time pattern
    # --------------------------------------------------------

    # Spread transactions over 2–15 steps.
    # This is intentionally less concentrated than S01.

    step_offsets = np.sort(
        np.random.randint(
            2,
            16,
            size=burst_size
        )
    )

    # --------------------------------------------------------
    # Generate small amounts
    # --------------------------------------------------------

    amounts = []

    total_amount = 0

    max_attempts = 100

    for _ in range(max_attempts):

        amounts = []

        for _ in range(burst_size):

            # Pick a real legitimate amount
            sampled_amount = np.random.choice(
                small_transactions["amount"].values
            )

            # Add small natural variation
            sampled_amount *= np.random.uniform(
                0.85,
                1.10
            )

            # Never allow individual transaction
            # to exceed the legitimate 75th percentile.
            sampled_amount = min(
                sampled_amount,
                amount_75th * 0.95
            )

            sampled_amount = max(
                sampled_amount,
                1000
            )

            amounts.append(
                round(sampled_amount, 2)
            )

        total_amount = sum(amounts)

        # We want the combined scenario to be
        # significantly larger than a normal transaction.
        if total_amount > amount_95th:
            break

    # If we couldn't produce a suitable scenario,
    # try another sender.
    if total_amount <= amount_95th:
        continue

    # --------------------------------------------------------
    # Account balance
    # --------------------------------------------------------

    seed_balance = float(
        seed["oldbalanceOrg"]
    )

    # Create enough balance so the scenario does not
    # accidentally become account draining.

    required_balance = (
        total_amount /
        np.random.uniform(
            0.45,
            0.65
        )
    )

    starting_balance = max(
        seed_balance,
        required_balance,
        total_amount * 1.6,
        50000
    )

    remaining_balance = starting_balance

    # --------------------------------------------------------
    # Generate transactions
    # --------------------------------------------------------

    scenario_rows = []

    valid_scenario = True

    for i in range(burst_size):

        amount = amounts[i]

        # Make sure each individual transaction does not
        # consume too much of the balance.

        if amount > remaining_balance * 0.30:
            valid_scenario = False
            break

        old_balance = remaining_balance

        new_balance = (
            old_balance -
            amount
        )

        destination = (
            "C_SYN_" +
            str(
                np.random.randint(
                    100000000,
                    999999999
                )
            )
        )

        row = {

            # -----------------------------
            # PaySim fields
            # -----------------------------

            "record_id":
                f"S05_{len(synthetic_rows) + len(scenario_rows) + 1:06d}",

            "step":
                base_step +
                int(step_offsets[i]),

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
                f"S05_{scenario_number:05d}",

            "scenario_type":
                "MULTIPLE_SMALL_TRANSACTIONS",

            "fraud_reason":
                "Multiple individually small transactions combine into an unusually large total amount",

            "severity":
                "HIGH",

            "transaction_count_in_scenario":
                burst_size,

            "combined_scenario_amount":
                round(
                    total_amount,
                    2
                ),

            "individual_amount_percentile":
                round(
                    (amount / amount_75th) * 100,
                    2
                )
        }

        scenario_rows.append(row)

        remaining_balance = new_balance

    # --------------------------------------------------------
    # Accept scenario
    # --------------------------------------------------------

    if not valid_scenario:
        continue

    synthetic_rows.extend(
        scenario_rows
    )

    scenario_number += 1

# ============================================================
# DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)

# ============================================================
# DERIVED METRICS
# ============================================================

synthetic["scenario_total_ratio"] = (
    synthetic["combined_scenario_amount"] /
    synthetic["oldbalanceOrg"]
)

# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("S05 VALIDATION")
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
    "Average transactions per scenario:",
    round(
        synthetic["transaction_count_in_scenario"].mean(),
        2
    )
)

print(
    "Average individual amount:",
    round(
        synthetic["amount"].mean(),
        2
    )
)

print(
    "Median individual amount:",
    round(
        synthetic["amount"].median(),
        2
    )
)

print(
    "Maximum individual amount:",
    round(
        synthetic["amount"].max(),
        2
    )
)

print(
    "Average combined scenario amount:",
    round(
        synthetic["combined_scenario_amount"].mean(),
        2
    )
)

print(
    "Minimum combined scenario amount:",
    round(
        synthetic["combined_scenario_amount"].min(),
        2
    )
)

print(
    "Percentage of rows below legitimate 75th percentile:",
    round(
        (
            synthetic["amount"] <= amount_75th
        ).mean() * 100,
        2
    ),
    "%"
)

print(
    "Percentage of scenarios above legitimate 95th percentile:"
)

scenario_totals = (
    synthetic
    .groupby("scenario_id")["combined_scenario_amount"]
    .first()
)

print(
    round(
        (
            scenario_totals > amount_95th
        ).mean() * 100,
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
    synthetic["type"] == "TRANSFER"
).all()

assert (
    synthetic["scenario_type"] ==
    "MULTIPLE_SMALL_TRANSACTIONS"
).all()

assert (
    synthetic["scenario_id"]
    .nunique()
    >= 500
)

# Individual transactions should remain below
# the legitimate 75th percentile.
assert (
    synthetic["amount"] <= amount_75th
).all()

# Combined scenario must exceed 95th percentile.
assert (
    scenario_totals > amount_95th
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
            "transaction_count_in_scenario",
            "combined_scenario_amount"
        ]
    ].head(12)
)