from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from scipy import stats

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'pdf.fonttype': 42,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

C_CPP  = '#1f3a93'
C_RUST = '#c0392b'
C_R    = '#16a085'

LANG_COLOR  = {'cpp': C_CPP, 'rust': C_RUST, 'r': C_R}
LANG_MARKER = {'cpp': 'o',   'rust': 's',    'r': '^'}
LANG_LABEL  = {'cpp': 'C++', 'rust': 'Rust', 'r': 'R'}

OUTPUT_DIR = Path('./output')


def load_results(csv_path: Path) -> dict:
    rows = []
    with open(csv_path, newline='') as f:
        for r in csv.DictReader(f):
            rows.append({
                'algorithm': r['algorithm'],
                'language':  r['language'],
                'n':         int(r['n']),
                'time_ns':   float(r['time_ns_median']),
                'time_lo':   float(r['time_ns_ci_lo']),
                'time_hi':   float(r['time_ns_ci_hi']),
                'peak_b':    float(r['peak_bytes']) if r['peak_bytes'] else float('nan'),
            })

    results: dict = {}
    for r in rows:
        results.setdefault(r['algorithm'], {}).setdefault(r['language'], []).append(r)

    for algo, langs in results.items():
        for lang, lst in langs.items():
            lst.sort(key=lambda x: x['n'])
            langs[lang] = {
                'n':          np.array([x['n']       for x in lst]),
                'time_ms':    np.array([x['time_ns'] for x in lst]) / 1e6,
                'time_ms_lo': np.array([x['time_lo'] for x in lst]) / 1e6,
                'time_ms_hi': np.array([x['time_hi'] for x in lst]) / 1e6,
                'peak_b':     np.array([x['peak_b']  for x in lst]),
            }
    return results


def _fmt_time_ms(ms: float) -> str:
    if ms >= 1000:
        return f'{ms/1000:.2f} s'
    if ms >= 1:
        return f'{ms:.2f} ms'
    if ms >= 1e-3:
        return f'{ms*1e3:.2f} µs'
    return f'{ms*1e6:.0f} ns'


def _fmt_bytes(b: float) -> str:
    if np.isnan(b):
        return '-'
    if b < 1e3:
        return f'{b:.0f} B'
    if b < 1e6:
        return f'{b/1e3:.1f} KB'
    if b < 1e9:
        return f'{b/1e6:.1f} MB'
    return f'{b/1e9:.2f} GB'


def analyse_speedups(results: dict) -> list[dict]:
    rows = []
    for algo, langs in results.items():
        langs_present = sorted(langs.keys())
        if len(langs_present) < 2:
            continue
        for i, a in enumerate(langs_present):
            for b in langs_present[i+1:]:
                ns = np.intersect1d(langs[a]['n'], langs[b]['n'])
                for n in ns:
                    ia = int(np.where(langs[a]['n'] == n)[0][0])
                    ib = int(np.where(langs[b]['n'] == n)[0][0])
                    ta = langs[a]['time_ms'][ia]
                    tb = langs[b]['time_ms'][ib]
                    if ta <= tb:
                        fast, slow = a, b
                        t_fast, t_slow = ta, tb
                        t_fast_lo = langs[a]['time_ms_lo'][ia]
                        t_fast_hi = langs[a]['time_ms_hi'][ia]
                        t_slow_lo = langs[b]['time_ms_lo'][ib]
                        t_slow_hi = langs[b]['time_ms_hi'][ib]
                    else:
                        fast, slow = b, a
                        t_fast, t_slow = tb, ta
                        t_fast_lo = langs[b]['time_ms_lo'][ib]
                        t_fast_hi = langs[b]['time_ms_hi'][ib]
                        t_slow_lo = langs[a]['time_ms_lo'][ia]
                        t_slow_hi = langs[a]['time_ms_hi'][ia]

                    ratio = t_slow / t_fast
                    ratio_lo = t_slow_lo / t_fast_hi
                    ratio_hi = t_slow_hi / t_fast_lo

                    fast_hi = max(t_fast_lo, t_fast_hi)
                    slow_lo = min(t_slow_lo, t_slow_hi)
                    resolved = slow_lo > fast_hi

                    rows.append({
                        'algorithm': algo,
                        'n': int(n),
                        'fast': fast, 'slow': slow,
                        't_fast_ms': t_fast, 't_slow_ms': t_slow,
                        'ratio': ratio,
                        'ratio_lo': ratio_lo,
                        'ratio_hi': ratio_hi,
                        'resolved_at_95ci': resolved,
                    })
    return rows


