import os

IGNORE_DIRS = [
    '.venv', '.git', '__pycache__', '.pytest_cache',
    'assets', 'screenshots', 'allure-results', 'allure-report', 'logs'
]

IGNORE_FILES = [
    'full_project_for_ai.txt', 'api-docs.json', 'exported_contacts.json'
]

VALID_EXTENSIONS = ('.py', '.yml', '.yaml', '.env', '.md', '.ini', '.json', '.csv', '.txt')
VALID_EXACT_NAMES = ('Dockerfile',)

with open('full_project_for_ai.txt', 'w', encoding='utf-8') as outfile:
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file in IGNORE_FILES:
                continue

            if file.endswith(VALID_EXTENSIONS) or file in VALID_EXACT_NAMES:
                filepath = os.path.join(root, file)

                outfile.write(f"\n\n{'=' * 60}\n")
                outfile.write(f"📄 FILE: {filepath}\n")
                outfile.write(f"{'=' * 60}\n\n")

                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    outfile.write(f"Ошибка чтения файла: {e}\n")

print("✅ Готово! Файл full_project_for_ai.txt создан.")
