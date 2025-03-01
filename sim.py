# %%
# sp.integrate(calc_integrand_1(2), (t, 1 / 2, x))

# %%


# %%




# def g_opt_inf(x):
#     return 3.0 * x**4 - 8.0 * x**3 + 6.0 * x**2


# # Generate random configurations

# %%


# %%


# %%


# %%
# min_c_list = np.geomspace(1e-10, 1e-5, 100)
# min_c_list

# %%

# def normalized_scoring_rule(p):
#     return unnormalized_scoring_rule(p) / integrate.quad(unnormalized_scoring_rule, 0, 1)[0]

import numpy as np
import scipy.integrate as spi
from src.utils import *
import matplotlib.pyplot as plt

from dataclasses import dataclass, asdict
from typing import Callable

scoring_rules = {
    "logarithmic": logarithmic_scoring_rule,
    "spherical": spherical_scoring_rule,
    "quadratic": quadratic_scoring_rule,
    "optimal": g_opt_inf,
    # "g_opt_1": g_opt_1_poly,
    # "g_opt_2": g_opt_2_poly,
}


def run_config(config):
    error, flips, cost = simulate_expert_flips_geometric_cost(
        true_bias=config.true_bias,
        scoring_rule_name=config.scoring_rule,
        base_cost=config.base_cost,
        alpha=config.alpha,
        ell=config.ell,
        start_decay_flips=config.start_decay_flips,
    )
    config = asdict(config)
    config['error'] = error
    config['flips'] = flips
    config["total_cost"] = cost
    return config

np.random.seed(42)  # For reproducibility

@dataclass
class Config:
    true_bias: float
    scoring_rule: str
    base_cost: float
    alpha: float
    # num_trials: int
    ell: float
    # seed: int
    start_decay_flips: int
    min_c: float

from tqdm.auto import tqdm
def generate_configs():
    configs = []
    results = []
    costs = np.geomspace(0.00003, 100, 1000)

    N = 10
    true_bias_list = list(0.5+np.linspace(0, 0.5, N//2))
    true_bias_list.extend(list(0.5-np.linspace(0, 0.5, N//2)))
    true_bias_list = np.array(sorted(list(set(true_bias_list))))[1:-1]
    # len(true_bias_list)
    # true_bias_list = [0.5, 0.5 -0.01, 0.5 +0.01]
    min_c_list = np.geomspace(1e-9, 1e-5, 10)
    start_decay_flips_list = [3, 10, 20, 50, 100, 1000, 10000, 100000]
    ell_list = [1, 2, 8, 20, 50, 100]

    # true_bias_list = np.linspace(0.01, 0.99, 30)
    alphas = [0.99, 0.999, 0.9999, 1, 1.0001, 1.001, 1.01]
    # for config_idx in range(N_CONFIGS):  # Generate 5 random configurations
    while True:
        rule_name = np.random.choice(list(scoring_rules.keys()))
        # rule_name = "optimal"
        cost = costs[np.random.randint(0, len(costs))]
        alpha = alphas[np.random.randint(0, len(alphas))]
        true_bias = true_bias_list[np.random.randint(0, len(true_bias_list))]

        config = Config(
            true_bias=true_bias,
            base_cost=cost,
            scoring_rule=rule_name,
            alpha=alpha,  # Random alpha between 0.8 and 1.2
            ell=ell_list[np.random.randint(0, len(ell_list))],  # Random ell between 1.5 and 3.0
            start_decay_flips=start_decay_flips_list[np.random.randint(0, len(start_decay_flips_list))],
            min_c=min_c_list[np.random.randint(0, len(min_c_list))],
        )
        yield config
    # configs.append(config)
    

configs = generate_configs()    
# len(configs)

# %%
from multiprocessing import Pool
from more_itertools import chunked

# Process configs in batches and write results incrementally

# N_CONFIGS = 200000000*3
import os
batch_size = 100000
# total_batches = (N_CONFIGS + batch_size - 1) // batch_size

with open('simulation_results.csv', 'w') as f:
    # Write header first
    dummy_result = run_config(next(configs))
    df_header = pd.DataFrame([dummy_result])
    df_header.to_csv(f, index=False)
    f.flush()

    # Process and write batches
    with Pool() as pool:
        itr = pool.imap(run_config, configs)
        pbar = tqdm(chunked(itr, batch_size), desc='Processing batches')
        for batch in pbar:
            if os.path.getsize('simulation_results.csv') >= 5 * 1024 * 1024 * 1024:  # 5GB
                break
            df_batch = pd.DataFrame(batch)
            df_batch.to_csv(f, index=False, header=False)
            f.flush()
            pbar.set_description(f'Processing batches (file size: {os.path.getsize("simulation_results.csv")/1024/1024:.1f}MB)')