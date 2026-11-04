# Матрица покрытия требований

> **Файл сгенерирован `ci/coverage_matrix.py`, руками не править.**
> Справочник требований — [`requirements_index.yml`](requirements_index.yml),
> покрытие — теги автотестов (`SRS-T41`, `TC-0012`, `API-CHECK-15`) и маркеры `known_bug`.
> Обновить: `python ci/coverage_matrix.py`. CI проверяет актуальность: `--check`.

Статусы: ✅ покрыто · 🐞 покрыто, но тест упирается в известный баг (строгий xfail) · 🟡 покрыто частично · ⬜ не покрыто · ⚪ непроверяемо или неприменимо (причина в строке).

## Сводка

| | Всего | Проверяемых | Покрыто | из них 🐞 с известным багом | ⬜ Не покрыто | ⚪ Непроверяемо / неприменимо |
|---|---:|---:|---:|---:|---:|---:|
| Требования SRS | 97 | 95 | 95 (100%) | 21 | 0 | 2 |
| Тест-кейсы STD | 34 | 33 | 33 (100%) | 12 | 0 | 1 |
| Проверки API из статьи | 20 | 19 | 19 (100%) | 8 | 0 | 1 |

Покрыто — на пункт есть хотя бы один автотест (✅ и 🐞). Всего автотестов: 189.

- **Известные баги:** 15 в реестре `data/known_bugs.py`, на тестах из матрицы — 15; затрагивают пункты SRS — 9: `DUPLICATE_CONTACT`, `EMAIL_ERROR_WORDING`, `EMAIL_NON_LATIN_ALLOWED`, `EMAIL_NOT_REQUIRED`, `NO_ERROR_ON_EMPTY_FIELD`, `PASSWORD_NON_LATIN_ALLOWED`, `PASSWORD_NO_MAX_LENGTH`, `PHONE_NOT_REQUIRED`, `USER_EXISTS_WORDING`.
- **Наблюдения без требований:** 6 в реестре `data/observations.py`, с тестами — 6 (в покрытие SRS не входят, см. раздел в конце).
- **Не покрыты пункты SRS (0):** нет.
- **Не покрыты кейсы STD (0):** нет.
- **Не покрыты проверки API (0):** нет; частично — 14.

## Требования SRS

- **T49–T53** — В SRS этих номеров нет — после T48 сразу идёт T54

### Customer — Регистрация пользователя: email и пароль (T1–T15)

| Пункт | Пересказ | Автотесты | Статус |
|---|---|---|---|
| T1 | Email при регистрации обязателен | `test_api_registration_required_fields` [email-absent] | ✅ покрыто |
| T2 | Email при регистрации не может быть пустым | `test_api_registration_required_fields` [email-empty] | ✅ покрыто |
| T3 | В email ровно один символ @ | `test_api_registration_email` [two-at] | ✅ покрыто |
| T4 | До @ есть хотя бы один символ | `test_api_registration_email` [one-char-before-at, nothing-before-at] | ✅ покрыто |
| T5 | После @ есть хотя бы один символ | `test_api_registration_email` [one-char-after-at, nothing-after-at] | ✅ покрыто |
| T6 | Буквы в email — только латиница | `test_api_registration_email` [cyrillic] | 🐞 покрыто, известный баг `EMAIL_NON_LATIN_ALLOWED` |
| T7 | Пароль при регистрации обязателен | `test_api_registration_required_fields` [password-absent] | ✅ покрыто |
| T8 | Пароль не может быть пустым | `test_api_registration_required_fields` [password-empty] | ✅ покрыто |
| T9 | В пароле есть хотя бы один спецсимвол из набора @ $ # ^ & * ! | `test_api_registration_password` [no-special, special-not-from-list] | ✅ покрыто |
| T10 | Буквы в пароле — только латиница | `test_api_registration_password` [cyrillic-letter] | 🐞 покрыто, известный баг `PASSWORD_NON_LATIN_ALLOWED` |
| T11 | В пароле есть хотя бы одна заглавная буква | `test_api_registration_password` [no-uppercase] | ✅ покрыто |
| T12 | В пароле есть хотя бы одна строчная буква | `test_api_registration_password` [no-lowercase] | ✅ покрыто |
| T13 | В пароле есть хотя бы одна цифра | `test_api_registration_password` [no-digit] | ✅ покрыто |
| T14 | Длина пароля — не меньше 8 символов | `test_api_registration_password` [len-7, len-8] | ✅ покрыто |
| T15 | Длина пароля — не больше 15 символов | `test_api_registration_password` [len-15, len-16] | 🐞 покрыто, известный баг `PASSWORD_NO_MAX_LENGTH` |

