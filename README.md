# Форматтер для выгрузки из жиры в Digital Nomads

1. Перейти по ссылке `https://jira.mvk.com/rest/api/2/search?jql=assignee was in (<USERNAME>) and updated > <DATE> and project in (<PROJECT>) and timespent > 0&fields=summary,worklog&maxResults=1000`, заменив `<USERNAME>` (например, `m.mustakimov`), `<DATE>` (например, `2023-03-1`), `<PROJECT>` (например, `ME`)
2. Сохранить выгрузку в корень директории в файл `jira_export.json`
3. Запустить main.py

Перед запуском надо установить зависимости из requirements.txt: `pip intall -r requirements.txt` в корне проекта