import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S09_circular_transactions.csv"

TARGET_SCENARIOS = 875
TRANSACTIONS_PER_SCENARIO = 4

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
    "Unique legitimate accounts:",
    transfer_seeds[
        "nameOrig"
    ].nunique()
)


if transfer_seeds[
    "nameOrig"
].nunique() < 100:

    raise ValueError(
        "Not enough unique legitimate accounts."
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
    round(
        amount_75th,
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
# GENERATE S09
# ============================================================

synthetic_rows = []


for scenario_number in range(
    1,
    TARGET_SCENARIOS + 1
):

    # --------------------------------------------------------
    # Select 4 DIFFERENT accounts
    # --------------------------------------------------------

    seeds = transfer_seeds.sample(
        n=TRANSACTIONS_PER_SCENARIO,
        replace=False,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).copy()

    accounts = seeds[
        "nameOrig"
    ].tolist()

    if len(
        set(accounts)
    ) != 4:

        continue


    # --------------------------------------------------------
    # Create cycle
    #
    # A -> B
    # B -> C
    # C -> D
    # D -> A
    # --------------------------------------------------------

    cycle_accounts = accounts


    # --------------------------------------------------------
    # Scenario ID
    # --------------------------------------------------------

    scenario_id = (
        f"S09_{scenario_number:05d}"
    )


    # --------------------------------------------------------
    # Starting step
    # --------------------------------------------------------

    base_step = np.random.randint(
        1,
        700
    )


    # --------------------------------------------------------
    # Generate 4 transactions
    # --------------------------------------------------------

    scenario_amounts = []


    for position in range(4):

        seed = seeds.iloc[position]

        sender = cycle_accounts[
            position
        ]

        destination = cycle_accounts[
            (position + 1) % 4
        ]


        # ----------------------------------------------------
        # Amount
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
                1.15
            )
        )

        # Keep individual amount below
        # legitimate high-value threshold.

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

        # Prevent account-draining behavior.

        if balance_usage >= 0.30:

            continue


        scenario_amounts.append(
            amount
        )


        # ----------------------------------------------------
        # Step
        # ----------------------------------------------------

        step = (
            base_step +
            position
        )


        # ----------------------------------------------------
        # Record ID
        # ----------------------------------------------------

        record_id = (
            f"S09_{len(synthetic_rows)+1:06d}"
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
                "CIRCULAR_TRANSACTION",

            "fraud_reason":
                "Funds moved through a closed chain of accounts, forming a circular transaction pattern",

            "severity":
                "CRITICAL",


            # -----------------------------
            # Graph features
            # -----------------------------

            "cycle_position":
                position + 1,

            "cycle_length":
                4,

            "next_account":
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
print("S09 VALIDATION")
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
    "Transactions per scenario:",
    round(
        len(synthetic) /
        synthetic["scenario_id"].nunique(),
        2
    )
)


# ============================================================
# CYCLE VALIDATION
# ============================================================

cycle_checks = []

for scenario_id, group in synthetic.groupby(
    "scenario_id"
):

    group = group.sort_values(
        "cycle_position"
    )

    senders = group[
        "nameOrig"
    ].tolist()

    destinations = group[
        "nameDest"
    ].tolist()

    # Each scenario must contain 4 accounts.

    unique_nodes = set(
        senders + destinations
    )

    valid_cycle = (
        len(group) == 4
        and len(set(senders)) == 4
        and len(set(destinations)) == 4
        and destinations[0] == senders[1]
        and destinations[1] == senders[2]
        and destinations[2] == senders[3]
        and destinations[3] == senders[0]
    )

    cycle_checks.append(
        valid_cycle
    )


print(
    "Valid circular scenarios:",
    sum(cycle_checks),
    "/",
    len(cycle_checks)
)


# ============================================================
# STEP WINDOW
# ============================================================

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


# ============================================================
# AMOUNT STATISTICS
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
    synthetic["isFraud"] == 1
).all()

assert (
    synthetic["type"] ==
    "TRANSFER"
).all()

assert (
    synthetic["scenario_type"] ==
    "CIRCULAR_TRANSACTION"
).all()

assert (
    synthetic["scenario_id"]
    .nunique()
    == TARGET_SCENARIOS
)

assert (
    synthetic
    .groupby("scenario_id")
    .size()
    == 4
).all()

assert (
    sum(cycle_checks)
    == TARGET_SCENARIOS
)

assert (
    scenario_steps[
        "step_window"
    ].max()
    <= 3
)

assert (
    synthetic[
        "balance_usage_ratio"
    ] < 0.30
).all()

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
print("Sample cycle:")

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
            "cycle_position",
            "cycle_length",
            "balance_usage_ratio"
        ]
    ]
)