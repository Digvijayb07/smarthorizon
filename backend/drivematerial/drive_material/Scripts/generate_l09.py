# ============================================================
# L09 - LEGITIMATE CIRCULAR TRANSACTIONS
# ============================================================
#
# Purpose:
# Create legitimate circular transaction patterns that look
# structurally similar to suspicious circular transactions.
#
# Pattern:
#
#       A ----> B
#       ^       |
#       |       v
#       D <---- C
#
# A -> B -> C -> D -> A
#
# All transactions are legitimate.
# ============================================================

import os
import numpy as np
import pandas as pd


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

BASE_FILE = "data/paysim_base_128k.csv"

OUTPUT_FILE = (
    "data/synthetic_L09_legitimate_circular_transactions.csv"
)

TARGET_ROWS = 3500

CYCLE_LENGTH = 4

TARGET_SCENARIOS = TARGET_ROWS // CYCLE_LENGTH

SEED = 909

np.random.seed(SEED)


# ------------------------------------------------------------
# LOAD BASE DATASET
# ------------------------------------------------------------

df = pd.read_csv(BASE_FILE)

print(f"Base dataset: {df.shape}")


# ------------------------------------------------------------
# NORMALIZE COLUMN NAMES
# ------------------------------------------------------------

df.columns = df.columns.str.strip()


# ------------------------------------------------------------
# REQUIRED COLUMNS
# ------------------------------------------------------------

required_columns = [
    "step",
    "type",
    "amount",
    "nameOrig",
    "oldbalanceOrg",
    "newbalanceOrig",
    "nameDest",
    "oldbalanceDest",
    "newbalanceDest",
    "isFraud",
]


missing = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# ------------------------------------------------------------
# LEGITIMATE TRANSACTIONS
# ------------------------------------------------------------

legitimate = df[
    df["isFraud"] == 0
].copy()

print(
    f"Legitimate transactions: "
    f"{len(legitimate)}"
)


# ------------------------------------------------------------
# LEGITIMATE TRANSFER SEEDS
# ------------------------------------------------------------

transfer_seeds = legitimate[
    legitimate["type"].astype(str) == "TRANSFER"
].copy()

if len(transfer_seeds) == 0:
    raise ValueError(
        "No legitimate TRANSFER transactions found."
    )


print(
    f"Legitimate transfer seeds: "
    f"{len(transfer_seeds)}"
)


# ------------------------------------------------------------
# AMOUNT STATISTICS
# ------------------------------------------------------------

amount_25th = float(
    legitimate["amount"].quantile(0.25)
)

amount_median = float(
    legitimate["amount"].median()
)

amount_75th = float(
    legitimate["amount"].quantile(0.75)
)

print(
    f"Legitimate amount 25th percentile: "
    f"{amount_25th:.2f}"
)

print(
    f"Legitimate amount median: "
    f"{amount_median:.2f}"
)

print(
    f"Legitimate amount 75th percentile: "
    f"{amount_75th:.2f}"
)


# ------------------------------------------------------------
# GENERATE SCENARIOS
# ------------------------------------------------------------

synthetic_rows = []

record_counter = 1