### New Contact — Создание контакта: правила полей (T16–T48)

| Пункт | Пересказ | Автотесты | Статус |
|---|---|---|---|
| T16 | Имя контакта обязательно | `test_api_contact_payload_variations` [no-name, name-null] | ✅ покрыто |
| T17 | Имя не может быть пустым | `test_api_contact_field_validation` [name-spaces]<br>`test_api_contact_payload_variations` [name-empty] | ✅ покрыто |
| T18 | В имени допускаются цифры | `test_api_contact_field_validation` [name-digits] | ✅ покрыто |
| T19 | В имени допускаются спецсимволы | `test_api_contact_field_validation` [name-special] | ✅ покрыто |
| T20 | Имя — не короче 1 символа | `test_api_contact_field_validation` [name-1-char] | ✅ покрыто |
| T21 | Фамилия обязательна | `test_api_contact_field_validation` [last-name-null] | ✅ покрыто |
| T22 | Фамилия не может быть пустой *(в SRS опечатка: «Contact name» вместо фамилии)* | `test_api_contact_field_validation` [last-name-spaces] | ✅ покрыто |
| T23 | В фамилии допускаются цифры | `test_api_contact_field_validation` [last-name-digits] | ✅ покрыто |
| T24 | В фамилии допускаются спецсимволы | `test_api_contact_field_validation` [last-name-special] | ✅ покрыто |
| T25 | Фамилия — не короче 1 символа | `test_api_contact_field_validation` [last-name-1-char] | ✅ покрыто |
| T26 | Email контакта обязателен *(в SRS опечатка: «Customer email» вместо email контакта)* | `test_api_contact_field_validation` [email-null]<br>`test_add_contact_negative` [TC-0015-empty-email] | 🐞 покрыто, известный баг `EMAIL_NOT_REQUIRED` |
| T27 | Email контакта не может быть пустым | `test_api_contact_payload_variations` [email-empty]<br>`test_add_contact_negative` [TC-0015-empty-email] | 🐞 покрыто, известный баг `EMAIL_NOT_REQUIRED` |
| T28 | В email контакта ровно один символ @ | `test_api_contact_field_validation` [email-two-at]<br>`test_api_contact_payload_variations` [email-invalid] | ✅ покрыто |
| T29 | До @ есть хотя бы один символ | `test_api_contact_field_validation` [email-min-a@b, email-nothing-before-at] | ✅ покрыто |
| T30 | После @ есть хотя бы один символ | `test_api_contact_field_validation` [email-min-a@b, email-nothing-after-at] | ✅ покрыто |
| T31 | Буквы в email контакта — только латиница | `test_api_contact_field_validation` [email-cyrillic] | 🐞 покрыто, известный баг `EMAIL_NON_LATIN_ALLOWED` |
| T32 | Email не совпадает с email ранее созданного контакта | `test_api_add_contact_duplicate` [email] | 🐞 покрыто, известный баг `DUPLICATE_CONTACT` |
| T33 | Адрес обязателен | `test_api_contact_field_validation` [address-null] | ✅ покрыто |
| T34 | Адрес не может быть пустым | `test_api_contact_field_validation` [address-spaces] | ✅ покрыто |
| T35 | В адресе допускаются цифры | `test_api_contact_field_validation` [address-digits] | ✅ покрыто |
| T36 | В адресе допускаются спецсимволы | `test_api_contact_field_validation` [address-special] | ✅ покрыто |
| T37 | Адрес — не короче 1 символа *(в SRS опечатка: «Contact name» вместо адреса)* | `test_api_contact_field_validation` [address-1-char] | ✅ покрыто |
| T38 | Телефон обязателен *(в SRS опечатка: «Phone Number address»)* | `test_api_contact_field_validation` [phone-null]<br>`test_api_contact_payload_variations` [no-phone] | 🐞 покрыто, известный баг `PHONE_NOT_REQUIRED` |
| T39 | Телефон не может быть пустым | `test_api_contact_payload_variations` [phone-spaces] | ✅ покрыто |
| T40 | Телефон состоит только из цифр | `test_api_contact_field_validation` [phone-letters, phone-plus, phone-dash, phone-space] | ✅ покрыто |
| T41 | Телефон — не короче 10 цифр | `test_api_contact_field_validation` [phone-len-9, phone-len-10]<br>`test_api_contact_payload_variations` [phone-short] | ✅ покрыто |
| T42 | Телефон — не длиннее 15 цифр | `test_api_contact_field_validation` [phone-len-15, phone-len-16] | ✅ покрыто |
| T43 | Спецсимволы в телефоне запрещены | `test_api_contact_field_validation` [phone-plus, phone-dash] | ✅ покрыто |
| T44 | Буквы в телефоне запрещены | `test_api_contact_field_validation` [phone-letters] | ✅ покрыто |
| T45 | Телефон не совпадает с телефоном ранее созданного контакта | `test_api_add_contact_duplicate` [phone]<br>`test_add_contact_duplicate_phone`<br>`test_double_click_creates_one_contact` | 🐞 покрыто, известный баг `DUPLICATE_CONTACT` |
| T46 | Описание необязательно | `test_add_contact_success_required_fields_only` | ✅ покрыто |
| T47 | В описании допускаются цифры | `test_api_contact_field_validation` [description-digits] | ✅ покрыто |
| T48 | В описании допускаются спецсимволы и цифры | `test_api_contact_field_validation` [description-special] | ✅ покрыто |

