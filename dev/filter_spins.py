import argparse
import json
from pathlib import Path


def is_x86(arch: str) -> bool:
    return arch.lower().startswith("x86")


def is_allowed_entry(entry: dict) -> bool:
    arch = str(entry.get("arch", ""))
    variant = str(entry.get("variant", ""))
    subvariant = str(entry.get("subvariant", ""))

    if not is_x86(arch):
        return False

    variant_upper = variant.upper()
    subvariant_upper = subvariant.upper()

    return (
        variant in {"Workstation", "KDE", "Everything", "Silverblue", "Kinoite"}
        or subvariant in {"Workstation", "KDE", "Everything", "Silverblue", "Kinoite"}
        or "COSMIC" in variant_upper
        or "COSMIC" in subvariant_upper
    )


def filter_spins(data: list[dict]) -> list[dict]:
    return [entry for entry in data if is_allowed_entry(entry)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Filter spin JSON to only include x86 entries for Workstation, "
            "KDE, Everything, Silverblue, Kinoite, and COSMIC/COSMIC-Atomic."
        )
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("src/resources/default_spins.json"),
        help="Path to source JSON file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("src/resources/default_spins.filtered.json"),
        help="Path to write filtered JSON file.",
    )
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8") as input_file:
        data = json.load(input_file)

    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of objects.")

    filtered = filter_spins(data)

    with args.output.open("w", encoding="utf-8") as output_file:
        json.dump(filtered, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")

    print(f"Wrote {len(filtered)} entries to {args.output}")


if __name__ == "__main__":
    main()
