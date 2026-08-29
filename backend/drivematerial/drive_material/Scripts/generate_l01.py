import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_L01_legitimate_high_value.csv"

TARGET_ROWS = 4000

RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


# ============================================================
# LOAD BASE DATASET
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
# LEGITIMATE HIGH-VALUE RANGE
# ============================================================

legitimate_95th = legit[
    "amount"
].quantile(0.95)

legitimate_99th = legit[
    "amount"
].quantile(0.99)

legitimate_max = legit[
    "amount"
].max()

print(
    "Legitimate 95th percentile:",
    round(
        legitimate_95th,
        2
    )
)

print(
    "Legitimate 99th percentile:",
    round(
        legitimate_99th,
        2
    )
)

print(
    "Legitimate maximum:",
    round(
        legitimate_max,
        2
    )
)


# ============================================================
# SELECT HIGH-VALUE LEGITIMATE SEEDS
# ============================================================

high_value_seeds = legit[
    legit["amount"] >= legitimate_95th
].copy()

print(
    "High-value legitimate seeds:",
    len(high_value_seeds)
)


if len(high_value_seeds) < TARGET_ROWS:

    raise ValueError(
        "Not enough legitimate high-value transactions."
    )


# ============================================================
# SAMPLE SEEDS
# ============================================================

seeds = high_value_seeds.sample(
    n=TARGET_ROWS,
    replace=False,
    random_state=RANDOM_SEED
).copy()

seeds = seeds.reset_index(
    drop=True
)


# ============================================================
# CREATE SYNTHETIC LEGITIMATE DATA
# ============================================================

synthetic = seeds.copy()


# ============================================================
# SYNTHETIC RECORD IDS
# ============================================================

synthetic[
    "record_id"
] = [
    f"L01_{i:06d}"
    for i in range(
        1,
        TARGET_ROWS + 1
    )
]


# ============================================================
# KEEP TRANSACTION TYPE
# ============================================================

# We intentionally preserve the original
# legitimate transaction type.


# ============================================================
# SLIGHT AMOUNT VARIATION
# ============================================================

synthetic[
    "amount"
] = (
    synthetic["amount"] *
    np.random.uniform(
        0.95,
        1.05,
        TARGET_ROWS
    )
)


# Keep values inside the legitimate range.

# Round the threshold first so that
# validation and generated amounts use
# the exact same 2-decimal boundary.

legitimate_95th = round(
    legitimate_95th,
    2
)

synthetic[
    "amount"
] = synthetic[
    "amount"
].clip(
    lower=legitimate_95th,
    upper=legitimate_max * 0.98
)

synthetic[
    "amount"
] = synthetic[
    "amount"
].round(2)

# Final safety clip after rounding

synthetic[
    "amount"
] = synthetic[
    "amount"
].clip(
    lower=legitimate_95th,
    upper=legitimate_max
)

synthetic[
    "amount"
] = synthetic[
    "amount"
].round(2)

# ============================================================
# RE-CALCULATE BALANCES
# ============================================================

for idx in synthetic.index:

    amount = float(
        synthetic.loc[
            idx,
            "amount"
        ]
    )

    old_balance = float(
        synthetic.loc[
            idx,
            "oldbalanceOrg"
        ]
    )

    # Make sure legitimate transaction
    # has enough balance.

    if old_balance <= amount:

        old_balance = (
            amount *
            np.random.uniform(
                1.5,
                3.0
            )
        )

    new_balance = (
        old_balance -
        amount
    )

    synthetic.loc[
        idx,
        "oldbalanceOrg"
    ] = round(
        old_balance,
        2
    )

    synthetic.loc[
        idx,
        "newbalanceOrig"
    ] = round(
        new_balance,
        2
    )


# ============================================================
# DESTINATION BALANCES
# ============================================================

synthetic[
    "oldbalanceDest"
] = synthetic[
    "oldbalanceDest"
].fillna(0.0)

synthetic[
    "newbalanceDest"
] = (
    synthetic[
        "oldbalanceDest"
    ] +
    synthetic[
        "amount"
    ]
).round(2)


# ============================================================
# FRAUD LABEL
# ============================================================

synthetic[
    "isFraud"
] = 0

synthetic[
    "isFlaggedFraud"
] = 0


# ============================================================
# INVESTIGATOR METADATA
# ============================================================

synthetic[
    "scenario_id"
] = [
    f"L01_{i:05d}"
    for i in range(
        1,
        TARGET_ROWS + 1
    )
]

synthetic[
    "scenario_type"
] = (
    "LEGITIMATE_HIGH_VALUE"
)

synthetic[
    "fraud_reason"
] = (
    "High-value transaction within "
    "observed legitimate transaction "
    "distribution"
)

synthetic[
    "severity"
] = "NONE"


# ============================================================
# LEGITIMACY FEATURES
# ============================================================

synthetic[
    "is_legitimate_counterexample"
] = 1

synthetic[
    "amount_percentile_flag"
] = (
    synthetic["amount"] >=
    legitimate_95th
).astype(int)

synthetic[
    "balance_usage_ratio"
] = (
    synthetic["amount"] /
    synthetic["oldbalanceOrg"]
).round(4)


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("L01 VALIDATION")
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
    "Minimum amount:",
    round(
        synthetic[
            "amount"
        ].min(),
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
    "Percentage above legitimate 95th percentile:",
    round(
        (
            synthetic["amount"]
            >= legitimate_95th
        ).mean() * 100,
        2
    ),
    "%"
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


# ============================================================
# ASSERTIONS
# ============================================================

assert len(synthetic) == TARGET_ROWS

assert (
    synthetic["isFraud"] == 0
).all()

assert (
    synthetic["isFlaggedFraud"] == 0
).all()

assert (
    synthetic[
        "scenario_type"
    ] ==
    "LEGITIMATE_HIGH_VALUE"
).all()

assert (
    synthetic[
        "is_legitimate_counterexample"
    ] == 1
).all()

assert (
    synthetic["amount"] >=
    legitimate_95th
).all()

assert (
    synthetic["amount"] <=
    legitimate_max
).all()

assert (
    synthetic[
        "balance_usage_ratio"
    ] < 1
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
            "severity"
        ]
    ].head(10)
)