### Update Contact — Редактирование контакта: правила полей (T54–T86)

| Пункт | Пересказ | Автотесты | Статус |
|---|---|---|---|
| T54 | Имя контакта обязательно | `test_api_update_contact_field_validation` [name-null, name-absent] | ✅ покрыто |
| T55 | Имя не может быть пустым | `test_api_update_contact_field_validation` [name-spaces, name-empty]<br>`test_edit_contact_clear_required_fields` [name] | ✅ покрыто |
| T56 | В имени допускаются цифры | `test_api_update_contact_field_validation` [name-digits] | ✅ покрыто |
| T57 | В имени допускаются спецсимволы | `test_api_update_contact_field_validation` [name-special] | ✅ покрыто |
| T58 | Имя — не короче 1 символа | `test_api_update_contact_field_validation` [name-1-char] | ✅ покрыто |
| T59 | Фамилия обязательна | `test_api_update_contact_field_validation` [last-name-null, last-name-absent] | ✅ покрыто |
| T60 | Фамилия не может быть пустой | `test_api_update_contact_field_validation` [last-name-spaces]<br>`test_edit_contact_clear_required_fields` [last_name] | ✅ покрыто |
| T61 | В фамилии допускаются цифры | `test_api_update_contact_field_validation` [last-name-digits] | ✅ покрыто |
| T62 | В фамилии допускаются спецсимволы | `test_api_update_contact_field_validation` [last-name-special] | ✅ покрыто |
| T63 | Фамилия — не короче 1 символа | `test_api_update_contact_field_validation` [last-name-1-char] | ✅ покрыто |
| T64 | Email контакта обязателен *(в SRS опечатка: «Customer email» вместо email контакта)* | `test_api_update_contact_field_validation` [email-null, email-absent] | 🐞 покрыто, известный баг `EMAIL_NOT_REQUIRED` |
| T65 | Email контакта не может быть пустым | `test_api_update_contact_field_validation` [email-empty]<br>`test_edit_contact_clear_required_fields` [email] | 🐞 покрыто, известный баг `EMAIL_NOT_REQUIRED` |
| T66 | В email контакта ровно один символ @ | `test_api_update_contact_field_validation` [email-two-at, email-no-at] | ✅ покрыто |
| T67 | До @ есть хотя бы один символ | `test_api_update_contact_field_validation` [email-min-a@b, email-nothing-before-at] | ✅ покрыто |
| T68 | После @ есть хотя бы один символ | `test_api_update_contact_field_validation` [email-min-a@b, email-nothing-after-at] | ✅ покрыто |
| T69 | Буквы в email контакта — только латиница | `test_api_update_contact_field_validation` [email-cyrillic] | 🐞 покрыто, известный баг `EMAIL_NON_LATIN_ALLOWED` |
| T70 | Email не совпадает с email ранее созданного контакта | `test_edit_contact_duplicate_email` | 🐞 покрыто, известный баг `DUPLICATE_CONTACT` |
| T71 | Адрес обязателен | `test_api_update_contact_field_validation` [address-null, address-absent] | ✅ покрыто |
| T72 | Адрес не может быть пустым | `test_api_update_contact_field_validation` [address-spaces]<br>`test_edit_contact_clear_required_fields` [address]<br>`test_edit_contact_blank_address` | ✅ покрыто |
| T73 | В адресе допускаются цифры | `test_api_update_contact_field_validation` [address-digits] | ✅ покрыто |
| T74 | В адресе допускаются спецсимволы | `test_api_update_contact_field_validation` [address-special] | ✅ покрыто |
| T75 | Адрес — не короче 1 символа | `test_api_update_contact_field_validation` [address-1-char] | ✅ покрыто |
| T76 | Телефон обязателен *(в SRS опечатка: «Phone Number address»)* | `test_api_update_contact_field_validation` [phone-null, phone-absent] | 🐞 покрыто, известный баг `PHONE_NOT_REQUIRED` |
| T77 | Телефон не может быть пустым | `test_api_update_contact_field_validation` [phone-spaces]<br>`test_edit_contact_clear_required_fields` [phone] | ✅ покрыто |
| T78 | Телефон состоит только из цифр | `test_api_update_contact_field_validation` [phone-letters, phone-plus, phone-dash, phone-space] | ✅ покрыто |
| T79 | Телефон — не короче 10 цифр | `test_api_update_contact_field_validation` [phone-len-9, phone-len-10] | ✅ покрыто |
| T80 | Телефон — не длиннее 15 цифр | `test_api_update_contact_field_validation` [phone-len-15, phone-len-16] | ✅ покрыто |
| T81 | Спецсимволы в телефоне запрещены | `test_api_update_contact_field_validation` [phone-plus, phone-dash] | ✅ покрыто |
| T82 | Буквы в телефоне запрещены | `test_api_update_contact_field_validation` [phone-letters] | ✅ покрыто |
| T83 | Телефон не совпадает с телефоном ранее созданного контакта | `test_edit_contact_duplicate_phone` | 🐞 покрыто, известный баг `DUPLICATE_CONTACT` |
| T84 | Описание необязательно | `test_api_update_contact_field_validation` [description-absent] | ✅ покрыто |
| T85 | В описании допускаются цифры | `test_api_update_contact_field_validation` [description-digits] | ✅ покрыто |
| T86 | В описании допускаются спецсимволы | `test_api_update_contact_field_validation` [description-special] | ✅ покрыто |

