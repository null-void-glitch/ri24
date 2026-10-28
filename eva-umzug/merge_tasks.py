#!/usr/bin/env python3
"""Merge tasks from aufgaben_complete.json into the customer list CSV.

- Join key: customer name (Vorname + Name), normalized (trim/lowercase/collapse ws).
- Multiple tasks per customer -> numbered columns Aufgabe_N_*.
- Tasks whose customer is not in the CSV -> separate report.
"""
import csv
import json
import re
import sys
from datetime import datetime

JSON_IN = "aufgaben_complete.json"
REPORT_OUT = "aufgaben_ohne_kunde.csv"

# Customer lists are merged in order; a task matched by any list is consumed.
# Remaining (unmatched) tasks end up in REPORT_OUT.
LISTS = [
    ("Liste_Philipp-komplett.csv", "Liste_Philipp-merged.csv"),
    ("Liste_Patrick-komplett.csv", "Liste_Patrick-merged.csv"),
]

# The customer list is exported from Excel as ISO-8859-1 / cp1252.
CSV_ENC = "cp1252"

TASK_FIELDS = ["Betreff", "Faellig", "Start", "Beschreibung"]

# Synthetic task for customers without any task after merging.
FOLLOWUP_SUBJECT = "Prüfung Anschlussfinanzierung"
FOLLOWUP_YEARS = 7
STATUS_DATE_COL = "Status Datum"


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def clean(s):
    """Tidy a task value for a CSV cell: collapse newlines/whitespace."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", str(s).strip())


def task_values(t):
    return {
        "Betreff": clean(t.get("subject")),
        "Faellig": clean(t.get("due_datetime")),
        "Start": clean(t.get("start_datetime")),
        "Beschreibung": clean(t.get("description")),
    }


def parse_status_date(s):
    """Parse a 'Status Datum' cell (DD.MM.YYYY [HH:MM]); return datetime or None."""
    s = (s or "").strip()
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def add_years(dt, years):
    """Add whole years, clamping Feb 29 -> Feb 28 on non-leap targets."""
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt.replace(month=2, day=28, year=dt.year + years)


def find_status_date(row, primary_idx):
    """Return the status datetime for a row.

    Prefer the 'Status Datum' column; a handful of source rows are shifted one
    column to the right (empty Objektart), so fall back to the first other cell
    that parses as a date.
    """
    if primary_idx < len(row):
        dt = parse_status_date(row[primary_idx])
        if dt is not None:
            return dt
    for cell in row:
        dt = parse_status_date(cell)
        if dt is not None:
            return dt
    return None


def followup_task(dt):
    """Build a synthetic follow-up task due FOLLOWUP_YEARS after status datetime dt."""
    faellig = ""
    if dt is not None:
        faellig = add_years(dt, FOLLOWUP_YEARS).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "Betreff": FOLLOWUP_SUBJECT,
        "Faellig": faellig,
        "Start": "",
        "Beschreibung": "",
    }


def load_tasks():
    """Load tasks from the JSON, grouped by normalized customer name."""
    with open(JSON_IN, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["rows"]

    tasks_by_name = {}
    for t in rows:
        key = norm(t.get("vorname")) + "|" + norm(t.get("name"))
        tasks_by_name.setdefault(key, []).append(t)

    # sort each customer's tasks by due date for stable numbering
    for v in tasks_by_name.values():
        v.sort(key=lambda t: t.get("due_datetime") or "")

    return rows, tasks_by_name


def merge_list(csv_in, csv_out, tasks_by_name, matched_keys):
    """Merge tasks into one customer list, writing csv_out.

    Adds keys it matched to the shared `matched_keys` set so later lists and the
    leftover report know which tasks were consumed.
    """
    # --- read CSV (cp1252 + ';' delimiter) ---
    with open(csv_in, encoding=CSV_ENC, newline="") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        csv_rows = list(reader)

    try:
        i_vorname = header.index("Kunde Vorname")
        i_name = header.index("Kunde Name")
        i_status_date = header.index(STATUS_DATE_COL)
    except ValueError:
        sys.exit(f"{csv_in}: missing 'Kunde Vorname'/'Kunde Name'/'Status Datum' column.")

    name_counts = {}  # normalized name -> how many CSV rows have it (collision detection)
    for r in csv_rows:
        key = norm(r[i_vorname]) + "|" + norm(r[i_name])
        name_counts[key] = name_counts.get(key, 0) + 1

    # max number of tasks any matched customer has -> column count
    max_tasks = 1  # every task-less customer gets one synthetic follow-up task
    for r in csv_rows:
        key = norm(r[i_vorname]) + "|" + norm(r[i_name])
        if key in tasks_by_name:
            max_tasks = max(max_tasks, len(tasks_by_name[key]))

    # --- build new header ---
    new_cols = ["Aufgaben_Anzahl"]
    for n in range(1, max_tasks + 1):
        for fld in TASK_FIELDS:
            new_cols.append(f"Aufgabe_{n}_{fld}")
    out_header = header + new_cols

    # --- merge ---
    matched_customers = 0
    matched_tasks_total = 0
    followup_created = 0
    followup_no_date = 0
    collisions = []
    out_rows = []
    for r in csv_rows:
        key = norm(r[i_vorname]) + "|" + norm(r[i_name])
        tasks = tasks_by_name.get(key, [])
        if tasks:
            matched_keys.add(key)
            matched_customers += 1
            matched_tasks_total += len(tasks)
            if name_counts[key] > 1:
                collisions.append((r[i_vorname], r[i_name], name_counts[key], len(tasks)))
            row_values = [task_values(t) for t in tasks]
        else:
            # No task after merging -> synthesize a follow-up due 7 years after status date.
            tv = followup_task(find_status_date(r, i_status_date))
            followup_created += 1
            if not tv["Faellig"]:
                followup_no_date += 1
            row_values = [tv]

        extra = [str(len(row_values))]
        for n in range(max_tasks):
            tv = row_values[n] if n < len(row_values) else None
            for fld in TASK_FIELDS:
                extra.append(tv[fld] if tv else "")
        out_rows.append(r + extra)

    # --- write merged CSV (';' delimiter, UTF-8 with BOM) ---
    with open(csv_out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writerow(out_header)
        w.writerows(out_rows)

    # --- summary for this list ---
    print(f"== {csv_in} -> {csv_out} ==")
    print(f"  Customers in CSV ......... {len(csv_rows)}")
    print(f"  Max tasks per customer ... {max_tasks}")
    print(f"  Customers with >=1 task .. {matched_customers}")
    print(f"  Tasks merged ............. {matched_tasks_total}")
    print(f"  Follow-ups created ....... {followup_created}  (subject: '{FOLLOWUP_SUBJECT}', +{FOLLOWUP_YEARS}y)")
    print(f"  of which without date .... {followup_no_date}")
    print(f"  Wrote {len(out_header)} columns")
    if collisions:
        print("  WARNING: name collisions (same name on multiple CSV rows; task attached to each):")
        for v, n, rows_n, tasks_n in collisions:
            print(f"    {v} {n}: {rows_n} CSV rows, {tasks_n} task(s) each")


def write_report(tasks_by_name, matched_keys):
    """Write the tasks not consumed by any customer list."""
    unmatched = []
    for key, tlist in tasks_by_name.items():
        if key not in matched_keys:
            unmatched.extend(tlist)

    with open(REPORT_OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writerow(["Vorname", "Name", "Betreff", "Faellig", "Start",
                    "Beschreibung", "Antragsnummer", "Objektadresse"])
        for t in sorted(unmatched, key=lambda x: (norm(x.get("name")), norm(x.get("vorname")))):
            tv = task_values(t)
            w.writerow([clean(t.get("vorname")), clean(t.get("name")),
                        tv["Betreff"], tv["Faellig"], tv["Start"], tv["Beschreibung"],
                        clean(t.get("antragsnummer")), clean(t.get("objektadresse"))])
    return unmatched


def main():
    rows, tasks_by_name = load_tasks()
    matched_keys = set()

    for csv_in, csv_out in LISTS:
        merge_list(csv_in, csv_out, tasks_by_name, matched_keys)
        print()

    unmatched = write_report(tasks_by_name, matched_keys)

    print("== overall ==")
    print(f"  Tasks in JSON ............ {len(rows)}")
    print(f"  Distinct customers w/task  {len(tasks_by_name)}")
    print(f"  Customers matched ........ {len(matched_keys)}")
    print(f"  Tasks unmatched (report) . {len(unmatched)}")
    print(f"  Wrote: {REPORT_OUT}  ({len(unmatched)} rows)")


if __name__ == "__main__":
    main()