for scenario_number in range(
    1,
    TARGET_SCENARIOS + 1
):

    scenario_id = (
        f"L09_{scenario_number:06d}"
    )

    # --------------------------------------------------------
    # Create four synthetic accounts
    # --------------------------------------------------------

    account_nodes = [
        f"CL{scenario_number:06d}_{i}"
        for i in range(1, 5)
    ]

    # A -> B
    # B -> C
    # C -> D
    # D -> A

    cycle_edges = [
        (
            account_nodes[0],
            account_nodes[1]
        ),
        (
            account_nodes[1],
            account_nodes[2]
        ),
        (
            account_nodes[2],
            account_nodes[3]
        ),
        (
            account_nodes[3],
            account_nodes[0]
        ),
    ]

    # --------------------------------------------------------
    # Scenario start step
    # --------------------------------------------------------

    scenario_start_step = int(
        np.random.randint(
            10,
            900
        )
    )

    # --------------------------------------------------------
    # Generate normal step gaps
    # --------------------------------------------------------

    step_gaps = []

    for position in range(CYCLE_LENGTH):

        if position == 0:
            gap = 0

        else:
            gap = int(
                np.random.randint(
                    1,
                    4
                )
            )

        step_gaps.append(gap)

    # --------------------------------------------------------
    # Generate transaction steps
    # --------------------------------------------------------

    steps = []

    current_step = scenario_start_step

    for position in range(CYCLE_LENGTH):

        if position > 0:
            current_step += step_gaps[position]

        steps.append(current_step)

    # --------------------------------------------------------
    # Scenario transaction amount
    #
    # Keep amounts moderate so that this is a legitimate
    # counterexample rather than an obviously suspicious
    # high-value circular transfer.
    # --------------------------------------------------------

    scenario_amounts = []

    for position in range(CYCLE_LENGTH):

        seed = transfer_seeds.sample(
            n=1
        ).iloc[0]

        seed_amount = float(
            seed["amount"]
        )

        # Keep amount around normal legitimate range.
        lower_bound = max(
            100.0,
            amount_25th * 0.75
        )

        upper_bound = min(
            amount_75th * 0.80,
            amount_median * 1.5
        )

        if upper_bound <= lower_bound:
            upper_bound = (
                lower_bound + 1000
            )

        amount = np.random.uniform(
            lower_bound,
            upper_bound
        )

        # Slight variation between cycle edges
        amount *= np.random.uniform(
            0.85,
            1.15
        )

        amount = round(
            amount,
            2
        )

        scenario_amounts.append(
            amount
        )

    # --------------------------------------------------------
    # Generate account balances
    #
    # Give each account sufficient balance so that the
    # transaction uses only a small portion of it.
    # --------------------------------------------------------

    account_balances = {}

    for account in account_nodes:

        balance = np.random.uniform(
            5 * amount_75th,
            10 * amount_75th
        )

        account_balances[account] = (
            round(balance, 2)
        )

    # --------------------------------------------------------
    # Create four transactions
    # --------------------------------------------------------

    for position in range(CYCLE_LENGTH):

        sender = cycle_edges[position][0]

        receiver = cycle_edges[position][1]

        amount = scenario_amounts[position]

        old_balance_org = (
            account_balances[sender]
        )

        # Ensure sufficient balance
        if old_balance_org <= amount:

            old_balance_org = round(
                amount * np.random.uniform(
                    5,
                    10
                ),
                2
            )

            account_balances[sender] = (
                old_balance_org
            )

        new_balance_org = (
            old_balance_org - amount
        )

        # ----------------------------------------------------
        # Destination balance
        # ----------------------------------------------------

        old_balance_dest = (
            account_balances[receiver]
        )

        new_balance_dest = (
            old_balance_dest + amount
        )

        # Update balances
        account_balances[sender] = (
            round(new_balance_org, 2)
        )

        account_balances[receiver] = (
            round(new_balance_dest, 2)
        )

        # ----------------------------------------------------
        # Balance usage ratio
        # ----------------------------------------------------

        balance_usage_ratio = (
            amount / old_balance_org
        )

        # ----------------------------------------------------
        # Scenario total
        # ----------------------------------------------------

        scenario_total_amount = sum(
            scenario_amounts
        )

        # ----------------------------------------------------
        # Create record
        # ----------------------------------------------------

        row = {
            "record_id": (
                f"L09_{record_counter:06d}"
            ),

            "step": steps[position],

            "type": "TRANSFER",

            "amount": amount,

            "nameOrig": sender,

            "oldbalanceOrg": round(
                old_balance_org,
                2
            ),

            "newbalanceOrig": round(
                new_balance_org,
                2
            ),

            "nameDest": receiver,

            "oldbalanceDest": round(
                old_balance_dest,
                2
            ),

            "newbalanceDest": round(
                new_balance_dest,
                2
            ),

            "isFraud": 0,

            "isFlaggedFraud": 0,

            "scenario_id": scenario_id,

            "scenario_type": (
                "LEGITIMATE_CIRCULAR_TRANSACTION"
            ),

            "severity": "NONE",

            "is_legitimate_counterexample": 1,

            "cycle_position": position + 1,

            "cycle_length": CYCLE_LENGTH,

            "step_gap_from_previous": (
                step_gaps[position]
            ),

            "scenario_step_window": (
                steps[-1] - steps[0]
            ),

            "scenario_total_amount": round(
                scenario_total_amount,
                2
            ),

            "balance_usage_ratio": round(
                balance_usage_ratio,
                6
            ),

            "historical_pattern": "NORMAL",

            "cycle_pattern": (
                "A->B->C->D->A"
            ),
        }

        synthetic_rows.append(row)

        record_counter += 1


# ------------------------------------------------------------
# CREATE DATAFRAME
# ------------------------------------------------------------

