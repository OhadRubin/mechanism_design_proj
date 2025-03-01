import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, Tuple
import seaborn as sns
import pandas as pd
import sympy as sp

# Set styling for better visualization
plt.style.use("seaborn-v0_8-whitegrid")
sns.set_palette("viridis")


def compute_expected_reward(scoring_rule, p):
    """Compute expected reward R_f(p) for a proper scoring rule f and belief p."""
    return p * scoring_rule(p) + (1 - p) * scoring_rule(1 - p)


# Definition 2.1 (Expected Reward). For scoring rule $f:(0,1) \rightarrow \mathbb{R}$, denote by $r_{p}^{f}(x):=$ $p \cdot f(x)+(1-p) \cdot f(1-x)$ the expected reward of an expert who predicts $x$ when their true belief is $p$.
# Let also $R^{f}(p):=r_{p}^{f}(p)$ be the expected reward of an expert who reports their true belief $p$. We may drop the superscript when the scoring rule $f$ is clear from context.


def compute_delta_reward(scoring_rule: Callable, k: int, n: int) -> float:
    """
    Compute the expected marginal gain ΔR_f(k,n) from one additional flip.

    Parameters:
    -----------
    scoring_rule : Callable
        The proper scoring rule function f(x) -> R
    k : int
        Number of heads observed so far
    n : int
        Total number of flips so far

    Returns:
    --------
    float
        The expected increase in reward from one additional flip

    Notes:
    ------
    This implements Lemma 2.6: If the expert has already flipped the coin n times,
    seeing k heads, then their expected increase in reward for exactly one additional
    flip is (k+1)/(n+2) * [R((k+2)/(n+3)) - R((k+1)/(n+2))] +
    (n-k+1)/(n+2) * [R((k+1)/(n+3)) - R((k+1)/(n+2))]
    """

    # Current posterior mean (belief)
    def R(p):
        return compute_expected_reward(scoring_rule, p)

    p1 = (k + 1) / (n + 2)
    p2 = (k + 2) / (n + 3)
    term1 = p1 * R(p2)

    p3 = (n + 1 - k) / (n + 2)
    p4 = (k + 1) / (n + 3)
    term2 = p3 * R(p4)

    p5 = p1
    term3 = -R(p5)
    return term1 + term2 + term3


def simulate_expert_flips_geometric_cost(
    true_bias: float,
    scoring_rule: Callable[[float], float],
    base_cost: float,
    alpha: float = 1.0,
    ell: float = 2.0,
    min_c: float = 1e-6,
    start_decay_flips=3,
) -> Tuple[float, float, list, list]:
    """
    Simulates expert behavior with geometric cost structure:
    - α=1: Constant cost c for each flip
    - 0<α<1: Decreasing cost α^(i-1)*c for the i-th flip
    - α>1: Increasing cost α^(i-1)*c for the i-th flip

    Args:
        scoring_rule: Function that takes prediction p and returns score
        base_cost: Base cost c per coin flip
        alpha: Factor for geometric progression (α)
        num_trials: Number of simulation trials
        ell: Power of error moment to optimize
        seed: Random seed for reproducibility
        start_decay_flips: Number of flips after which the cost starts to decay
    Returns:
        Tuple of (average ell-th power of absolute error, average number of flips,
                 list of all errors, list of all flip counts)
    """

    heads = 0
    flips = 0

    while True:
        # Calculate marginal gain from additional flip
        delta_reward = compute_delta_reward(scoring_rule, heads, flips)

        # Calculate cost of the next flip
        if flips < start_decay_flips:
            next_flip_cost = base_cost
        else:
            next_flip_cost = base_cost * (alpha ** (flips - start_decay_flips))
        next_flip_cost = np.where(next_flip_cost < min_c, min_c, next_flip_cost)

        # Stop if expected gain is less than cost
        if delta_reward < next_flip_cost:
            break

        # Simulate the actual flip
        if np.random.random() < true_bias:
            heads += 1
        flips += 1

    # Calculate final prediction and error
    final_pred = (heads + 1) / (flips + 2)
    error = abs(final_pred - true_bias) ** ell

    return error, flips


def create_logarithmic_scoring_rule():
    x = sp.Symbol("x")
    unnormalized_expr = sp.log(1 + x)
    # Compute the integral symbolically
    integral_value = float(sp.integrate(unnormalized_expr, (x, 0, 1)))

    def logarithmic_scoring_rule(p):
        return np.log1p(p) / integral_value

    return logarithmic_scoring_rule


def create_spherical_scoring_rule():
    x = sp.Symbol("x")
    unnormalized_expr = x / sp.sqrt(x**2 + (1 - x) ** 2)
    # Compute the integral symbolically
    integral_value = float(sp.integrate(unnormalized_expr, (x, 0, 1)))

    def spherical_scoring_rule(p):
        return p / np.sqrt(p**2 + (1 - p) ** 2) / integral_value

    return spherical_scoring_rule


# Define scoring rules from the paper


def create_quadratic_scoring_rule():
    # Define the symbolic integral for normalization
    x = sp.Symbol("x")
    unnormalized_expr = 2 * x - x**2
    # Compute the integral symbolically
    integral_value = float(sp.integrate(unnormalized_expr, (x, 0, 1)))

    def quadratic_scoring_rule(p):
        return (2 * p - p**2) / integral_value

    return quadratic_scoring_rule


logarithmic_scoring_rule = create_logarithmic_scoring_rule()
spherical_scoring_rule = create_spherical_scoring_rule()
quadratic_scoring_rule = create_quadratic_scoring_rule()
