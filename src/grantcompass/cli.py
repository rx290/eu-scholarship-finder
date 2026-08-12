import argparse
import sys

from . import config as config_mod
from . import professors, report, score


def cmd_init(_args):
    path, created = config_mod.ensure_local_config()
    if created:
        print(f"Created {path} from config.example.yaml -- fill in your real GPA/field/countries.")
    else:
        print(f"{path} already exists -- leaving as-is.")


def cmd_professors(_args):
    records = professors.run()
    print(f"{len(records)} European PI records -> data/professors_raw.json")


def cmd_score(_args):
    records = score.run()
    print(f"{len(records)} scored records -> data/scored.json")


def cmd_report(args):
    cfg = config_mod.load_config()
    top_n = args.top_n or cfg.get("output", {}).get("top_n", 15)
    path = report.run(top_n=top_n)
    print(f"Report -> {path}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="grantcompass")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="scaffold config.local.yaml").set_defaults(func=cmd_init)
    sub.add_parser("professors", help="run OpenReview/OpenAlex PI discovery").set_defaults(func=cmd_professors)
    sub.add_parser("score", help="score professors_raw.json + programs_raw.json").set_defaults(func=cmd_score)

    report_parser = sub.add_parser("report", help="render output/report.md + full_results.csv")
    report_parser.add_argument("--top-n", type=int, default=None)
    report_parser.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
