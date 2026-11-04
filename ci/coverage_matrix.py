"""
Матрица покрытия требований: docs/coverage.md из тегов автотестов.

    python ci/coverage_matrix.py           # пересобрать docs/coverage.md
    python ci/coverage_matrix.py --check   # только проверить, что файл актуален (для CI)

Тесты НЕ запускаются: pytest только собирает их (как --collect-only), а генератор
читает у каждого теста теги и маркеры известных багов. Поэтому матрица показывает,
ЧТО проверяет набор тестов, а не результат последнего прогона.

Откуда берутся данные:
  * docs/requirements_index.yml — справочник: пункты SRS, кейсы STD, 20 проверок API;
  * теги Allure на тестах (SRS-T41, TC-0012, API-CHECK-15) — статические
    @allure.tag(...), в том числе в pytest.param(..., marks=allure.tag(...));
  * параметры test_case ("TC-0007") и requirements (["T41"]) параметризованных тестов:
    эти тесты ставят теги через allure.dynamic.tag во время выполнения, при сборе
    таких тегов ещё нет — поэтому генератор читает те же значения из параметров;
  * маркер known_bug (data/known_bugs.py): строгий xfail с причиной "[KEY] ...".

Опечатка в теге (SRS-T50, TC-0099) или тег на непроверяемом пункте — ошибка генерации:
иначе такой тест молча выпал бы из матрицы.
"""

import argparse
import contextlib
import difflib
import io
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "docs" / "requirements_index.yml"
OUTPUT_PATH = ROOT / "docs" / "coverage.md"
TEST_DIRS = ("api_tests", "tests")

sys.path.insert(0, str(ROOT))  # чтобы импортировать реестр багов так же, как его импортируют тесты
from data.known_bugs import KNOWN_BUGS  # noqa: E402

BUG_REASON = re.compile(r"^\[([A-Z0-9_]+)\]")

ICON_COVERED = "✅"
ICON_BUG = "🐞"
ICON_MISSING = "⬜"
ICON_UNTESTABLE = "⚪"
ICON_PARTIAL = "🟡"


class CoverageError(Exception):
    """Данные не согласованы: неизвестный тег, тег на непроверяемом пункте и т.п."""


# ==========================================
# Сбор тестов
# ==========================================
@dataclass
class CollectedTest:
    path: str  # файл теста относительно корня проекта
    function: str  # имя функции без параметров
    param_id: str | None  # id параметризации или None
    tags: set[str] = field(default_factory=set)
    bugs: set[str] = field(default_factory=set)


class _Collector:
    """Плагин pytest: забирает собранные тесты, ничего не запуская."""

    def __init__(self) -> None:
        self.tests: list[CollectedTest] = []

    def pytest_collection_finish(self, session) -> None:
        for item in session.items:
            self.tests.append(_describe(item))


def _describe(item) -> CollectedTest:
    callspec = getattr(item, "callspec", None)
    test = CollectedTest(
        path=Path(item.path).relative_to(ROOT).as_posix(),
        function=getattr(item, "originalname", item.name),
        param_id=callspec.id if callspec else None,
    )

    for mark in item.iter_markers("allure_label"):
        if mark.kwargs.get("label_type") == "tag":
            test.tags.update(str(tag) for tag in mark.args)

    if callspec:
        test_case = callspec.params.get("test_case")
        if isinstance(test_case, str):
            test.tags.add(test_case)
        requirements = callspec.params.get("requirements")
        if isinstance(requirements, (list, tuple)):
            test.tags.update(f"SRS-{r}" for r in requirements)

    for mark in item.iter_markers("xfail"):
        match = BUG_REASON.match(mark.kwargs.get("reason", ""))
        if match:
            test.bugs.add(match.group(1))
    return test


def collect_tests() -> list[CollectedTest]:
    collector = _Collector()
    output = io.StringIO()
    os.chdir(ROOT)  # pytest.ini и conftest.py ищутся от текущей папки
    with contextlib.redirect_stdout(output):
        exit_code = pytest.main(
            [*TEST_DIRS, "--collect-only", "-q", "-p", "no:cacheprovider"],
            plugins=[collector],
        )
    if exit_code != pytest.ExitCode.OK:
        print(output.getvalue(), file=sys.stderr)
        raise CoverageError(f"pytest не смог собрать тесты (код {exit_code}), вывод выше")
    return collector.tests


