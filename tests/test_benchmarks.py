from nutrition_engine.benchmarks import (
    MACRO_BENCHMARKS,
    SCALING_BENCHMARKS,
    run_extra_scaling_checks,
    run_macro_benchmarks,
    run_scaling_benchmarks,
)


def test_macro_benchmark_dataset_has_enough_cases():
    assert len(MACRO_BENCHMARKS) >= 5


def test_scaling_benchmark_dataset_has_enough_cases():
    assert len(SCALING_BENCHMARKS) >= 3


def test_every_macro_benchmark_passes():
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
