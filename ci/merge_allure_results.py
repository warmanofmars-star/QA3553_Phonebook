"""
Подготовка результатов Allure из нескольких браузеров к одному общему отчёту.

Используется в GitHub Actions: тесты идут параллельно в матрице (chrome, firefox),
каждый job сохраняет свою папку allure-results-<браузер>. Этот скрипт запускается
перед `allure generate` и делает три вещи:

  1. Уникализирует тесты по браузеру. Один и тот же тест в Chrome и Firefox имеет
     одинаковые historyId и testCaseId — Allure счёл бы их одним тестом с "ретраем"
     и показал бы только один результат. Дописываем браузер к идентификаторам,
     а к имени и сьюту — метку [CHROME] / [FIREFOX], чтобы различать их в отчёте.
  2. Склеивает environment.properties всех браузеров в один:
     Browser=chrome, firefox (Allure берёт только один такой файл).
  3. Пишет executor.json — блок Executors в отчёте со ссылкой на прогон CI.

Запуск:
    python ci/merge_allure_results.py allure-results-chrome allure-results-firefox
"""

import json
import os
import sys
from pathlib import Path


def read_properties(path: Path) -> dict[str, str]:
    """Простой парсер .properties: строки КЛЮЧ=ЗНАЧЕНИЕ."""
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def tag_results_with_browser(folder: Path, browser: str) -> int:
    """Дописывает браузер к идентификаторам и именам тестов. Возвращает число файлов."""
    label = browser.upper()
    files = list(folder.glob("*-result.json"))
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))

        # Идентификаторы, по которым Allure склеивает тесты и строит историю
        for key in ("historyId", "testCaseId"):
            if key in data:
                data[key] = f"{data[key]}-{browser}"

        # Человекочитаемые имена
        for key in ("name", "fullName"):
            if key in data:
                data[key] = f"{data[key]} [{label}]"
        for item in data.get("labels", []):
            if item.get("name") == "suite":
                item["value"] = f"{item['value']} ({label})"

        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return len(files)


def merge_environment(folders: list[Path]) -> dict[str, str]:
    """Объединяет environment.properties: разные значения одного ключа — через запятую."""
    merged: dict[str, list[str]] = {}
    for folder in folders:
        for key, value in read_properties(folder / "environment.properties").items():
            values = merged.setdefault(key, [])
            if value not in values:
                values.append(value)

    environment = {key: ", ".join(values) for key, values in merged.items()}

    # Данные о прогоне CI (переменные GITHUB_* задаёт сам GitHub Actions)
    if os.getenv("GITHUB_ACTIONS"):
        environment["CI"] = "GitHub Actions"
        environment["Branch"] = os.getenv("GITHUB_REF_NAME", "")
        environment["Commit"] = os.getenv("GITHUB_SHA", "")[:7]
        environment["Run"] = os.getenv("GITHUB_RUN_NUMBER", "")
    return environment


def write_executor(folder: Path) -> None:
    """executor.json: блок Executors и ссылки из графика трендов на конкретные прогоны."""
    if not os.getenv("GITHUB_ACTIONS"):
        return
    run_url = f"{os.getenv('GITHUB_SERVER_URL')}/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}"
    executor = {
        "name": "GitHub Actions",
        "type": "github",
        "buildName": f"#{os.getenv('GITHUB_RUN_NUMBER')} ({os.getenv('GITHUB_REF_NAME')})",
        "buildOrder": int(os.getenv("GITHUB_RUN_NUMBER", "0")),
        "buildUrl": run_url,
    }
    (folder / "executor.json").write_text(json.dumps(executor), encoding="utf-8")


def main(args: list[str]) -> int:
    folders = [Path(arg) for arg in args if Path(arg).is_dir()]
    missing = [arg for arg in args if not Path(arg).is_dir()]
    for arg in missing:
        # Например, job одного браузера упал до сохранения результатов
        print(f"⚠ Папка {arg} не найдена — пропускаю")
    if not folders:
        print("❌ Нет ни одной папки с результатами")
        return 1

    for folder in folders:
        browser = folder.name.removeprefix("allure-results-")
        count = tag_results_with_browser(folder, browser)
        print(f"✅ {folder}: помечено результатов: {count} ({browser})")

    # Общий environment и executor кладём в первую папку, из остальных убираем дубли
    environment = merge_environment(folders)
    for folder in folders[1:]:
        (folder / "environment.properties").unlink(missing_ok=True)
    (folders[0] / "environment.properties").write_text(
        "".join(f"{key}={value}\n" for key, value in environment.items()), encoding="utf-8"
    )
    write_executor(folders[0])
    print("✅ Environment:", environment)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
