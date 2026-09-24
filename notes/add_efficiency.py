#!/usr/bin/env python3
"""Add bandwidth and FLOP efficiency columns to RAJAPerf kernel run data.

Efficiency is computed relative to the theoretical peaks of the EMR
(Emerald Rapids) single-socket machine:

    bandwidth efficiency (%) = measured bandwidth / peak bandwidth * 100
    flop efficiency (%)      = measured flops     / peak flops     * 100
"""

import argparse
import csv
import os

# EMR single-socket theoretical peaks.
EMR_PEAK_BANDWIDTH_GIB_S = 333.79   # GiB/sec
EMR_PEAK_FLOPS_GFLOP_S = 3891.2     # gigaFLOP/sec = 2*1.9*16*64


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", nargs="?",
                   default="RAJAPerf-kernel-run-data.csv",
                   help="Input CSV file.")
    p.add_argument("-o", "--output",
                   help="Output CSV file (default: <input>-with-efficiency.csv).")
    p.add_argument("--peak-bandwidth", type=float,
                   default=EMR_PEAK_BANDWIDTH_GIB_S,
                   help="Peak bandwidth in GiB/sec (default: %(default)s).")
    p.add_argument("--peak-flops", type=float,
                   default=EMR_PEAK_FLOPS_GFLOP_S,
                   help="Peak flops in gigaFLOP/sec (default: %(default)s).")
    return p.parse_args()


def to_float(value):
    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        return None


def main():
    args = parse_args()

    if args.output:
        output = args.output
    else:
        root, ext = os.path.splitext(args.input)
        output = f"{root}-with-efficiency{ext or '.csv'}"

    with open(args.input, newline="") as f:
        rows = list(csv.reader(f))

    # The first line is a free-text banner; the second line is the header.
    header_idx = None
    for i, row in enumerate(rows):
        if row and row[0].strip() == "Kernel":
            header_idx = i
            break
    if header_idx is None:
        raise SystemExit("Could not find header row starting with 'Kernel'.")

    header = [c.strip() for c in rows[header_idx]]

    def find_col(substring):
        for j, name in enumerate(header):
            if substring.lower() in name.lower():
                return j
        raise SystemExit(f"Could not find column containing '{substring}'.")

    bw_col = find_col("Bandwidth")
    flop_col = find_col("flops")

    out_rows = list(rows)
    out_rows[header_idx] = rows[header_idx] + [
        " Bandwidth efficiency (%) ",
        " Flop efficiency (%) ",
    ]

    for i in range(header_idx + 1, len(out_rows)):
        row = out_rows[i]
        if not row or not row[0].strip():
            continue
        bw = to_float(row[bw_col]) if bw_col < len(row) else None
        flop = to_float(row[flop_col]) if flop_col < len(row) else None
        bw_eff = "" if bw is None else f"{bw / args.peak_bandwidth * 100:.4f}"
        flop_eff = "" if flop is None else f"{flop / args.peak_flops * 100:.4f}"
        out_rows[i] = row + [f" {bw_eff:>22} ", f" {flop_eff:>18} "]

    with open(output, "w", newline="") as f:
        csv.writer(f).writerows(out_rows)

    print(f"Wrote {output}")
    print(f"Peak bandwidth: {args.peak_bandwidth} GiB/sec")
    print(f"Peak flops:     {args.peak_flops} gigaFLOP/sec")


if __name__ == "__main__":
    main()