def welch_from_ci(median_a: float, ci_lo_a: float, ci_hi_a: float, n_a: int,
                  median_b: float, ci_lo_b: float, ci_hi_b: float, n_b: int
                  ) -> tuple[float, float]:
    t_crit_a = stats.t.ppf(0.975, df=n_a - 1)
    t_crit_b = stats.t.ppf(0.975, df=n_b - 1)
    se_a = (ci_hi_a - ci_lo_a) / (2 * t_crit_a)
    se_b = (ci_hi_b - ci_lo_b) / (2 * t_crit_b)

    diff = median_a - median_b
    se_diff = np.sqrt(se_a**2 + se_b**2)
    t_stat = diff / se_diff

    df = (se_a**2 + se_b**2)**2 / (
        (se_a**4) / (n_a - 1) + (se_b**4) / (n_b - 1)
    )
    p = 2 * (1 - stats.t.cdf(abs(t_stat), df=df))
    return float(t_stat), float(p)


def analyse_scaling(results: dict, n_boot: int = 5000,
                    rng_seed: int = 42) -> list[dict]:
    rng = np.random.default_rng(rng_seed)
    rows = []
    for algo, langs in results.items():
        for lang, d in langs.items():
            n = d['n']; t = d['time_ms']
            if len(n) < 3:
                continue
            log_n = np.log(n); log_t = np.log(t)

            slope, intercept = np.polyfit(log_n, log_t, deg=1)

            slopes = np.empty(n_boot)
            idx = np.arange(len(n))
            for i in range(n_boot):
                pick = rng.choice(idx, size=len(idx), replace=True)
                if len(np.unique(pick)) < 2:
                    slopes[i] = np.nan
                    continue
                s, _ = np.polyfit(log_n[pick], log_t[pick], deg=1)
                slopes[i] = s
            slopes = slopes[~np.isnan(slopes)]
            lo, hi = np.percentile(slopes, [2.5, 97.5])

            rows.append({
                'algorithm': algo,
                'language': lang,
                'slope': float(slope),
                'slope_lo': float(lo),
                'slope_hi': float(hi),
                'intercept': float(intercept),
                'n_points': int(len(n)),
            })
    return rows


def make_overview(results: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.5))

    # KMP
    ax = axes[0, 0]; d = results['kmp']
    ax.loglog(d['cpp']['n'],  d['cpp']['time_ms'],  'o-',
              color=C_CPP,  lw=2, ms=7, label='C++ (SeqAn3)')
    ax.loglog(d['rust']['n'], d['rust']['time_ms'], 's-',
              color=C_RUST, lw=2, ms=7, label='Rust (rust-bio)')
    ax.set_title('KMP', pad=8)
    ax.set_xlabel('n (bytes)'); ax.set_ylabel('time (ms)')
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    ax.grid(True, which='both', alpha=0.25)

    # Smith-Waterman
    ax = axes[0, 1]; d = results['smith_waterman']
    ax.loglog(d['cpp']['n'],  d['cpp']['time_ms'],  'o-',
              color=C_CPP,  lw=2, ms=7, label='C++ (SSW)')
    ax.loglog(d['rust']['n'], d['rust']['time_ms'], 's-',
              color=C_RUST, lw=2, ms=7, label='Rust (rust-bio)')
    ax.set_title('Smith-Waterman', pad=8)
    ax.set_xlabel('n (bp)'); ax.set_ylabel('time (ms)')
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    ax.grid(True, which='both', alpha=0.25)

    # Needleman-Wunsch
    ax = axes[1, 0]; d = results['needleman_wunsch']
    ax.loglog(d['r']['n'],    d['r']['time_ms'],    '^-',
              color=C_R,    lw=2, ms=7, label='R (pwalign)')
    ax.loglog(d['rust']['n'], d['rust']['time_ms'], 's-',
              color=C_RUST, lw=2, ms=7, label='Rust (rust-bio)')
    ax.set_title('Needleman-Wunsch', pad=8)
    ax.set_xlabel('n (bp)'); ax.set_ylabel('time (ms)')
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    ax.grid(True, which='both', alpha=0.25)

    # Tree traversal
    ax = axes[1, 1]; d = results['tree_traversal']
    ax.loglog(d['cpp']['n'],  d['cpp']['time_ms'],  'o-',
              color=C_CPP,  lw=2, ms=7, label='C++ (CompactTree)')
    ax.loglog(d['r']['n'],    d['r']['time_ms'],    '^-',
              color=C_R,    lw=2, ms=7, label='R (ape)')
    ax.loglog(d['rust']['n'], d['rust']['time_ms'], 's-',
              color=C_RUST, lw=2, ms=7, label='Rust (phylo-rs)')

    rust_max_n  = d['rust']['n'][-1]
    rust_max_ms = d['rust']['time_ms'][-1]
    ax.annotate(_fmt_time_ms(rust_max_ms),
                xy=(rust_max_n, rust_max_ms),
                xytext=(rust_max_n*0.15, rust_max_ms*0.2),
                fontsize=11, fontweight='bold', color=C_RUST,
                arrowprops=dict(arrowstyle='->', color=C_RUST, lw=1.2))

    ax.set_title('Tree traversal', pad=8)
    ax.set_xlabel('n (tips)'); ax.set_ylabel('time (ms)')
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    ax.grid(True, which='both', alpha=0.25)

    fig.suptitle('Wall time vs. n across all four primitives (log-log)',
                 fontsize=14, y=1.00, fontweight='bold')
    plt.tight_layout()
    plt.savefig(out_path); plt.close()


