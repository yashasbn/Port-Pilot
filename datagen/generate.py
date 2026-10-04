#!/usr/bin/env python3
"""Generate deterministic synthetic PortPilot CSV data from planted_truths.md."""

from __future__ import annotations

import argparse
import atexit
import csv
import math
import random
import re
from contextlib import ExitStack
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

TRUTHS_PATH = Path(__file__).with_name("planted_truths.md")


def read_field(lines: list[str], label: str) -> str:
    pattern = re.compile(rf"^\|\s*{re.escape(label)}\s*\|\s*(.*?)\s*\|\s*$")
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).replace("`", "").strip()
    raise ValueError(f"Missing table field {label!r} in planted_truths.md")


def get_section(document: str, heading: str) -> list[str]:
    start = document.find(heading)
    if start < 0:
        raise ValueError(f"Missing section {heading!r} in planted_truths.md")
    end = document.find("\n## ", start + len(heading))
    content = document[start:] if end < 0 else document[start:end]
    return content.splitlines()


def extract_dates(value: str) -> list[date]:
    return [date.fromisoformat(part) for part in re.findall(r"\d{4}-\d{2}-\d{2}", value)]


def extract_quoted_values(value: str) -> list[str]:
    return re.findall(r"'([^']+)'", value)


def load_config() -> dict[str, object]:
    document = TRUTHS_PATH.read_text(encoding="utf-8")
    global_section = document[: document.find("\n## Truth #1")]
    start = extract_dates(read_field(global_section.splitlines(), "Dataset start"))[0]
    end = extract_dates(read_field(global_section.splitlines(), "Dataset end"))[0]
    demo_as_of = extract_dates(read_field(global_section.splitlines(), "`DEMO_AS_OF`"))[0]

    truth1 = get_section(document, "## Truth #1:")
    truth2 = get_section(document, "## Truth #2:")
    truth3 = get_section(document, "## Truth #3:")
    truth4 = get_section(document, "## Truth #4:")
    truth5 = get_section(document, "## Truth #5:")
    truth6 = get_section(document, "## Truth #6:")
    controls = get_section(document, "## Deliberate non-signals")

    congestion_window = extract_dates(read_field(truth1, "Window"))
    congestion_multipliers = re.findall(
        r"([0-9]+(?:\.[0-9]+)?)", read_field(truth1, "Effect")
    )
    reefer_scope = read_field(truth2, "Scope")
    reefer_iso = re.search(r"iso_type\s*=\s*'([^']+)'", reefer_scope)
    reefer_operator = re.search(r"operated by\s+`?([A-Z][A-Z0-9_]+)`?", reefer_scope)
    monsoon_window = extract_dates(read_field(truth3, "Window"))
    monsoon_lanes = extract_quoted_values(read_field(truth3, "Scope"))
    customer_scope = read_field(truth4, "Scope")
    customer_name = re.search(r"customer\s+`?([A-Z][A-Z0-9_]+)`?", customer_scope)
    customer_window = extract_dates(read_field(truth4, "Window"))
    if len(customer_window) == 1 and "dataset end" in read_field(truth4, "Window"):
        customer_window.append(end)
    missing_event_scope = read_field(truth5, "Scope")
    event_scope_values = extract_quoted_values(missing_event_scope)
    missing_event_window = re.findall(
        r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})", read_field(truth5, "Window")
    )
    lax_control = re.search(
        r"ISO week\s+(\d+)\s+\((\d{4}-\d{2}-\d{2})\s+through\s+(\d{4}-\d{2}-\d{2})\).*?(-\d+) percentage-point",
        read_field(controls, "One-week LAX blip"),
    )
    high_volume_control = re.search(
        r"([A-Z][A-Z0-9_]+) receives (\d+)% of bookings",
        read_field(controls, "High-volume customer with normal performance"),
    )
    equipment_scope = read_field(truth6, "Scope")
    equipment_lane = re.search(r"trade_lane\s*=\s*'([^']+)'", equipment_scope)
    affected_vessels = re.search(r"VESSEL_001 through VESSEL_(\d+)", equipment_scope)
    equipment_window = extract_dates(read_field(truth6, "Window"))
    equipment_penalty = re.search(r"(\d+)-percentage-point", read_field(truth6, "Effect"))
    equipment_delay = re.search(r"with (\d+) hours", read_field(truth6, "Delay event"))

    if len(congestion_window) != 2 or len(congestion_multipliers) < 2:
        raise ValueError("Could not parse Truth #1 window/effect")
    if reefer_iso is None or reefer_operator is None or len(monsoon_window) != 2 or not monsoon_lanes:
        raise ValueError("Could not parse Truth #2 or #3 scope/window")
    if customer_name is None or len(customer_window) != 2 or len(event_scope_values) < 2:
        raise ValueError("Could not parse Truth #4 or #5 scope/window")
    if len(missing_event_window) != 2:
        raise ValueError("Could not parse Truth #5 timestamp window")
    if lax_control is None or high_volume_control is None:
        raise ValueError("Could not parse deterministic control definitions")
    if (equipment_lane is None or affected_vessels is None or len(equipment_window) != 2
            or equipment_penalty is None or equipment_delay is None):
        raise ValueError("Could not parse Truth #6 incident definition")

    return {
        "dataset_start": start,
        "dataset_end": end,
        "demo_as_of": demo_as_of,
        "congestion_start": congestion_window[0],
        "congestion_end": congestion_window[1],
        "congestion_peak_start": congestion_window[0] + timedelta(days=7),
        "congestion_peak_end": congestion_window[0] + timedelta(days=13),
        "congestion_peak_multiplier": float(congestion_multipliers[0]),
        "congestion_other_multiplier": float(congestion_multipliers[1]),
        "reefer_iso_type": reefer_iso.group(1),
        "reefer_operator": reefer_operator.group(1),
        "monsoon_start": monsoon_window[0],
        "monsoon_end": monsoon_window[1],
        "monsoon_lanes": set(monsoon_lanes),
        "customer_name": customer_name.group(1),
        "customer_start": customer_window[0],
        "customer_end": customer_window[1],
        "tos_source": event_scope_values[0],
        "suppressed_event_type": event_scope_values[1],
        "suppression_start": datetime.strptime(
            f"{missing_event_window[0][0]} {missing_event_window[0][1]}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc),
        "suppression_end": datetime.strptime(
            f"{missing_event_window[1][0]} {missing_event_window[1][1]}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc),
        "lax_control_start": date.fromisoformat(lax_control.group(2)),
        "lax_control_end": date.fromisoformat(lax_control.group(3)),
        "lax_control_delta": int(lax_control.group(4)) / 100.0,
        "high_volume_customer": high_volume_control.group(1),
        "high_volume_share": int(high_volume_control.group(2)) / 100.0,
        "equipment_lane": equipment_lane.group(1),
        "equipment_affected_vessel_max": int(affected_vessels.group(1)),
        "equipment_start": equipment_window[0],
        "equipment_end": equipment_window[1],
        "equipment_otd_penalty": int(equipment_penalty.group(1)) / 100.0,
        "equipment_delay_hours": int(equipment_delay.group(1)),
    }


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def open_streaming_writers(output_dir: Path) -> tuple[ExitStack, dict[str, csv.DictWriter]]:
    schemas = {
        "journey": ("fact_container_journey.csv", [
            "seed_id", "container_id", "booking_date", "delivery_date", "customer_id", "trade_lane", "vessel_id", "iso_type",
            "temperature_excursion", "on_time_delivery", "delay_hours", "documentation_late", "dwell_penalty_hours",
            "routed_through_sgsin",
        ]),
        "port_call": ("fact_port_call.csv", [
            "container_id", "port_code", "call_sequence", "arrival_date", "berth_wait_hours", "delay_hours",
        ]),
        "container_event": ("fact_container_event.csv", [
            "event_id", "container_id", "port_code", "source_system", "event_type", "event_at_utc",
        ]),
        "delay_event": ("fact_delay_event.csv", [
            "event_id", "container_id", "cause_code", "delay_hours", "event_date",
        ]),
        "equipment_exception": ("fact_equipment_exception.csv", [
            "event_id", "container_id", "cause_code", "iso_type", "vessel_id", "event_date",
        ]),
        "truth_answer_key": ("truth_answer_key.csv", ["container_id", "actual_dwell_hours"]),
        "metadata": ("dataset_metadata.csv", ["metadata_key", "metadata_value"]),
    }
    stack = ExitStack()
    writers = {}
    for key, (filename, columns) in schemas.items():
        handle = stack.enter_context((output_dir / filename).open("w", encoding="utf-8", newline=""))
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writers[key] = writer
    atexit.register(stack.close)
    return stack, writers


def iso_week_start(day: date) -> date:
    return day - timedelta(days=day.isoweekday() - 1)


def in_window(day: date, start: date, end: date) -> bool:
    return start <= day <= end


def seasonal_intensity(day: date, start: date, end: date) -> float:
    if not in_window(day, start, end):
        return 0.0
    elapsed = (day - start).days
    duration = max(1, (end - start).days)
    return math.sin(math.pi * elapsed / duration)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).with_name("output"))
    parser.add_argument("--seed", type=int, default=20260926)
    parser.add_argument("--containers-per-day", type=int, default=80)
    args = parser.parse_args()
    if args.containers_per_day < 1:
        parser.error("--containers-per-day must be positive")

    config = load_config()
    rng = random.Random(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_stack, output_writers = open_streaming_writers(args.output_dir)

    vessel_rows = []
    for index in range(1, 121):
        affected = index <= 8
        vessel_rows.append({
            "vessel_id": f"VESSEL_{index:03d}",
            "operator": config["reefer_operator"] if affected else f"CARRIER_{(index - 1) % 12 + 1:02d}",
            "fleet_group": "AFFECTED_REEFER_FLEET" if affected else "GENERAL_FLEET",
        })

    customer_ids = [f"CUSTOMER_{index:03d}" for index in range(1, 20)]
    planted_customer = "CUSTOMER_001"
    customer_rows = [
        {
            "customer_id": customer,
            "tier": "STANDARD",
            "segment": "GENERAL",
            "contact_email": f"{customer.lower()}@example.invalid",
            "account_manager": f"AM_{(index - 1) % 4 + 1:02d}",
        }
        for index, customer in enumerate(customer_ids, start=1)
    ]
    customer_rows[0].update({
        "customer_id": config["customer_name"],
        "tier": "GOLD",
        "segment": "CHEMICALS",
        "contact_email": "meridian-chemicals@example.invalid",
        "account_manager": "AM_01",
    })
    customer_rows.append({
        "customer_id": config["high_volume_customer"],
        "tier": "STANDARD",
        "segment": "GENERAL",
        "contact_email": "pacific-retail@example.invalid",
        "account_manager": "AM_02",
    })

    advisory_rows: list[dict[str, object]] = []
    container_number = 0
    reefer_eligible = 0
    affected_reefer_exceptions = 0
    delay_event_count = 0
    equipment_exception_count = 0
    container_event_count = 0
    week33_cohort_count = 0
    week33_truth4_count = 0
    week33_driver_contributions = {
        "CONGESTION": 0.0,
        "EQUIPMENT": 0.0,
        "CUSTOMER_DOCUMENTATION": 0.0,
    }

    source_by_port = {
        "SGSIN": "TOS_SINGAPORE",
        "NLRTM": "TOS_ROTTERDAM",
        "USLAX": "TOS_LOS_ANGELES",
        "CNSHA": "TOS_SHANGHAI",
        "INNSA": "TOS_NHAVASHEVA",
        "GBFXT": "TOS_FELIXSTOWE",
        "AUSYD": "TOS_SYDNEY",
        "KRPUS": "TOS_BUSAN",
        "JPYOK": "TOS_YOKOHAMA",
        "NZAKL": "TOS_AUCKLAND",
        "AUMEL": "TOS_MELBOURNE",
    }
    lanes = [
        "ASIA_EUROPE", "TRANS_PACIFIC", "INDIA_EUROPE", "INDIA_APAC", "APAC_DOMESTIC",
        "NORTH_ASIA", "TRANS_TASMAN",
    ]
    # NORTH_ASIA + TRANS_TASMAN = 14/37 (~38%) of the non-INDIA_APAC APAC cohort, none via SGSIN.
    lane_weights = [30, 25, 12, 10, 23, 8, 6]
    lane_ports = {
        "ASIA_EUROPE": ["SGSIN", "NLRTM", "USLAX"],
        "TRANS_PACIFIC": ["CNSHA", "USLAX"],
        "INDIA_EUROPE": ["INNSA", "NLRTM"],
        "INDIA_APAC": ["INNSA", "SGSIN"],
        "APAC_DOMESTIC": ["SGSIN"],
        "NORTH_ASIA": ["CNSHA", "KRPUS", "JPYOK"],
        "TRANS_TASMAN": ["AUSYD", "NZAKL", "AUMEL"],
    }
    weekly_noise: dict[date, float] = {}
    day = config["dataset_start"]
    while day <= config["dataset_end"]:
        week_start = iso_week_start(day)
        iso_week_number = day.isocalendar().week
        weekly_noise.setdefault(
            week_start,
            ((iso_week_number * 73) % 401) / 10000.0 - 0.02,
        )
        congestion = in_window(day, config["congestion_start"], config["congestion_end"])
        if day >= config["congestion_peak_start"] and day <= config["congestion_peak_end"]:
            congestion_multiplier = config["congestion_peak_multiplier"]
        elif congestion:
            congestion_multiplier = config["congestion_other_multiplier"]
        else:
            congestion_multiplier = 1.0
        monsoon_intensity = seasonal_intensity(
            day, config["monsoon_start"], config["monsoon_end"]
        )
        customer_active = in_window(day, config["customer_start"], config["customer_end"])

        for _ in range(args.containers_per_day):
            container_number += 1
            container_id = f"CONT_{container_number:08d}"
            lane = rng.choices(lanes, weights=lane_weights, k=1)[0]
            vessel_index = rng.randint(1, 120)
            vessel_id = f"VESSEL_{vessel_index:03d}"
            affected_vessel = vessel_index <= 8
            iso_type = rng.choices(["22G1", "42G1", "45R1"], weights=[45, 35, 20], k=1)[0]
            customer_draw = rng.random()
            if customer_draw < config["high_volume_share"]:
                customer_id = config["high_volume_customer"]
            elif customer_draw < config["high_volume_share"] + (
                0.20 if lane in {"APAC_DOMESTIC", "NORTH_ASIA", "TRANS_TASMAN"} else 0.08
            ):
                customer_id = planted_customer
            else:
                customer_id = rng.choice(customer_ids[1:])
            customer_late = (
                customer_id == planted_customer and customer_active and rng.random() < 0.34
            )
            ports = lane_ports[lane]
            routed_singapore = "SGSIN" in ports
            berth_wait = max(0.2, rng.lognormvariate(math.log(6.0) - 0.25**2 / 2, 0.25))
            route_delay = 0.0
            if congestion and routed_singapore:
                berth_wait *= congestion_multiplier
                route_delay = max(0.0, berth_wait - 6.0)

            base_probability = 0.87 + weekly_noise[week_start]
            effective_probability = base_probability
            cause_codes: list[tuple[str, float]] = []
            congestion_penalty = 0.0
            equipment_otd_penalty = 0.0
            customer_otd_penalty = 0.0
            if congestion and routed_singapore:
                congestion_penalty = min(0.25, 0.035 * route_delay / 6.0)
                effective_probability -= congestion_penalty
                cause_codes.append(("CONGESTION", route_delay))
            if (
                config["equipment_start"] <= day <= config["equipment_end"]
                and lane == config["equipment_lane"]
                and vessel_index <= config["equipment_affected_vessel_max"]
            ):
                equipment_otd_penalty = config["equipment_otd_penalty"]
                effective_probability -= equipment_otd_penalty
                cause_codes.append(("EQUIPMENT", config["equipment_delay_hours"]))
            if monsoon_intensity and lane in config["monsoon_lanes"]:
                effective_probability -= 0.12 * monsoon_intensity
                cause_codes.append(("WEATHER", 2.4 * monsoon_intensity))
            if (
                config["lax_control_start"] <= day <= config["lax_control_end"]
                and "USLAX" in ports
            ):
                effective_probability += config["lax_control_delta"]
            dwell_penalty = 26.0 if customer_late else 0.0
            if customer_late:
                customer_otd_penalty = 0.233
                effective_probability -= customer_otd_penalty
                cause_codes.append(("CUSTOMER_DOCUMENTATION", dwell_penalty))
            if (
                config["equipment_start"] <= day <= config["equipment_end"]
                and lane in {"APAC_DOMESTIC", config["equipment_lane"], "TRANS_TASMAN"}
            ):
                week33_cohort_count += 1
                if customer_late:
                    week33_truth4_count += 1
                week33_driver_contributions["CONGESTION"] += congestion_penalty
                week33_driver_contributions["EQUIPMENT"] += equipment_otd_penalty
                week33_driver_contributions["CUSTOMER_DOCUMENTATION"] += customer_otd_penalty
            effective_probability = max(0.05, min(0.99, effective_probability))
            on_time = rng.random() < effective_probability

            reefer_exception = False
            if affected_vessel and iso_type == config["reefer_iso_type"]:
                reefer_eligible += 1
                reefer_exception = rng.random() < 0.045
            elif iso_type == config["reefer_iso_type"]:
                reefer_exception = rng.random() < 0.008
            if reefer_exception:
                if affected_vessel and iso_type == config["reefer_iso_type"]:
                    affected_reefer_exceptions += 1
                equipment_exception_count += 1
                output_writers["equipment_exception"].writerow({
                    "event_id": f"EQX_{equipment_exception_count:08d}",
                    "container_id": container_id,
                    "cause_code": "EQUIPMENT",
                    "iso_type": iso_type,
                    "vessel_id": vessel_id,
                    "event_date": day.isoformat(),
                })

            actual_dwell = 30.0 + rng.uniform(-2.0, 2.0)
            output_writers["journey"].writerow({
                "seed_id": args.seed,
                "container_id": container_id,
                "booking_date": day.isoformat(),
                "delivery_date": min(
                    config["dataset_end"],
                    day + timedelta(days=len(ports) + (0 if on_time else 1)),
                ).isoformat(),
                "customer_id": config["customer_name"] if customer_id == planted_customer else customer_id,
                "trade_lane": lane,
                "vessel_id": vessel_id,
                "iso_type": iso_type,
                "temperature_excursion": int(reefer_exception),
                "on_time_delivery": int(on_time),
                "delay_hours": round(sum(value for _, value in cause_codes) + (0.0 if on_time else 8.0), 2),
                "documentation_late": int(customer_late),
                "dwell_penalty_hours": dwell_penalty,
                "routed_through_sgsin": int(routed_singapore),
            })
            output_writers["truth_answer_key"].writerow({
                "container_id": container_id,
                "actual_dwell_hours": round(actual_dwell, 2),
            })

            for call_sequence, port_code in enumerate(ports, start=1):
                call_date = day + timedelta(days=call_sequence - 1)
                if call_date > config["dataset_end"]:
                    continue
                port_wait = berth_wait if port_code == "SGSIN" else max(0.2, rng.lognormvariate(math.log(6) - 0.25**2 / 2, 0.25))
                propagated_delay = 0.0
                if congestion and routed_singapore:
                    hop = call_sequence - (ports.index("SGSIN") + 1)
                    if hop == 1:
                        propagated_delay = route_delay * 0.4
                    elif hop == 2:
                        propagated_delay = route_delay * 0.16
                if monsoon_intensity and lane in config["monsoon_lanes"]:
                    propagated_delay += 2.4 * monsoon_intensity
                output_writers["port_call"].writerow({
                    "container_id": container_id,
                    "port_code": port_code,
                    "call_sequence": call_sequence,
                    "arrival_date": call_date.isoformat(),
                    "berth_wait_hours": round(port_wait, 2),
                    "delay_hours": round(propagated_delay, 2),
                })

            for call_sequence, port_code in enumerate(ports, start=1):
                call_date = day + timedelta(days=call_sequence - 1)
                if call_date > config["dataset_end"]:
                    continue
                source_system = source_by_port[port_code]
                gate_out_offset = actual_dwell
                offsets = {
                    "GATE_IN": 0.0,
                    "DISCHARGE": 8.0,
                    "LOAD": 20.0,
                    "GATE_OUT": gate_out_offset,
                }
                for event_type in ("GATE_IN", "DISCHARGE", "LOAD", "GATE_OUT"):
                    event_time = datetime.combine(call_date, datetime.min.time(), tzinfo=timezone.utc)
                    event_time += timedelta(hours=offsets[event_type])
                    if event_time.date() > config["demo_as_of"]:
                        continue
                    if (
                        source_system == config["tos_source"]
                        and event_type == config["suppressed_event_type"]
                        and config["suppression_start"] <= event_time <= config["suppression_end"]
                    ):
                        continue
                    container_event_count += 1
                    output_writers["container_event"].writerow({
                        "event_id": f"EVT_{container_event_count:09d}",
                        "container_id": container_id,
                        "port_code": port_code,
                        "source_system": source_system,
                        "event_type": event_type,
                        "event_at_utc": event_time.isoformat(),
                    })

            for cause_code, delay_hours in cause_codes:
                delay_event_count += 1
                output_writers["delay_event"].writerow({
                    "event_id": f"DLY_{delay_event_count:08d}",
                    "container_id": container_id,
                    "cause_code": cause_code,
                    "delay_hours": round(delay_hours, 2),
                    "event_date": day.isoformat(),
                })
        day += timedelta(days=1)

    for index, issue_date in enumerate(("2026-08-04", "2026-08-11", "2026-08-18"), start=1):
        advisory_rows.append({"doc_id": f"ADV_SG_{index:02d}", "publisher": "PSA_SINGAPORE", "issued_at": issue_date, "doc_type": "PORT_ADVISORY", "content": "Singapore berth congestion advisory."})
    for index, issue_date in enumerate(("2026-06-10", "2026-06-24", "2026-07-08", "2026-07-22", "2026-08-05", "2026-08-19"), start=1):
        advisory_rows.append({"doc_id": f"ADV_WX_{index:02d}", "publisher": "WEATHER_DESK", "issued_at": issue_date, "doc_type": "WEATHER_BULLETIN", "content": "Indian Ocean monsoon conditions affecting scheduled voyages."})
    for index in range(1, 3):
        advisory_rows.append({"doc_id": f"NOTE_ENG_{index:02d}", "publisher": "NORDIC_REEFER_LINE_ENGINEERING", "issued_at": f"2026-0{index + 4}-15", "doc_type": "INTERNAL_ENGINEERING_NOTE", "content": "Internal reefer temperature excursion review for 45R1 equipment."})
    for index in range(1, 13):
        issue_date = date(2026, 5, 1) + timedelta(days=(index - 1) * 12)
        advisory_rows.append({"doc_id": f"NOTE_DOC_{index:02d}", "publisher": config["customer_name"], "issued_at": issue_date.isoformat(), "doc_type": "CUSTOMER_EXCEPTION_NOTE", "content": "Customs paperwork missing or submitted after documentation cutoff."})

    output_stack.close()
    atexit.unregister(output_stack.close)
    write_csv(args.output_dir / "dataset_metadata.csv", ["metadata_key", "metadata_value"], [
        {"metadata_key": "DEMO_AS_OF", "metadata_value": config["demo_as_of"].isoformat()},
        {"metadata_key": "GENERATOR_SEED", "metadata_value": str(args.seed)},
    ])
    write_csv(args.output_dir / "dim_vessel.csv", ["vessel_id", "operator", "fleet_group"], vessel_rows)
    write_csv(args.output_dir / "dim_customer.csv", [
        "customer_id", "tier", "segment", "contact_email", "account_manager",
    ], customer_rows)
    write_csv(args.output_dir / "advisory_documents.csv", [
        "doc_id", "publisher", "issued_at", "doc_type", "content",
    ], advisory_rows)

    affected_rate = affected_reefer_exceptions / reefer_eligible if reefer_eligible else 0.0
    print(f"Generated {container_number} journeys in {args.output_dir}")
    print(f"Generated {container_event_count} container events")
    print(f"Demo as-of date from planted_truths.md: {config['demo_as_of']}")
    print(f"Reefer exception rate for affected fleet: {affected_rate:.3%} ({affected_reefer_exceptions}/{reefer_eligible})")
    print("Truth #1 attribution is intentionally not forced; measure from journey and port-call rows on Day 6.")
    if week33_cohort_count:
        contribution_total = sum(week33_driver_contributions.values())
        shares = {
            cause: 100.0 * contribution / contribution_total
            for cause, contribution in week33_driver_contributions.items()
        }
        print("Week-33 driver-share sanity check (expected probability contributions, NOT measured OTD):")
        print("  " + ", ".join(f"{cause} {share:.1f}%" for cause, share in shares.items()))
        print(f"  Truth #4 late-documentation rows in cohort: {week33_truth4_count}")


if __name__ == "__main__":
    main()
