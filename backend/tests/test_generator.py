from decimal import Decimal

from app.services.generator import calculate_llm_cost


def test_calculate_llm_cost():
    # 1M входных + 1M выходных = 31.01 + 206.50 = 237.51
    assert calculate_llm_cost(1_000_000, 1_000_000) == Decimal("237.51")


def test_calculate_llm_cost_small():
    # 1000 входных + 500 выходных
    # 1000/1M * 31.01 + 500/1M * 206.50 = 0.03101 + 0.10325 = 0.13
    assert calculate_llm_cost(1000, 500) == Decimal("0.13")
