import pandas as pd
import numpy as np

# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S06_transfer_cashout.csv"

TARGET_ROWS = 5000
TARGET_SCENARIOS = 2500

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

# We need legitimate transfers as seeds.
transfer_seeds = legit[
    (legit["type"] == "TRANSFER") &
    (legit["amount"] > 0) &
    (legit["nameOrig"].notna())
].copy()

print(
    "Legitimate transfer seeds:",
    len(transfer_seeds)
)

if len(transfer_seeds) == 0:
    raise ValueError(
        "No legitimate transfer seeds found."
    )

# ============================================================
# AMOUNT DISTRIBUTION
# ============================================================

transfer_95th = (
    transfer_seeds["amount"]
    .quantile(0.95)
)

transfer_50th = (
    transfer_seeds["amount"]
    .median()
)

print(
    "Transfer median:",
    round(transfer_50th, 2)
)

print(
    "Transfer 95th percentile:",
    round(transfer_95th, 2)
)

# ============================================================
# GENERATE S06
# ============================================================

synthetic_rows = []

scenario_number = 1

while scenario_number <= TARGET_SCENARIOS:

    # --------------------------------------------------------
    # Select transfer seed
    # --------------------------------------------------------

    seed = transfer_seeds.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    sender = seed["nameOrig"]

    # --------------------------------------------------------
    # Create a substantial transfer amount
    # --------------------------------------------------------

    transfer_amount = max(
        float(seed["amount"]) *
        np.random.uniform(
            1.0,
            2.0
        ),

        transfer_95th *
        np.random.uniform(
            0.60,
            1.00
        )
    )

    transfer_amount = round(
        transfer_amount,
        2
    )

    # --------------------------------------------------------
    # CASH_OUT amount
    # --------------------------------------------------------

    # Most of the transferred money gets withdrawn.

    cashout_ratio = np.random.uniform(
        0.75,
        0.95
    )

    cashout_amount = round(
        transfer_amount *
        cashout_ratio,
        2
    )

    # --------------------------------------------------------
    # Create sufficient sender balance
    # --------------------------------------------------------

    # Sender needs to be able to make the transfer.
    sender_balance = (
        transfer_amount *
        np.random.uniform(
            1.5,
            2.5
        )
    )

    sender_balance = max(
        sender_balance,
        50000
    )

    sender_after_transfer = (
        sender_balance -
        transfer_amount
    )

    # --------------------------------------------------------
    # Destination account
    # --------------------------------------------------------

    receiver = (
        "C_SYN_" +
        str(
            np.random.randint(
                100000000,
                999999999
            )
        )
    )

    # Destination receives transfer first.
    destination_before = 0.0

    destination_after_transfer = (
        transfer_amount
    )

    # Destination then cashes out most of it.
    destination_after_cashout = (
        destination_after_transfer -
        cashout_amount
    )

    # --------------------------------------------------------
    # Steps
    # --------------------------------------------------------

    base_step = int(
        seed["step"]
    )

    transfer_step = (
        base_step +
        np.random.randint(
            1,
            10
        )
    )

    # Cash-out occurs very shortly afterward.
    cashout_step = (
        transfer_step +
        np.random.randint(
            1,
            4
        )
    )

    # --------------------------------------------------------
    # IDs
    # --------------------------------------------------------

    transfer_record_id = (
        f"S06_{len(synthetic_rows)+1:06d}"
    )

    cashout_record_id = (
        f"S06_{len(synthetic_rows)+2:06d}"
    )

    scenario_id = (
        f"S06_{scenario_number:05d}"
    )

    # ========================================================
    # TRANSACTION 1 — TRANSFER
    # ========================================================

    transfer_row = {

        "record_id":
            transfer_record_id,

        "step":
            transfer_step,

        "type":
            "TRANSFER",

        "amount":
            transfer_amount,

        "nameOrig":
            sender,

        "oldbalanceOrg":
            round(
                sender_balance,
                2
            ),

        "newbalanceOrig":
            round(
                sender_after_transfer,
                2
            ),

        "nameDest":
            receiver,

        "oldbalanceDest":
            destination_before,

        "newbalanceDest":
            round(
                destination_after_transfer,
                2
            ),

        "isFraud":
            1,

        "isFlaggedFraud":
            0,

        "scenario_id":
            scenario_id,

        "scenario_type":
            "TRANSFER_THEN_CASH_OUT",

        "fraud_reason":
            "Large transfer followed by rapid cash withdrawal of most transferred funds",

        "severity":
            "CRITICAL",

        "chain_position":
            1,

        "chain_role":
            "TRANSFER",

        "chain_total_amount":
            round(
                transfer_amount +
                cashout_amount,
                2
            ),

        "cashout_ratio":
            round(
                cashout_ratio,
                4
            )
    }

    # ========================================================
    # TRANSACTION 2 — CASH_OUT
    # ========================================================

    cashout_row = {

        "record_id":
            cashout_record_id,

        "step":
            cashout_step,

        "type":
            "CASH_OUT",

        "amount":
            cashout_amount,

        "nameOrig":
            receiver,

        "oldbalanceOrg":
            round(
                destination_after_transfer,
                2
            ),

        "newbalanceOrig":
            round(
                destination_after_cashout,
                2
            ),

        "nameDest":
            "CASH_OUT",

        "oldbalanceDest":
            0.0,

        "newbalanceDest":
            0.0,

        "isFraud":
            1,

        "isFlaggedFraud":
            0,

        "scenario_id":
            scenario_id,

        "scenario_type":
            "TRANSFER_THEN_CASH_OUT",

        "fraud_reason":
            "Large transfer followed by rapid cash withdrawal of most transferred funds",

        "severity":
            "CRITICAL",

        "chain_position":
            2,

        "chain_role":
            "CASH_OUT",

        "chain_total_amount":
            round(
                transfer_amount +
                cashout_amount,
                2
            ),

        "cashout_ratio":
            round(
                cashout_ratio,
                4
            )
    }

    synthetic_rows.append(
        transfer_row
    )

    synthetic_rows.append(
        cashout_row
    )

    scenario_number += 1