### Login — Регистрация и вход: сообщения об ошибках (F1–F4)

| Пункт | Пересказ | Автотесты | Статус |
|---|---|---|---|
| F1 | Невалидные данные при регистрации — сообщение «Wrong email or password» | `test_registration_negative` [TC-0002-invalid-email, TC-0003-invalid-password] | ✅ покрыто |
| F2 | Невалидные данные при входе — сообщение «Wrong email or password» | `test_login_negative` [TC-0007-invalid-email, TC-0006-wrong-password] | ✅ покрыто |
| F3 | Регистрация уже существующего пользователя — сообщение «User already exists» | `test_registration_negative` [TC-0004-existing-user, TC-0004-existing-email-new-password] | 🐞 покрыто, известный баг `USER_EXISTS_WORDING` |
| F4 | Вход незарегистрированного пользователя — сообщение «Wrong email or password» | `test_login_negative` [TC-0008-unregistered-user] | ✅ покрыто |

### Add — Добавление контакта: сообщения об ошибках (F5–F9)

| Пункт | Пересказ | Автотесты | Статус |
|---|---|---|---|
| F5 | Пустое имя — сообщение «Name cannot be empty!» | `test_add_contact_negative` [TC-0013-empty-name] | 🐞 покрыто, известный баг `NO_ERROR_ON_EMPTY_FIELD` |
| F6 | Пустая фамилия — сообщение «Last Name cannot be empty!» | `test_add_contact_negative` [TC-0014-empty-last-name] | 🐞 покрыто, известный баг `NO_ERROR_ON_EMPTY_FIELD` |
| F7 | Некорректный email — сообщение «Email not valid: must have format email!» | `test_add_contact_negative` [TC-0015-empty-email, TC-0015-invalid-email] | 🐞 покрыто, известный баг `EMAIL_ERROR_WORDING`, `EMAIL_NOT_REQUIRED` |
| F8 | Некорректный телефон — сообщение о том, что нужны только цифры, длина от 10 до 15 | `test_add_contact_negative` [TC-0016-empty-phone, TC-0016-letters-in-phone, TC-0016-short-phone] | ✅ покрыто |
| F9 | Пустой адрес — сообщение «Address cannot be empty!» | `test_add_contact_negative` [TC-0017-empty-address] | 🐞 покрыто, известный баг `NO_ERROR_ON_EMPTY_FIELD` |