def make_tree(results: dict, out_path: Path) -> None:
    d = results['tree_traversal']
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.loglog(d['cpp']['n'],  d['cpp']['time_ms'],  'o-',
              color=C_CPP,  lw=2.5, ms=9, label='C++ (CompactTree)')
    ax.loglog(d['r']['n'],    d['r']['time_ms'],    '^-',
              color=C_R,    lw=2.5, ms=9, label='R (ape)')
    ax.loglog(d['rust']['n'], d['rust']['time_ms'], 's-',
              color=C_RUST, lw=2.5, ms=9, label='Rust (phylo-rs)')

    for lang in ('cpp', 'r', 'rust'):
        ax.fill_between(d[lang]['n'],
                        d[lang]['time_ms_lo'], d[lang]['time_ms_hi'],
                        color=LANG_COLOR[lang], alpha=0.15, lw=0)

    rust_max_n  = d['rust']['n'][-1]
    rust_max_ms = d['rust']['time_ms'][-1]
    ax.annotate(_fmt_time_ms(rust_max_ms),
                xy=(rust_max_n, rust_max_ms),
                xytext=(rust_max_n*0.22, rust_max_ms*0.3),
                fontsize=13, fontweight='bold', color=C_RUST,
                arrowprops=dict(arrowstyle='-', color=C_RUST, lw=1.5))

    ax.axvspan(1e3, 1e4, color='gray', alpha=0.08, lw=0)
    ax.text(np.sqrt(1e3 * 1e4), ax.get_ylim()[1] * 0.4,
            'Rust overtakes R\nin this band',
            ha='center', va='center', fontsize=10, style='italic',
            color='dimgray',
            bbox=dict(boxstyle='round,pad=0.3',
                      facecolor='white', edgecolor='lightgray', lw=0.5))

    ax.set_xlabel('n (tree tips)')
    ax.set_ylabel('time (ms, log scale)')
    ax.set_title('Tree traversal: Rust scales superlinearly while C++ and R remain near-linear',
                 pad=12, fontsize=13)
    ax.legend(loc='upper left', frameon=False)
    ax.grid(True, which='both', alpha=0.25)
    plt.savefig(out_path); plt.close()