synthetic = pd.DataFrame(
    synthetic_rows
)


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

print()
print("=" * 60)
print("L09 VALIDATION")
print("=" * 60)

print(
    f"Rows: {len(synthetic)}"
)

print(
    f"Fraud labels: "
    f"{synthetic['isFraud'].value_counts().to_dict()}"
)

print(
    f"Transaction types: "
    f"{synthetic['type'].value_counts().to_dict()}"
)

print(
    f"Unique accounts: "
    f"{pd.concat([synthetic['nameOrig'], synthetic['nameDest']]).nunique()}"
)

print(
    f"Unique scenarios: "
    f"{synthetic['scenario_id'].nunique()}"
)

transactions_per_scenario = (
    synthetic
    .groupby("scenario_id")
    .size()
)

print(
    f"Average transactions per scenario: "
    f"{transactions_per_scenario.mean():.1f}"
)

print(
    f"Minimum transactions per scenario: "
    f"{transactions_per_scenario.min()}"
)

print(
    f"Maximum transactions per scenario: "
    f"{transactions_per_scenario.max()}"
)


# ------------------------------------------------------------
# CYCLE VALIDATION
# ------------------------------------------------------------

valid_cycles = 0

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

    cycle_is_valid = (
        len(group) == 4
        and destinations[0] == senders[1]
        and destinations[1] == senders[2]
        and destinations[2] == senders[3]
        and destinations[3] == senders[0]
    )

    if cycle_is_valid:
        valid_cycles += 1


print(
    f"Valid circular scenarios: "
    f"{valid_cycles} / {TARGET_SCENARIOS}"
)


# ------------------------------------------------------------
# AMOUNT VALIDATION
# ------------------------------------------------------------

print(
    f"Average amount: "
    f"{synthetic['amount'].mean():.2f}"
)

print(
    f"Median amount: "
    f"{synthetic['amount'].median():.2f}"
)

print(
    f"Minimum amount: "
    f"{synthetic['amount'].min():.2f}"
)

print(
    f"Maximum amount: "
    f"{synthetic['amount'].max():.2f}"
)


# ------------------------------------------------------------
# STEP WINDOW
# ------------------------------------------------------------

print(
    f"Average scenario step window: "
    f"{synthetic.groupby('scenario_id')['step'].agg(lambda x: x.max() - x.min()).mean():.2f}"
)

print(
    f"Maximum scenario step window: "
    f"{synthetic.groupby('scenario_id')['step'].agg(lambda x: x.max() - x.min()).max()}"
)


# ------------------------------------------------------------
# BALANCE USAGE
# ------------------------------------------------------------

print(
    f"Average balance usage: "
    f"{synthetic['balance_usage_ratio'].mean() * 100:.2f} %"
)

print(
    f"Maximum balance usage: "
    f"{synthetic['balance_usage_ratio'].max() * 100:.2f} %"
)


# ------------------------------------------------------------
# ASSERTIONS
# ------------------------------------------------------------

assert len(synthetic) == TARGET_ROWS

assert synthetic["isFraud"].eq(0).all()

assert synthetic[
    "is_legitimate_counterexample"
].eq(1).all()

assert synthetic[
    "scenario_type"
].eq(
    "LEGITIMATE_CIRCULAR_TRANSACTION"
).all()

assert synthetic[
    "type"
].eq("TRANSFER").all()

assert (
    synthetic["scenario_id"].nunique()
    == TARGET_SCENARIOS
)

assert (
    transactions_per_scenario.min()
    == CYCLE_LENGTH
)

assert (
    transactions_per_scenario.max()
    == CYCLE_LENGTH
)

assert valid_cycles == TARGET_SCENARIOS

assert (
    synthetic["amount"] > 0
).all()

assert (
    synthetic["balance_usage_ratio"] < 1
).all()


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

os.makedirs(
    "data",
    exist_ok=True
)

synthetic.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print(
    f"Saved: {OUTPUT_FILE}"
)

print(
    f"Final shape: {synthetic.shape}"
)


# ------------------------------------------------------------
# SAMPLE
# ------------------------------------------------------------

print()
print("Sample cycle:")

print(
    synthetic[
        [
            "record_id",
            "step",
            "type",
            "amount",
            "nameOrig",
            "nameDest",
            "scenario_id",
            "scenario_type",
            "cycle_position",
            "cycle_length",
            "step_gap_from_previous",
            "balance_usage_ratio",
        ]
    ]
    .head(8)
    .to_string(index=False)
)