### Update — Редактирование контакта: невалидные данные не сохраняются (F10–F14)

| Пункт | Пересказ | Автотесты | Статус |
|---|---|---|---|
| F10 | Очищенное имя при редактировании не сохраняется | `test_edit_contact_clear_required_fields` [name] | ✅ покрыто |
| F11 | Очищенная фамилия при редактировании не сохраняется | `test_edit_contact_clear_required_fields` [last_name] | ✅ покрыто |
| F12 | Некорректный email при редактировании не сохраняется | `test_edit_contact_clear_required_fields` [email] | 🐞 покрыто, известный баг `EMAIL_NOT_REQUIRED` |
| F13 | Некорректный телефон при редактировании не сохраняется | `test_edit_contact_clear_required_fields` [phone] | ✅ покрыто |
| F14 | Очищенный адрес при редактировании не сохраняется | `test_edit_contact_clear_required_fields` [address]<br>`test_edit_contact_blank_address` | ✅ покрыто |

### Manager — Действия менеджера (F15–F16)

| Пункт | Пересказ | Автотесты | Статус |
|---|---|---|---|
| F15 | Менеджер удаляет контакт по несуществующему id — сообщение «Contact does not exist!» | — | ⚪ непроверяемо — Роль Manager — учётной записи менеджера у проекта нет |
| F16 | Менеджер удаляет все контакты с неверным токеном — сообщение «Wrong authorization token!» | — | ⚪ непроверяемо — Роль Manager — учётной записи менеджера у проекта нет |

## Тест-кейсы STD

- **TC-0010** — В STD этого номера нет — после TC-0009 сразу идёт TC-0011
- **TC-0020** — В STD этого номера нет — после TC-0019 сразу идёт TC-0021

