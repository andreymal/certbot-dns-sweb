# certbot-dns-sweb

Плагин для Certbot, который реализует проверку DNS-01 и позволяет получить
wildcard-сертификаты Let's Encrypt для доменов, которые обслуживает
SpaceWeb (https://sweb.ru/).

Основан на непубличном API, который используется в веб-панели SpaceWeb,
поэтому всё может сломаться в любой момент, никаких гарантий нет, используйте
на свой страх и риск. Если сломается — пинайте кого-нибудь по этому поводу,
может даже кто-нибудь починит.


## Установка

Если `certbot` установлен глобально в системе, то придётся в ней помусорить.
Используйте `pip`, соответствующий той версии Python, для которой у вас
установлен Certbot (`pip2` или `pip3`):

    pip install git+https://github.com/andreymal/certbot-dns-sweb.git#egg=certbot-dns-sweb

Если вы используете `certbot-auto`, то нужно установить плагин внутри его
виртуального окружения (virtualenv):

    /opt/eff.org/certbot/venv/bin/pip install git+https://github.com/andreymal/certbot-dns-sweb.git#egg=certbot-dns-sweb


## Использование

Первым делом рекомендуется зайти в панель управления SpaceWeb и создать
ограниченный аккаунт, у которого будет доступ только к доменам (Аккаунт →
Профиль → Пользователи). Вам выдадут логин вида `subname@username`.

Создайте текстовый файл где-нибудь (например `/etc/letsencrypt/sweb.ini`)
и запишите туда логин и пароль, а также юзер-агент по вкусу:

    certbot_dns_sweb:dns_sweb_username = subname@username
    certbot_dns_sweb:dns_sweb_password = correcthorsebatterystaple
    certbot_dns_sweb:dns_sweb_user_agent = "Mozilla/5.0 definitely-not-a-robot/999.99"
    certbot_dns_sweb:dns_sweb_drop_old_txt = 1

Опция `drop_old_txt` включает удаление старых записей `_acme-challenge`,
так как они могут мешать проверке.

Не забудьте ограничить доступ на чтение посторонними:

    chmod 600 /etc/letsencrypt/sweb.ini

Запросите сертификат с нужными вам настройками (в примере `certonly`,
не забудьте отредактировать команду на свой вкус):

    certbot certonly -a certbot-dns-sweb:dns-sweb \
      --certbot-dns-sweb:dns-sweb-credentials /etc/letsencrypt/sweb.ini \
      -d "example.ru" -d "*.example.ru"

Плагин создаст TXT-записи `_acme-challenge`, после чего придётся подождать
20 минут (меньшее ожидание работало нестабильно), пока у всех DNS-серверов
почистятся кэши. После этого вы получите wildcard-сертификат, если ничего
не сломалось. Созданные записи будут автоматически удалены после получения
сертификата.

Если вы получите ошибку «Incorrect TXT record», есть следующие варианты:

- возможно, кэши DNS так и не успели почиститься, тогда можно изменить время
  ожидания опцией `--certbot-dns-sweb:dns-sweb-propagation-seconds 1800`
  (указывается в секундах);

- вы не включили опцию `drop_old_txt`, у вас остались какие-то старые
  DNS-записи `_acme-challenge` и они мешаются; удалите их вручную в панели
  управления и попробуйте снова;

- SpaceWeb что-то изменил и плагин в принципе стал неработоспособен; тут уже
  ничего не поделать, кроме как пытаться чинить плагин.
