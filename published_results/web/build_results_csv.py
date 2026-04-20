"""Convert the markdown summary tables into a machine-readable CSV."""

from __future__ import annotations

import argparse
import csv
import re
from collections import OrderedDict
from pathlib import Path

DEFAULT_OUTPUT_FILE = Path(__file__).with_name("results-2_1_1_runs.csv")


def default_input_file() -> Path:
    local = Path(__file__).with_name("results-2_1_1.md")
    if local.exists():
        return local

    fallback = Path(__file__).resolve().parent.parent / "CNCSIM" / "results-2_1_1.md"
    if fallback.exists():
        return fallback

    return local

HEADER_WITHOUT_VERSION = [
    "Run",
    "Score",
    "Wall",
    "Input",
    "Output",
    "Cost",
    "Tools",
    "Files",
    "LOC",
    "Links",
    "Last Message",
]
HEADER_WITH_VERSION = [
    "Run",
    "Version",
    "Score",
    "Wall",
    "Input",
    "Output",
    "Cost",
    "Tools",
    "Files",
    "LOC",
    "Links",
    "Last Message",
]


def parse_row(line: str):
    if not line.startswith("|"):
        return None
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(line: str) -> bool:
    s = line.strip()
    return bool(re.match(r"^\|?\s*:?-{3,}:?(\s*\|\s*:?-{3,}:?)+\s*\|?$", s))


def parse_score(value: str):
    m = re.match(r"^(\d+)/(\d+)\s*\(([-0-9.]+)%\)$", value.strip())
    if not m:
        return None, None, None
    return int(m.group(1)), int(m.group(2)), float(m.group(3))


def parse_number(value: str):
    if value is None:
        return None
    s = value.strip().replace("~", "").replace("$", "").replace(",", "")
    if not s or s in {"-", "?"}:
        return None
    m = re.match(r"^(?P<num>[0-9]+(?:\.[0-9]+)?)(?P<unit>[KMG]?)$", s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return None
    value_num = float(m.group("num"))
    mult = {"": 1, "K": 1_000, "M": 1_000_000}.get(m.group("unit").upper(), 1)
    return round(value_num * mult, 6)


def parse_links(cell: str):
    return {label.lower(): url for label, url in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", cell)}


def parse_wall_minutes(value: str):
    m = re.match(r"^(?P<num>[0-9]+(?:\.[0-9]+)?)\s*min$", value.strip())
    if not m:
        return None
    return float(m.group("num"))


def parse_eval(run_label: str, links: dict[str, str]):
    m = re.match(r"^(eval\d+)/", run_label.strip())
    if m:
        return m.group(1)
    for url in links.values():
        m = re.search(r"/((?:eval\d+))/run\d+/", url)
        if m:
            return m.group(1)
    return ""


def build_rows(lines):
    current_language = None
    current_agent = None
    current_model = None
    current_effort = None
    rows = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            current_language = line[3:].strip()
            current_agent = None
            current_model = None
            current_effort = None
        elif line.startswith("### "):
            current_agent = line[3:].strip()
            current_model = None
            current_effort = None
        elif line.startswith("#### "):
            heading = line[5:].strip()
            if " / " in heading:
                current_model, current_effort = [x.strip() for x in heading.rsplit(" / ", 1)]
            else:
                current_model = heading
                current_effort = ""
        elif line.startswith("|") and i + 1 < len(lines) and is_separator(lines[i + 1]):
            headers = parse_row(line)
            if headers == HEADER_WITHOUT_VERSION:
                has_version = False
            elif headers == HEADER_WITH_VERSION:
                has_version = True
            else:
                i += 1
                continue

            score_i = 1 + (1 if has_version else 0)
            wall_i = 2 + (1 if has_version else 0)
            input_i = 3 + (1 if has_version else 0)
            output_i = 4 + (1 if has_version else 0)
            cost_i = 5 + (1 if has_version else 0)
            tools_i = 6 + (1 if has_version else 0)
            files_i = 7 + (1 if has_version else 0)
            loc_i = 8 + (1 if has_version else 0)
            links_i = 9 + (1 if has_version else 0)
            message_i = 10 + (1 if has_version else 0)

            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                if is_separator(lines[j]):
                    j += 1
                    continue
                cells = parse_row(lines[j])
                j += 1
                if not cells or len(cells) <= message_i:
                    continue

                run_label = cells[0].strip()
                score = cells[score_i].strip()
                wall = cells[wall_i].strip()
                input_tokens = cells[input_i].strip()
                output_tokens = cells[output_i].strip()
                cost = cells[cost_i].strip()
                tools = cells[tools_i].strip()
                files = cells[files_i].strip()
                loc = cells[loc_i].strip()
                link_cell = cells[links_i].strip()
                last_message = cells[message_i].strip()

                links = parse_links(link_cell)
                score_count, score_total, score_pct = parse_score(score)
                rows.append(
                    OrderedDict(
                        [
                            ("language", current_language),
                            ("agent", current_agent),
                            ("model", current_model),
                            ("effort", current_effort),
                            ("run_id", run_label),
                            ("eval", parse_eval(run_label, links)),
                            ("score_count", score_count),
                            ("score_total", score_total),
                            ("score_pct", score_pct),
                            ("wall_min", parse_wall_minutes(wall)),
                            ("input_tokens", parse_number(input_tokens)),
                            ("output_tokens", parse_number(output_tokens)),
                            ("cost_usd", parse_number(cost)),
                            ("tools", parse_number(tools)),
                            ("files", parse_number(files)),
                            ("loc", parse_number(loc)),
                            ("result_link", links.get("result", "")),
                            ("transcript_link", links.get("transcript", "")),
                            ("last_message", last_message),
                        ]
                    )
                )
            i = j - 1
        i += 1

    return rows


def parse_args():
    parser = argparse.ArgumentParser(description="Convert official results markdown to CSV.")
    parser.add_argument(
        "--input",
        type=Path,
        default=default_input_file(),
        help="Path to markdown input file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path for generated CSV output",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    lines = args.input.read_text(encoding="utf-8").splitlines()
    rows = build_rows(lines)
    with args.output.open("w", encoding="utf-8", newline="") as out:
        if not rows:
            out.write("")
            print(f"No rows found in {args.input}; wrote empty CSV.")
            return
        writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