| Кейс | Название | Автотесты | Статус |
|---|---|---|---|
| TC-0001 | Незарегистрированный пользователь регистрируется с валидными данными | `test_registration_success` | ✅ покрыто |
| TC-0002 | Регистрация с невалидным email и валидным паролем отклоняется | `test_registration_negative` [TC-0002-invalid-email] | ✅ покрыто |
| TC-0003 | Регистрация с валидным email и невалидным паролем отклоняется | `test_registration_negative` [TC-0003-invalid-password] | ✅ покрыто |
| TC-0004 | Повторная регистрация с уже зарегистрированными данными отклоняется | `test_registration_negative` [TC-0004-existing-user, TC-0004-existing-email-new-password] | 🐞 покрыто, известный баг `USER_EXISTS_WORDING` |
| TC-0005 | Зарегистрированный пользователь входит с валидными данными | `test_login_success` | ✅ покрыто |
| TC-0006 | Вход с верным email и неверным паролем отклоняется | `test_login_negative` [TC-0006-wrong-password] | ✅ покрыто |
| TC-0007 | Вход с невалидным email и верным паролем отклоняется | `test_login_negative` [TC-0007-invalid-email] | ✅ покрыто |
| TC-0008 | Незарегистрированный пользователь не может войти | `test_login_negative` [TC-0008-unregistered-user] | ✅ покрыто |
| TC-0009 | Авторизованный пользователь выходит из системы | `test_logout_success` | ✅ покрыто |
| TC-0011 | Добавление контакта со всеми полями *(в STD название обрезано)* | `test_add_contact_success_all_fields` | ✅ покрыто |
| TC-0012 | Добавление контакта только с обязательными полями | `test_add_contact_success_required_fields_only` | ✅ покрыто |
| TC-0013 | Контакт с невалидным именем не добавляется | `test_add_contact_negative` [TC-0013-empty-name] | 🐞 покрыто, известный баг `NO_ERROR_ON_EMPTY_FIELD` |
| TC-0014 | Контакт с невалидной фамилией не добавляется | `test_add_contact_negative` [TC-0014-empty-last-name] | 🐞 покрыто, известный баг `NO_ERROR_ON_EMPTY_FIELD` |
| TC-0015 | Контакт с невалидным email не добавляется | `test_add_contact_negative` [TC-0015-empty-email, TC-0015-invalid-email] | 🐞 покрыто, известный баг `EMAIL_ERROR_WORDING`, `EMAIL_NOT_REQUIRED` |
| TC-0016 | Контакт с невалидным телефоном не добавляется | `test_add_contact_negative` [TC-0016-empty-phone, TC-0016-letters-in-phone, TC-0016-short-phone] | ✅ покрыто |
| TC-0017 | Контакт с невалидным адресом не добавляется | `test_add_contact_negative` [TC-0017-empty-address] | 🐞 покрыто, известный баг `NO_ERROR_ON_EMPTY_FIELD` |
| TC-0018 | Контакт с повторяющимся email не добавляется | `test_api_add_contact_duplicate` [email] | 🐞 покрыто, известный баг `DUPLICATE_CONTACT` |
| TC-0019 | Контакт с повторяющимся телефоном не добавляется | `test_api_add_contact_duplicate` [phone]<br>`test_add_contact_duplicate_phone` | 🐞 покрыто, известный баг `DUPLICATE_CONTACT` |
| TC-0021 | Изменение только имени на валидное | `test_edit_contact_single_field` [name] | ✅ покрыто |
| TC-0022 | Изменение только фамилии на валидную | `test_edit_contact_single_field` [last_name] | ✅ покрыто |
| TC-0023 | Изменение только email на валидный | `test_edit_contact_single_field` [email] | ✅ покрыто |
| TC-0024 | Изменение только телефона на валидный | `test_edit_contact_single_field` [phone] | ✅ покрыто |
| TC-0025 | Изменение только адреса на валидный | `test_edit_contact_single_field` [address] | ✅ покрыто |
| TC-0026 | Изменение только описания на валидное | `test_edit_contact_single_field` [description] | 🐞 покрыто, известный баг `EDIT_DESCRIPTION_BROKEN` |
| TC-0027 | Изменение всех полей на валидные | `test_edit_contact_all_fields` | 🐞 покрыто, известный баг `EDIT_DESCRIPTION_BROKEN` |
| TC-0028 | Имя, изменённое на некорректное, не сохраняется | `test_edit_contact_clear_required_fields` [name] | ✅ покрыто |
| TC-0029 | Фамилия, изменённая на некорректную, не сохраняется | `test_edit_contact_clear_required_fields` [last_name] | ✅ покрыто |
| TC-0030 | Email, изменённый на некорректный, не сохраняется | `test_edit_contact_clear_required_fields` [email] | 🐞 покрыто, известный баг `EMAIL_NOT_REQUIRED` |
| TC-0031 | Телефон, изменённый на некорректный, не сохраняется | `test_edit_contact_clear_required_fields` [phone] | ✅ покрыто |
| TC-0032 | Описание, изменённое на некорректное, не сохраняется | — | ⚪ непроверяемо — Противоречит SRS T84–T86: описание необязательно и допускает любые символы — некорректного описания не бывает |
| TC-0033 | Адрес, изменённый на некорректный, не сохраняется | `test_edit_contact_clear_required_fields` [address]<br>`test_edit_contact_blank_address` | ✅ покрыто |
| TC-0034 | Email, совпадающий с email другого контакта, при редактировании не сохраняется | `test_edit_contact_duplicate_email` | 🐞 покрыто, известный баг `DUPLICATE_CONTACT` |
| TC-0035 | Телефон, совпадающий с телефоном другого контакта, при редактировании не сохраняется | `test_edit_contact_duplicate_phone` | 🐞 покрыто, известный баг `DUPLICATE_CONTACT` |
| TC-0036 | Удаление существующего контакта | `test_delete_contact` | ✅ покрыто |

