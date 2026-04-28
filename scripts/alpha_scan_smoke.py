#!/usr/bin/env python3
import subprocess
import os
import argparse
import time
import sys

def run(cmd):
    print('\n$ ' + ' '.join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_samples', type=int, default=10)
    parser.add_argument('--out_base', default='results/alpha_smoke')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    os.makedirs(args.out_base, exist_ok=True)

    common = [
        sys.executable, 'run_minimal_poc.py',
        '--data', 'nyu', '--nyu_mat', 'data/nyu_depth_v2_labeled.mat',
        '--num_samples', str(args.num_samples), '--height', '240', '--width', '320',
        '--seed', str(args.seed),
        '--fixed_alpha', '0.25', '--fixed_radius', '3', '--fixed_iterations', '1',
        '--adaptive_alpha_min', '0.01', '--adaptive_radius', '3', '--adaptive_iterations', '1',
        '--adaptive_selection_lambda', '0.5'
    ]

    exps = []
    # baseline linear
    exps.append(('cfg_linear', ['--adaptive_alpha_map', 'linear']))

    # gamma variants (vary gamma and adaptive_alpha_max)
    for gamma in [1.4, 1.6, 1.8]:
        for amax in [0.14, 0.18, 0.22]:
            name = f'cfg_gamma_{gamma}_amax_{amax}'.replace('.', 'p')
            extra = ['--adaptive_alpha_map', 'gamma', '--adaptive_alpha_gamma', str(gamma), '--adaptive_alpha_max', str(amax)]
            exps.append((name, extra))

    # piecewise variants (vary top gain)
    for top in [0.05, 0.10, 0.15]:
        name = f'cfg_piecewise_top_{top}'.replace('.', 'p')
        extra = ['--adaptive_alpha_map', 'piecewise', '--adaptive_piecewise_low', '0.3', '--adaptive_piecewise_high', '0.75', '--adaptive_piecewise_top_gain', str(top), '--adaptive_alpha_cap', '0.15']
        exps.append((name, extra))

    for name, extra in exps:
        out_dir = os.path.join(args.out_base, name)
        os.makedirs(out_dir, exist_ok=True)
        cmd = common + ['--out_dir', out_dir] + extra
        print('=' * 72)
        print('Running experiment:', name)
        run(cmd)
        time.sleep(1)


if __name__ == '__main__':
    main()