# ============================================================
# DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)

# ============================================================
# VALIDATION METRICS
# ============================================================

synthetic["chain_id"] = (
    synthetic["scenario_id"]
)

# Time difference between transfer and cash-out
chain_steps = (
    synthetic
    .groupby("scenario_id")["step"]
    .agg(["min", "max"])
)

chain_steps["step_gap"] = (
    chain_steps["max"] -
    chain_steps["min"]
)

# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("S06 VALIDATION")
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
    "Average chain step gap:",
    round(
        chain_steps["step_gap"].mean(),
        2
    )
)

print(
    "Maximum chain step gap:",
    chain_steps["step_gap"].max()
)

print(
    "Average cash-out ratio:",
    round(
        synthetic[
            synthetic["chain_role"] ==
            "CASH_OUT"
        ]["cashout_ratio"].mean() * 100,
        2
    ),
    "%"
)

print(
    "Minimum cash-out ratio:",
    round(
        synthetic[
            synthetic["chain_role"] ==
            "CASH_OUT"
        ]["cashout_ratio"].min() * 100,
        2
    ),
    "%"
)

print(
    "Maximum cash-out ratio:",
    round(
        synthetic[
            synthetic["chain_role"] ==
            "CASH_OUT"
        ]["cashout_ratio"].max() * 100,
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
    "TRANSFER_THEN_CASH_OUT"
).all()

assert (
    synthetic["scenario_id"]
    .nunique()
    == TARGET_SCENARIOS
)

# Every scenario must contain exactly
# one TRANSFER and one CASH_OUT.

type_counts = (
    synthetic
    .groupby("scenario_id")["type"]
    .value_counts()
    .unstack(fill_value=0)
)

assert (
    type_counts["TRANSFER"] == 1
).all()

assert (
    type_counts["CASH_OUT"] == 1
).all()

# Cash-out must happen after transfer.
for scenario_id, group in synthetic.groupby(
    "scenario_id"
):

    transfer_step = group[
        group["type"] == "TRANSFER"
    ]["step"].iloc[0]

    cashout_step = group[
        group["type"] == "CASH_OUT"
    ]["step"].iloc[0]

    assert cashout_step > transfer_step

# Cash-out must occur within 3 steps.
assert (
    chain_steps["step_gap"] <= 3
).all()

# At least 75% of transferred amount gets cashed out.
assert (
    synthetic[
        synthetic["chain_role"] ==
        "CASH_OUT"
    ]["cashout_ratio"] >= 0.75
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
print("Sample chain:")

sample_scenario = (
    synthetic["scenario_id"]
    .iloc[0]
)

print(
    synthetic[
        synthetic["scenario_id"] ==
        sample_scenario
    ][
        [
            "record_id",
            "step",
            "type",
            "amount",
            "nameOrig",
            "nameDest",
            "scenario_id",
            "chain_position",
            "chain_role",
            "cashout_ratio"
        ]
    ]
)