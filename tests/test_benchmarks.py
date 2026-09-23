from nutrition_engine.benchmarks import (
    MACRO_BENCHMARKS,
    MAE_TARGET_PERCENT,
    SCALING_BENCHMARKS,
    calculate_f1_score,
    calculate_mae_percent,
    run_extra_scaling_checks,
    run_macro_benchmarks,
    run_scaling_benchmarks,
    track_constraint_compliance,
)


def test_macro_benchmark_dataset_has_enough_cases():
    assert len(MACRO_BENCHMARKS) >= 5


def test_scaling_benchmark_dataset_has_enough_cases():
    assert len(SCALING_BENCHMARKS) >= 3


def test_every_macro_benchmark_passes():
    # Every deterministic reference case must pass before agent work is judged.
    results = run_macro_benchmarks()
    failures = [result for result in results if not result["passed"]]

    assert failures == []


def test_every_scaling_benchmark_passes():
    results = run_scaling_benchmarks()
    failures = [result for result in results if not result["passed"]]

    assert failures == []


def test_target_quantity_and_serving_benchmarks_pass():
    results = run_extra_scaling_checks()
    failures = [result for result in results if not result["passed"]]

    assert failures == []


def test_exact_macro_benchmarks_meet_mae_target():
    # The baseline establishes the <2% error target used for future systems.
    results = run_macro_benchmarks()
    actual = [result["actual"].protein_g for result in results]
    expected = [case.expected_protein_g for case in MACRO_BENCHMARKS]

    assert calculate_mae_percent(actual, expected) < MAE_TARGET_PERCENT


def test_f1_baseline_and_constraint_compliance_tracker():
    # Perfect labels define the initial F1 reference; the tracker covers both
    # protein minimum and calorie maximum in one compliance result.
    assert calculate_f1_score([True, True, False], [True, True, False]) == 1.0

    tracker = track_constraint_compliance(
        [
            {"protein_g": 140, "calories": 1_900},
            {"protein_g": 120, "calories": 1_800},
            {"protein_g": 150, "calories": 2_100},
        ]
    )

    assert tracker["compliant_meals"] == 1
    assert tracker["compliance_rate"] == 0.3333