def make_nw(results: dict, out_path: Path) -> None:
    d = results['needleman_wunsch']
    n = d['rust']['n']
    ratio = d['r']['time_ms'] / d['rust']['time_ms']

    ratio_lo = d['r']['time_ms_lo'] / d['rust']['time_ms_hi']
    ratio_hi = d['r']['time_ms_hi'] / d['rust']['time_ms_lo']
    yerr = np.vstack([ratio - ratio_lo, ratio_hi - ratio])

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.errorbar(n, ratio, yerr=yerr,
                fmt='o-', color=C_RUST, lw=2.5, ms=11,
                ecolor=C_RUST, elinewidth=1.5, capsize=6, alpha=0.95)
    ax.axhline(1.0, color='gray', linestyle='--', lw=1.5, alpha=0.7)
    ax.text(n[-1], 1.18, 'parity line', ha='right',
            color='gray', fontsize=11, style='italic')

    ax.annotate(f'{ratio[0]:.0f}x\n(interpreter overhead\ndominates)',
                xy=(n[0], ratio[0]), xytext=(n[0]*1.6, ratio[0]*0.85),
                fontsize=11, color=C_RUST,
                arrowprops=dict(arrowstyle='->', color=C_RUST, lw=1.3))
    ax.annotate(f'{ratio[-1]:.2f}x\n(within 1 %\nof parity)',
                xy=(n[-1], ratio[-1]), xytext=(n[-1]*0.45, 1.55),
                fontsize=11, color=C_RUST,
                arrowprops=dict(arrowstyle='->', color=C_RUST, lw=1.3))

    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('n (base pairs)')
    ax.set_ylabel('Rust speedup over R (log scale)')
    ax.set_title('Needleman-Wunsch: Rust\'s advantage collapses with sequence length',
                 pad=12, fontsize=13)
    ax.set_xticks(n)
    ax.get_xaxis().set_major_formatter(
        ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    ax.set_yticks([1, 2, 5, 10, 20, 50])
    ax.get_yaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.grid(True, which='both', alpha=0.25)
    plt.savefig(out_path); plt.close()


def make_sw(results: dict, out_path: Path) -> None:
    d = results['smith_waterman']
    t_cpp_ms  = d['cpp']['time_ms'][-1]
    t_rust_ms = d['rust']['time_ms'][-1]
    m_cpp_b   = d['cpp']['peak_b'][-1]
    m_rust_b  = d['rust']['peak_b'][-1]
    m_cpp_mb  = m_cpp_b  / 1e6
    m_rust_mb = m_rust_b / 1e6
    n_largest = int(d['cpp']['n'][-1])

    time_ratio = t_rust_ms / t_cpp_ms
    mem_ratio  = m_rust_mb / m_cpp_mb

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.5))
    langs  = ['C++\n(SSW)', 'Rust\n(rust-bio)']
    times  = [t_cpp_ms, t_rust_ms]
    mems   = [m_cpp_mb, m_rust_mb]
    colors = [C_CPP, C_RUST]

    bars1 = ax1.bar(langs, times, color=colors, width=0.55,
                    edgecolor='black', linewidth=0.6)
    ax1.set_ylabel('time (ms)')
    ax1.set_title('Wall time', pad=10)
    ax1.grid(True, axis='y', alpha=0.25)
    ax1.set_ylim(0, max(times)*1.25)
    for bar, val in zip(bars1, times):
        ax1.text(bar.get_x() + bar.get_width()/2,
                 val + max(times)*0.03,
                 f'{val:.1f} ms', ha='center',
                 fontsize=12, fontweight='bold')
    ax1.text(0.5, 0.93, f'{time_ratio:.1f}x gap',
             transform=ax1.transAxes, ha='center',
             fontsize=13, fontweight='bold', color='dimgray',
             bbox=dict(boxstyle='round,pad=0.4',
                       facecolor='white', edgecolor='gray'))

    bars2 = ax2.bar(langs, mems, color=colors, width=0.55,
                    edgecolor='black', linewidth=0.6)
    ax2.set_yscale('log')
    ax2.set_ylim(min(mems)*0.3, max(mems)*6)
    ax2.set_ylabel('peak memory (MB, log scale)')
    ax2.set_title('Peak heap allocation', pad=10)
    ax2.grid(True, axis='y', alpha=0.25, which='both')
    labels_mem = [_fmt_bytes(m_cpp_b), _fmt_bytes(m_rust_b)]
    for bar, val, lbl in zip(bars2, mems, labels_mem):
        ax2.text(bar.get_x() + bar.get_width()/2, val * 1.5, lbl,
                 ha='center', fontsize=12, fontweight='bold')
    ax2.text(0.5, 0.93, f'{mem_ratio:.0f}x gap',
             transform=ax2.transAxes, ha='center',
             fontsize=13, fontweight='bold', color='dimgray',
             bbox=dict(boxstyle='round,pad=0.4',
                       facecolor='white', edgecolor='gray'))

    fig.suptitle(f'Smith-Waterman at n = {n_largest:,} bp', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(out_path); plt.close()


def make_kmp_ratio(results: dict, out_path: Path) -> None:
    d = results['kmp']
    n = d['cpp']['n']
    ratio = d['rust']['time_ms'] / d['cpp']['time_ms']
    ratio_lo = d['rust']['time_ms_lo'] / d['cpp']['time_ms_hi']
    ratio_hi = d['rust']['time_ms_hi'] / d['cpp']['time_ms_lo']
    yerr = np.vstack([ratio - ratio_lo, ratio_hi - ratio])

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.errorbar(n, ratio, yerr=yerr,
                fmt='o-', color=C_CPP, lw=2.5, ms=3,
                ecolor=C_CPP, elinewidth=2.0, capsize=10, alpha=0.95)
    ax.axhline(1.0, color='gray', linestyle='--', lw=1.5, alpha=0.7)
    ax.text(n[-1], 1.06, 'parity', ha='right',
            color='gray', fontsize=11, style='italic')

    ax.set_xscale('log')
    ax.set_xlabel('n (text length, bytes)')
    ax.set_ylabel('C++ speedup over Rust')
    ax.set_title('KMP: ratio narrows as the working set grows',
                 pad=12, fontsize=13)
    ax.set_xticks(n)
    ax.get_xaxis().set_major_formatter(
        ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    ax.set_ylim(0, max(ratio) * 1.25)
    ax.grid(True, which='major', alpha=0.25)
    plt.savefig(out_path); plt.close()


def make_scaling(scaling_rows: list[dict], out_path: Path) -> None:
    expected = {
        'kmp':              1.0,
        'tree_traversal':   1.0,
        'smith_waterman':   2.0,
        'needleman_wunsch': 2.0,
    }
    pretty = {
        'kmp':              'KMP',
        'smith_waterman':   'Smith-Waterman',
        'needleman_wunsch': 'Needleman-Wunsch',
        'tree_traversal':   'Tree traversal',
    }
    expected_x = sorted(set(expected.values()))

    fig, ax = plt.subplots(figsize=(10, 6))
    for x in expected_x:
        ax.axvline(x, color='gray', lw=1.0, linestyle='--', alpha=0.55)

    y = 0
    yticks = []; ylabels = []
    for algo in ['kmp', 'smith_waterman', 'needleman_wunsch', 'tree_traversal']:
        algo_rows = [r for r in scaling_rows if r['algorithm'] == algo]
        algo_rows.sort(key=lambda r: r['language'])
        for r in algo_rows:
            color = LANG_COLOR[r['language']]
            label = LANG_LABEL[r['language']]
            xerr_lo = r['slope'] - r['slope_lo']
            xerr_hi = r['slope_hi'] - r['slope']
            ax.errorbar(r['slope'], y,
                        xerr=[[xerr_lo], [xerr_hi]],
                        fmt=LANG_MARKER[r['language']],
                        color=color, ms=10, lw=2, capsize=5,
                        markeredgecolor='black', markeredgewidth=0.6)
            ax.text(r['slope_hi'] + 0.05, y,
                    f'{label}: k = {r["slope"]:.2f}',
                    va='center', fontsize=10, color=color, fontweight='bold')
            y += 1
        yticks.append(y - len(algo_rows) / 2 - 0.5)
        ylabels.append(pretty[algo])
        y += 0.8

    ax.set_yticks(yticks); ax.set_yticklabels(ylabels)
    ax.invert_yaxis()
    ax.set_xlabel('Empirical scaling exponent  k   (fit:  t = a · n^k)')
    ax.set_title('Empirical scaling vs. theoretical complexity, with 95 % bootstrap CIs',
                 pad=12, fontsize=13)
    ax.set_xlim(0, max(r['slope_hi'] for r in scaling_rows) + 0.9)
    y_top = -1.5
    ax.set_ylim(y - 0.5, y_top)
    for x in expected_x:
        ax.text(x, y_top + 0.4, f'k = {x:.0f}  (expected)',
                ha='center', va='bottom', fontsize=10,
                color='dimgray', style='italic')
    ax.grid(True, axis='x', alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_path); plt.close()


def write_summary_table(results: dict, out_path: Path) -> None:
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['algorithm', 'language', 'n',
                    'time_median', 'time_ci_lo', 'time_ci_hi',
                    'peak_memory'])
        for algo in sorted(results):
            for lang in sorted(results[algo]):
                d = results[algo][lang]
                for i, n in enumerate(d['n']):
                    w.writerow([
                        algo, lang, int(n),
                        _fmt_time_ms(d['time_ms'][i]),
                        _fmt_time_ms(d['time_ms_lo'][i]),
                        _fmt_time_ms(d['time_ms_hi'][i]),
                        _fmt_bytes(d['peak_b'][i]),
                    ])


def write_speedups_table(rows: list[dict], out_path: Path) -> None:
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['algorithm', 'n', 'fast', 'slow',
                    'fast_time', 'slow_time',
                    'speedup', 'speedup_ci_lo', 'speedup_ci_hi',
                    'resolved_at_95ci'])
        for r in rows:
            w.writerow([
                r['algorithm'], r['n'], r['fast'], r['slow'],
                _fmt_time_ms(r['t_fast_ms']),
                _fmt_time_ms(r['t_slow_ms']),
                f'{r["ratio"]:.3f}',
                f'{r["ratio_lo"]:.3f}',
                f'{r["ratio_hi"]:.3f}',
                str(r['resolved_at_95ci']),
            ])


