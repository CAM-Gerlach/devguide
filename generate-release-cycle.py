"""
Read in a JSON and generate two CSVs and a Mermaid file
"""
from __future__ import annotations

import csv
import datetime as dt
import json

MERMAID_HEADER = """
gantt
    dateFormat  YYYY-MM-DD
    title       Python release cycle
    axisFormat  %Y
""".lstrip()

MERMAID_SECTION = """
    section Python {version}
    {release_status}               :{mermaid_status}   python{version}, {release_date},{eol}
"""  # noqa: E501

MERMAID_STATUS_MAPPING = {
    "feature": "",
    "bugfix": "active,",
    "security": "done,",
    "end-of-life": "crit,",
}


def csv_date(date_str: str, now_str: str) -> str:
    """Format a date for CSV"""
    if date_str > now_str:
        # Future, add italics
        return f"*{date_str}*"
    return date_str


def mermaid_date(date_str: str) -> str:
    """Format a date for Mermaid"""
    if len(date_str) == len("yyyy-mm"):
        # Mermaid needs a full yyyy-mm-dd, so let's approximate
        date_str = f"{date_str}-01"
    return date_str


class Versions:
    """For converting JSON to CSV and Mermaid"""

    def __init__(self) -> None:
        with open("include/release-cycle.json") as f:
            self.versions = json.load(f)
        self.sorted_versions = sorted(
            self.versions.items(),
            key=lambda k: [int(i) for i in k.split(".")],
            reverse=True,
        )

    def save_csv(self) -> None:
        """Output CSV files"""
        now_str = str(dt.datetime.utcnow())

        versions_bycategory = {"branches": {}, "end-of-life": {}}
        for version, details in self.sorted_versions.items():
            row = {
                "Branch": details["branch"],
                "Schedule": f":pep:`{details['pep']}`",
                "Status": details["status"],
                "First release": csv_date(details["release_date"], now_str),
                "End of life": csv_date(details["eol"], now_str),
                "Release manager": details["release_manager"],
            }
            cat = "end-of-life" if details["status"] == "end-of-life" else "branches"
            versions_bycategory[cat][version] = row

        for cat, versions in versions_bycategory.items():
            with open(f"include/{cat}.csv", "w", encoding="UTF-8", newline="") as file:
                csv_file = csv.DictWriter(
                    file, fieldnames=versions.keys(), lineterminator="\n"
                )
                csv_file.writeheader()
                row = csv_file.writerows(versions.values())

    def save_mermaid(self) -> None:
        """Output Mermaid file"""
        out = [MERMAID_HEADER]

        for version, details in reversed(self.versions.items()):
            v = MERMAID_SECTION.format(
                version=version,
                release_date=details["release_date"],
                eol=mermaid_date(details["eol"]),
                release_status=details["status"],
                mermaid_status=MERMAID_STATUS_MAPPING[details["status"]],
            )
            out.append(v)

        with open(
            "include/release-cycle.mmd", "w", encoding="UTF-8", newline="\n"
        ) as f:
            f.writelines(out)


def main() -> None:
    versions = Versions()
    versions.save_csv()
    versions.save_mermaid()


if __name__ == "__main__":
    main()
