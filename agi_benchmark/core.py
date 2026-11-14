"""Pure scoring rules, separate from input sources and translated messages."""

import argparse
import string
from decimal import Decimal, ROUND_HALF_UP

from .errors import BenchmarkError

BENCHMARK_ID = "agi-achievement-rate"
DESCRIPTION_KEY = "description_agi"
DEFAULT_RULES = {"letters": "agi", "case_sensitive": False, "precision": 0}


def add_arguments(parser, tr):
    parser.add_argument("--letters", help=tr("letters"))
    case = parser.add_mutually_exclusive_group()
    case.add_argument("--case-sensitive", dest="case_sensitive", action="store_true", help=tr("case_sensitive"))
    case.add_argument("--ignore-case", dest="case_sensitive", action="store_false", help=tr("ignore_case"))
    parser.set_defaults(case_sensitive=None)

    def precision(value):
        try:
            number = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(tr("invalid_precision")) from exc
        if not 0 <= number <= 4:
            raise argparse.ArgumentTypeError(tr("invalid_precision"))
        return number

    parser.add_argument("--precision", type=precision, help=tr("precision"))


def overrides(args):
    return {key: getattr(args, key) for key in DEFAULT_RULES if getattr(args, key) is not None}


def validate_rules(values):
    unknown = set(values) - set(DEFAULT_RULES)
    if unknown:
        raise BenchmarkError("unknown_rules", keys=", ".join(sorted(unknown)))
    rules = {**DEFAULT_RULES, **values}
    letters = rules["letters"]
    if not isinstance(letters, str) or not letters or any(c not in string.ascii_letters for c in letters):
        raise BenchmarkError("invalid_letters")
    if type(rules["case_sensitive"]) is not bool:
        raise BenchmarkError("invalid_boolean")
    if not rules["case_sensitive"]:
        letters = letters.lower()
    if len(set(letters)) != len(letters):
        raise BenchmarkError("duplicate_letters")
    if type(rules["precision"]) is not int or not 0 <= rules["precision"] <= 4:
        raise BenchmarkError("invalid_precision")
    rules["letters"] = letters
    return rules


def measure(name, rules):
    letters = rules["letters"]
    matched = [letter for letter in letters if (
        letter in name if rules["case_sensitive"] else letter in name or letter.upper() in name
    )]
    quantum = Decimal(1).scaleb(-rules["precision"])
    percent = (Decimal(len(matched) * 100) / Decimal(len(letters))).quantize(quantum, rounding=ROUND_HALF_UP)
    return {
        "score": int(percent) if rules["precision"] == 0 else float(percent),
        "unit": "percent",
        "details": {
            "matched_letters": matched,
            "missing_letters": [letter for letter in letters if letter not in matched],
            "matched_count": len(matched),
            "total_letters": len(letters),
            "ratio": {"numerator": len(matched), "denominator": len(letters)},
        },
    }


def render_score(result, rules, tr):
    return tr("score_agi", score=f'{result["score"]:.{rules["precision"]}f}')


def score(api_name: str) -> int:
    """Compatibility helper: original default scoring on an unmodified string."""
    return measure(api_name, DEFAULT_RULES)["score"]