## 20 проверок API

По статье «Как тестировать API: 20 проверок» (Хабр, Нетология).

| № | Проверка | Автотесты | Статус |
|---|---|---|---|
| 1 | Код успешного ответа соответствует контракту | `test_api_add_contact`<br>`test_api_get_all_contacts`<br>`test_api_update_contact`<br>`test_api_delete_contact`<br>`test_api_login_success` | ✅ покрыто |
| 2 | Структура ответа: обязательные поля на месте, лишних нет *(Swagger не запрещает дополнительные свойства, поэтому «лишние» поля контракт не нарушают; обязательные поля и типы проверяет JSON Schema)* | `test_api_add_contact`<br>`test_api_get_all_contacts` | ✅ покрыто |
| 3 | Типы и форматы полей ответа | `test_api_add_contact`<br>`test_api_get_all_contacts` | ✅ покрыто |
| 4 | Значения в ответе соответствуют запросу и данным системы | `test_api_get_all_contacts`<br>`test_api_update_contact` | ✅ покрыто |
| 5 | Бизнес-логика ответа; в ответах нет закрытых данных (пароли, хеши, лишние поля) | `test_api_auth_responses_do_not_expose_password`<br>`test_api_contact_responses_do_not_expose_credentials` | ✅ покрыто |
| 6 | Обязательные поля запроса | `test_api_contact_payload_variations` [no-name, no-phone] | 🐞 покрыто, известный баг `PHONE_NOT_REQUIRED` |
| 7 | Пустые строки, строки из пробелов, null | `test_api_contact_payload_variations` [name-empty, name-null, phone-spaces, email-empty] | 🐞 покрыто, известный баг `EMAIL_NOT_REQUIRED` |
| 8 | Неверный тип или формат входных данных — без молчаливого приведения | `test_api_contact_payload_variations` [name-boolean, phone-short, email-invalid]<br>`test_api_wrong_content_type_is_client_error` | 🐞 покрыто, известный баг `TYPE_COERCION`, `WRONG_CONTENT_TYPE_500` |
| 9 | Граничные значения и классы эквивалентности | `test_api_contact_field_validation`<br>`test_api_update_contact_field_validation`<br>`test_api_registration_password`<br>`test_api_registration_email`<br>`test_api_registration_required_fields` | 🐞 покрыто, известный баг `EMAIL_NON_LATIN_ALLOWED`, `EMAIL_NOT_REQUIRED`, `PASSWORD_NON_LATIN_ALLOWED`, `PASSWORD_NO_MAX_LENGTH`, `PHONE_NOT_REQUIRED` |
| 10 | Неизвестные и серверные поля в запросе: клиент не меняет защищённые свойства *(Неизвестные поля Swagger не запрещает — их игнорирование нормально; подмену серверного поля id проверяет тест mass assignment)* | `test_api_mass_assignment_foreign_id` | ✅ покрыто |
| 11 | Свой корректный код ошибки для каждой причины | `test_api_add_contact_duplicate`<br>`test_api_invalid_tokens`<br>`test_api_login_negative`<br>`test_api_contact_payload_variations`<br>`test_api_delete_missing_contact_returns_404` | 🐞 покрыто, известный баг `DUPLICATE_CONTACT`, `EMAIL_NOT_REQUIRED`, `NOT_FOUND_400`, `NO_AUTH_403`, `PHONE_NOT_REQUIRED`, `TYPE_COERCION` |
| 12 | Тело ошибки: стабильная структура, status в теле равен HTTP-статусу | `test_api_validation_error_body` | ✅ покрыто |
| 13 | Ошибка не раскрывает стек, SQL, пути, секреты | `test_api_add_contact_duplicate`<br>`test_api_invalid_tokens`<br>`test_api_login_negative`<br>`test_api_contact_payload_variations`<br>`test_api_bola_cannot_delete_others_contact`<br>`test_api_bola_cannot_update_others_contact`<br>`test_api_delete_missing_contact_returns_404`<br>`test_api_delete_idempotency`<br>`test_api_unsupported_method_is_rejected`<br>`test_api_wrong_content_type_is_client_error` | 🐞 покрыто, известный баг `DUPLICATE_CONTACT`, `EMAIL_NOT_REQUIRED`, `NOT_FOUND_400`, `NO_AUTH_403`, `PHONE_NOT_REQUIRED`, `TYPE_COERCION`, `WRONG_CONTENT_TYPE_500` |
| 14 | Аутентификация: токена нет, токен испорчен, токен истёк | `test_api_invalid_tokens` | 🟡 частично — Истёкший токен получить нельзя — срок жизни токена нами не управляется; известный баг `NO_AUTH_403` |
| 15 | Доступ к чужому объекту (BOLA): чтение, изменение, удаление | `test_api_bola_cannot_delete_others_contact`<br>`test_api_bola_cannot_update_others_contact`<br>`test_api_bola_cannot_read_others_contact` | ✅ покрыто |
| 16 | Доступ к функции по роли (BFLA) | `test_api_customer_cannot_clear_all_contacts` | 🐞 покрыто, известный баг `CUSTOMER_CAN_CLEAR_ALL` |
| 17 | Состояние объекта после операции | `test_api_update_contact`<br>`test_api_delete_contact` | ✅ покрыто |
| 18 | Побочные эффекты в связанных сущностях | — | ⚪ неприменимо — В нашем API нет связанных сущностей (склада, платежей и т.п.) — только контакты пользователя |
| 19 | Повтор запроса и идемпотентность | `test_api_delete_idempotency` | ✅ покрыто |
| 20 | Согласованность эндпоинтов в цепочке операций | `test_api_contact_lifecycle` | ✅ покрыто |