# ==========================================
# Сопоставление тестов и требований
# ==========================================
@dataclass
class Item:
    """Пункт справочника (требование SRS, кейс STD или проверка API) и тесты на него."""

    tag: str  # как пункт выглядит в теге теста
    label: str  # как пункт показывается в таблице
    title: str
    group: str | None = None
    note: str | None = None
    untestable: str | None = None  # причина, если проверить нельзя
    untestable_word: str = "непроверяемо"  # для проверок API — «неприменимо»
    partial: str | None = None  # что из пункта проверить нельзя
    tests: list[CollectedTest] = field(default_factory=list)

    @property
    def bugs(self) -> list[str]:
        return sorted({bug for test in self.tests for bug in test.bugs})

    @property
    def status(self) -> str:
        if self.untestable:
            return "untestable"
        if not self.tests:
            return "missing"
        return "bug" if self.bugs else "covered"


def load_items() -> tuple[dict, dict[str, list[Item]]]:
    index = yaml.safe_load(INDEX_PATH.read_text(encoding="utf-8"))

    def reason(entry: dict, flag: str) -> str | None:
        if entry.get(flag, True) is False:
            if not entry.get("reason"):
                raise CoverageError(f"{entry['id']}: {flag}: false без reason")
            return entry["reason"]
        return None

    srs = [
        Item(
            tag=f"SRS-{r['id']}",
            label=r["id"],
            title=r["summary"],
            group=r["section"],
            note=r.get("note"),
            untestable=reason(r, "testable"),
        )
        for r in index["srs"]["requirements"]
    ]
    std = [
        Item(tag=c["id"], label=c["id"], title=c["title"], note=c.get("note"), untestable=reason(c, "testable"))
        for c in index["std"]["cases"]
    ]
    api = [
        Item(
            tag=f"API-CHECK-{c['id']}",
            label=str(c["id"]),
            title=c["title"],
            note=c.get("note"),
            untestable=reason(c, "applicable"),
            untestable_word="неприменимо",
            partial=c.get("partial"),
        )
        for c in index["api_checks"]
    ]

    sections = {s["id"] for s in index["srs"]["sections"]}
    unknown_sections = {i.group for i in srs} - sections
    if unknown_sections:
        raise CoverageError(f"Разделы требований не описаны в srs.sections: {sorted(unknown_sections)}")
    return index, {"srs": srs, "std": std, "api": api}


def link_tests(items: dict[str, list[Item]], tests: list[CollectedTest]) -> None:
    by_tag = {item.tag: item for group in items.values() for item in group}
    if len(by_tag) != sum(len(group) for group in items.values()):
        raise CoverageError("В справочнике повторяются идентификаторы")

    problems = []
    for test in tests:
        for bug in sorted(test.bugs):
            if bug not in KNOWN_BUGS:
                problems.append(f"{test.path}::{test.function}: баг {bug} не найден в data/known_bugs.py")
        for tag in sorted(test.tags):
            if not tag.startswith(("SRS-", "TC-", "API-CHECK-")):
                continue  # посторонние теги матрицу не касаются
            item = by_tag.get(tag)
            if item is None:
                problems.append(f"{_full_name(test)}: тег {tag} не найден в {INDEX_PATH.name}")
            elif item.untestable:
                problems.append(f"{_full_name(test)}: тег {tag} стоит на непроверяемом пункте")
            else:
                item.tests.append(test)
    if problems:
        raise CoverageError("Теги тестов не согласуются со справочником:\n  " + "\n  ".join(problems))


def _full_name(test: CollectedTest) -> str:
    suffix = f"[{test.param_id}]" if test.param_id else ""
    return f"{test.path}::{test.function}{suffix}"


# ==========================================
# Markdown
# ==========================================
def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _compress_ids(labels: list[str]) -> str:
    """T1, T2, T3, T7 -> T1–T3, T7 (только для идущих подряд номеров с одним префиксом)."""
    parsed = []
    for label in labels:
        match = re.fullmatch(r"([A-Z]+-?)(\d+)", label)
        parsed.append((match.group(1), int(match.group(2))) if match else (label, None))

    parts, i = [], 0
    while i < len(parsed):
        prefix, number = parsed[i]
        j = i
        while number is not None and j + 1 < len(parsed) and parsed[j + 1] == (prefix, parsed[j][1] + 1):
            j += 1
        # Диапазон — от трёх подряд: "T1, T2" короче и понятнее, чем "T1–T2"
        parts.append(f"{labels[i]}–{labels[j]}" if j - i >= 2 else ", ".join(labels[i : j + 1]))
        i = j + 1
    return ", ".join(parts)