def write_scaling_table(rows: list[dict], out_path: Path) -> None:
    expected = {
        'kmp':              1.0,
        'tree_traversal':   1.0,
        'smith_waterman':   2.0,
        'needleman_wunsch': 2.0,
    }
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['algorithm', 'language',
                    'slope', 'slope_ci_lo', 'slope_ci_hi',
                    'expected_complexity'])
        for r in rows:
            w.writerow([
                r['algorithm'], r['language'],
                f'{r["slope"]:.3f}',
                f'{r["slope_lo"]:.3f}',
                f'{r["slope_hi"]:.3f}',
                expected[r['algorithm']],
            ])


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('results.csv')
    out_dir  = Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT_DIR

    if not csv_path.exists():
        sys.exit(f"error: {csv_path} not found")
    out_dir.mkdir(parents=True, exist_ok=True)

    results = load_results(csv_path)
    speedup_rows = analyse_speedups(results)
    scaling_rows = analyse_scaling(results)

    nw = results['needleman_wunsch']
    i = int(np.where(nw['rust']['n'] == 5000)[0][0])
    j = int(np.where(nw['r']['n']    == 5000)[0][0])
    t_stat, p_val = welch_from_ci(
        median_a=nw['rust']['time_ms'][i],
        ci_lo_a=nw['rust']['time_ms_lo'][i],
        ci_hi_a=nw['rust']['time_ms_hi'][i],
        n_a=100,
        median_b=nw['r']['time_ms'][j],
        ci_lo_b=nw['r']['time_ms_lo'][j],
        ci_hi_b=nw['r']['time_ms_hi'][j],
        n_b=20,
    )
    print(f"NW n=5000 Welch t-test (Rust vs R): t = {t_stat:+.3f}, p = {p_val:.4f}")

    figures = [
        ('3.1_overview.pdf',    lambda p: make_overview(results, p)),
        ('3.2_kmp_ratio.pdf',   lambda p: make_kmp_ratio(results, p)),
        ('3.3_sw.pdf',          lambda p: make_sw(results, p)),
        ('3.4_nw.pdf',          lambda p: make_nw(results, p)),
        ('3.5_tree.pdf',        lambda p: make_tree(results, p)),
        ('3.6_scaling.pdf',     lambda p: make_scaling(scaling_rows, p)),
    ]
    for fname, fn in figures:
        path = out_dir / fname
        fn(path)
        print(f"Wrote {path}")

    tables = [
        ('3.6_speedups.csv',      lambda p: write_speedups_table(speedup_rows, p)),
        ('3.6_scaling_table.csv', lambda p: write_scaling_table(scaling_rows, p)),
        ('3.7_summary_table.csv', lambda p: write_summary_table(results, p)),
    ]
    for fname, fn in tables:
        path = out_dir / fname
        fn(path)
        print(f"Wrote {path}")


if __name__ == '__main__':
    main()