## Наблюдения без требований

Плохое поведение, о котором в требованиях ничего не сказано: это не нарушение требования,
а обоснованное ожидание (источник — в таблице). Реестр — `data/observations.py`, тег теста — `OBS-<KEY>`.

Статусы: 👁 наблюдается (строгий xfail) · ✅ поведение соответствует ожиданию · ⬜ нет тестов.

| Ключ | Источник ожидания | Автотесты | Статус |
|---|---|---|---|
| `DOUBLE_SUBMIT` | Общие принципы UX: защита формы от повторной отправки | `test_double_click_sends_one_post` | 👁 наблюдается — Кнопка Save не блокируется на время запроса: двойной клик отправляет два POST /v1/contacts |
| `SILENT_FAILURE` | Общие принципы UX: видимость состояния системы, сообщение об ошибке | `test_failure_is_shown_to_user` | 👁 наблюдается — При 500 или обрыве сети на добавление, редактирование и удаление интерфейс ничего не сообщает |
| `EDIT_FORM_CLOSES_ON_FAILURE` | Общие принципы UX: не терять введённые пользователем данные | `test_edit_form_stays_open_on_put_failure` | 👁 наблюдается — При сбое PUT /v1/contacts форма редактирования закрывается, введённые значения пропадают |
| `ENDLESS_LOADING` | Общие принципы UX: у загрузки есть конец — данные, пустое состояние или ошибка | `test_list_failure_does_not_load_forever` | 👁 наблюдается — При 500 на GET /v1/contacts список навсегда остаётся в состоянии 'Loading...' |
| `EXPIRED_SESSION_NO_REDIRECT` | Семантика HTTP 401 (RFC 9110): запрос требует аутентификации | `test_expired_session_redirects_to_login` | 👁 наблюдается — При 401 на GET /v1/contacts интерфейс остаётся на /contacts с 'Loading...' и кнопкой Sign Out |
| `UNHANDLED_NETWORK_ERROR` | Общие практики фронтенда: сетевые ошибки fetch перехватываются | `test_network_error_is_handled` | 👁 наблюдается — При обрыве сети на POST /v1/contacts на странице необработанное исключение 'Failed to fetch' |