class Renderer:
    def __init__(self, index: dict, items: dict[str, list[Item]], tests: list[CollectedTest]) -> None:
        self.index = index
        self.items = items
        self.tests = tests
        self.params_total: dict[tuple[str, str], int] = {}
        for test in tests:
            key = (test.path, test.function)
            self.params_total[key] = self.params_total.get(key, 0) + 1
        # Имя функции без файла — если оно уникально в проекте (так короче)
        names: dict[str, set[str]] = {}
        for path, function in self.params_total:
            names.setdefault(function, set()).add(path)
        self.ambiguous = {name for name, paths in names.items() if len(paths) > 1}

    # ---------- ячейки ----------
    def tests_cell(self, item: Item) -> str:
        if not item.tests:
            return "—"
        groups: dict[tuple[str, str], list[CollectedTest]] = {}
        for test in item.tests:
            groups.setdefault((test.path, test.function), []).append(test)

        lines = []
        for (path, function), group in groups.items():
            name = f"{Path(path).stem}::{function}" if function in self.ambiguous else function
            line = f"`{name}`"
            if group[0].param_id is not None and len(group) < self.params_total[(path, function)]:
                line += " [" + ", ".join(_cell(t.param_id) for t in group) + "]"
            lines.append(line)
        return "<br>".join(lines)

    @staticmethod
    def status_cell(item: Item) -> str:
        bugs = ", ".join(f"`{b}`" for b in item.bugs)
        if item.status == "untestable":
            return f"{ICON_UNTESTABLE} {item.untestable_word} — {item.untestable}"
        if item.status == "missing":
            return f"{ICON_MISSING} не покрыто"
        if item.partial:
            text = f"{ICON_PARTIAL} частично — {item.partial}"
            return f"{text}; известный баг {bugs}" if bugs else text
        if item.status == "bug":
            return f"{ICON_BUG} покрыто, известный баг {bugs}"
        return f"{ICON_COVERED} покрыто"

    @staticmethod
    def title_cell(item: Item) -> str:
        return _cell(item.title + (f" *({item.note})*" if item.note else ""))

    # ---------- сводка ----------
    @staticmethod
    def counts(items: list[Item]) -> dict[str, int]:
        result = {"total": len(items), "covered": 0, "bug": 0, "missing": 0, "untestable": 0, "partial": 0}
        for item in items:
            result[item.status] += 1
            if item.partial and item.status != "untestable" and item.tests:
                result["partial"] += 1
        result["testable"] = result["total"] - result["untestable"]
        result["with_tests"] = result["covered"] + result["bug"]
        return result

    def summary(self) -> list[str]:
        rows = [
            ("Требования SRS", self.items["srs"]),
            ("Тест-кейсы STD", self.items["std"]),
            ("Проверки API из статьи", self.items["api"]),
        ]
        lines = [
            "## Сводка",
            "",
            "| | Всего | Проверяемых | Покрыто | из них 🐞 с известным багом | ⬜ Не покрыто "
            "| ⚪ Непроверяемо / неприменимо |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for title, items in rows:
            c = self.counts(items)
            percent = round(100 * c["with_tests"] / c["testable"]) if c["testable"] else 0
            lines.append(
                f"| {title} | {c['total']} | {c['testable']} | {c['with_tests']} ({percent}%) "
                f"| {c['bug']} | {c['missing']} | {c['untestable']} |"
            )

        srs_bugs = sorted({bug for item in self.items["srs"] for bug in item.bugs})
        all_bugs = sorted({bug for test in self.tests for bug in test.bugs})
        missing_srs = [i.label for i in self.items["srs"] if i.status == "missing"]
        missing_std = [i.label for i in self.items["std"] if i.status == "missing"]
        missing_api = [i.label for i in self.items["api"] if i.status == "missing"]
        partial_api = [i.label for i in self.items["api"] if i.partial and i.tests]
        lines += [
            "",
            f"Покрыто — на пункт есть хотя бы один автотест (✅ и 🐞). Всего автотестов: {len(self.tests)}.",
            "",
            f"- **Известные баги:** {len(KNOWN_BUGS)} в реестре `data/known_bugs.py`, "
            f"на тестах из матрицы — {len(all_bugs)}; затрагивают пункты SRS — {len(srs_bugs)}: "
            + ", ".join(f"`{b}`" for b in srs_bugs)
            + ".",
            f"- **Не покрыты пункты SRS ({len(missing_srs)}):** {_compress_ids(missing_srs) or 'нет'}.",
            f"- **Не покрыты кейсы STD ({len(missing_std)}):** {_compress_ids(missing_std) or 'нет'}.",
            f"- **Не покрыты проверки API ({len(missing_api)}):** {', '.join(missing_api) or 'нет'}"
            + (f"; частично — {', '.join(partial_api)}." if partial_api else "."),
        ]
        return lines

    # ---------- таблицы ----------
    def table(self, header: str, items: list[Item]) -> list[str]:
        lines = [f"| {header} | Автотесты | Статус |", "|---|---|---|---|"]
        lines += [f"| {i.label} | {self.title_cell(i)} | {self.tests_cell(i)} | {self.status_cell(i)} |" for i in items]
        return lines

    def gaps(self, section: str) -> list[str]:
        return [f"- **{g['ids']}** — {g['note']}" for g in self.index[section].get("numbering_gaps", [])]

    def render(self) -> str:
        lines = [
            "# Матрица покрытия требований",
            "",
            "> **Файл сгенерирован `ci/coverage_matrix.py`, руками не править.**",
            "> Справочник требований — [`requirements_index.yml`](requirements_index.yml),",
            "> покрытие — теги автотестов (`SRS-T41`, `TC-0012`, `API-CHECK-15`) и маркеры `known_bug`.",
            "> Обновить: `python ci/coverage_matrix.py`. CI проверяет актуальность: `--check`.",
            "",
            f"Статусы: {ICON_COVERED} покрыто · {ICON_BUG} покрыто, но тест упирается в известный баг "
            f"(строгий xfail) · {ICON_PARTIAL} покрыто частично · {ICON_MISSING} не покрыто · "
            f"{ICON_UNTESTABLE} непроверяемо или неприменимо (причина в строке).",
            "",
            *self.summary(),
            "",
            "## Требования SRS",
            "",
            *self.gaps("srs"),
        ]
        for section in self.index["srs"]["sections"]:
            items = [i for i in self.items["srs"] if i.group == section["id"]]
            lines += ["", f"### {section['id']} — {section['title']}", "", *self.table("Пункт | Пересказ", items)]

        lines += ["", "## Тест-кейсы STD", "", *self.gaps("std"), ""]
        lines += self.table("Кейс | Название", self.items["std"])
        lines += ["", "## 20 проверок API", "", "По статье «Как тестировать API: 20 проверок» (Хабр, Нетология).", ""]
        lines += self.table("№ | Проверка", self.items["api"])
        return "\n".join(lines) + "\n"


def build() -> str:
    index, items = load_items()
    tests = collect_tests()
    link_tests(items, tests)
    return Renderer(index, items, tests).render()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--check", action="store_true", help="не писать файл, а проверить, что он актуален")
    args = parser.parse_args()
    # Консоль Windows (cp1251) не умеет эмодзи из diff: заменяем такие символы, а не падаем
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")

    try:
        content = build()
    except CoverageError as error:
        print(f"ОШИБКА: {error}", file=sys.stderr)
        return 2

    relative = OUTPUT_PATH.relative_to(ROOT).as_posix()
    if not args.check:
        OUTPUT_PATH.write_text(content, encoding="utf-8", newline="\n")
        print(f"{relative} обновлён")
        return 0

    # Git на Windows может отдать файл с CRLF: сравниваем содержимое, а не переводы строк
    current = OUTPUT_PATH.read_text(encoding="utf-8").replace("\r\n", "\n") if OUTPUT_PATH.exists() else ""
    if current == content:
        print(f"{relative} актуален")
        return 0

    diff = list(
        difflib.unified_diff(
            current.splitlines(),
            content.splitlines(),
            f"{relative} (в репозитории)",
            f"{relative} (по тестам)",
            lineterm="",
        )
    )
    print(
        f"ОШИБКА: {relative} не совпадает с тем, что генерируется из текущих тестов и справочника.\n"
        f"Запусти `python ci/coverage_matrix.py` и закоммить обновлённый {relative}.\n"
        f"Расхождения (первые 40 строк):",
        file=sys.stderr,
    )
    print("\n".join(diff[:40]), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
