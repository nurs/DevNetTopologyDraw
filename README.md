# DevNetTopologyDraw

Вариант реализации задания на визуализацию сетевых топологий для Cisco DevNet Марафона.

### Метод решения:

Приложение на языке Python генерирует файл 'devnet.yaml' с описанием топологии для [go.drawthe.net](http://go.drawthe.net/). Тот, в свою очередь, отображает схему на браузере и дает возможность скачать ее в формате 'PNG'. 
Для подключения к оборудованиям используется библиотека - 'netmiko', а для парсинга вывода данных о соседях - 'textfsm'.
Исходный код 'drawthe.net' также включен в приложение, чтобы локально запустить http сервер, и автоматически открывать созданную топологию на браузере.
Данные об оборудованиях должны быть заполнены в файле 'devices.csv'. Помимо стандартных (ip,passwd...) данных необходимо внести данные о роли устройства в сети. Это дает возможность выбрать иконку и правильно расположить устройства на карте.

### Особенности:
  - Если между двумя оборудованиями есть несколько линков, отрисовывается один, но отмечаются все порты.
  - Приложение может найти и отобразить оборудование даже при отсутствии доступа, или при отсутствии в списке устройств, если его видно в списке соседей на других оборудованиях. Иконки таких оборудований выделяются серым цветом. 
  - Нажав на 'HOSTNAME' оборудования можно открыть сессию SSH.
  - [go.drawthe.net](http://go.drawthe.net/) дает возможность изменить вид карты и расположение устройств в онлайн режиме. Минус в том, что нельзя передвигать оборудования с помощью мышки. Вместо этого устанавливаем координаты вручную.

### Пример вывода:

![sample](sample.png)

### Запуск:

```sh
$ pip install netmiko
$ pip install textfsm
```
Заполните таблицу в 'devices.csv' своими данными. Определите какую роль выполняет устройство в сети, и заполните колонку 'device_role' этими данными:

- CORE - ядро сети
- DISTRIBUTION - уровень агрегации
- CORE-DISTRIBUTION - если у вас уровни ядра и агрегации на одном устройстве
- ACCESS - уровень доступа
- SERVER-FARM - серверные коммутаторы
- INTERNET - edge устройство, поключенное к интернету
- WAN - соединение филиалов

device_type
- "cisco_ios"
- "cisco_ios_telnet"
- "cisco_xe"

```sh
$ python -m http.server 8585 --directory DIREKTORIA_PROEKTA
```

Сперва запускаем http сервер на порту '8585' и указываем директорию проекта в машине. 
* Если будете менять порт, то также отредактируйте переменную 'WEB_URL' в файле 'Main.py'.

```sh
$ python Main.py
```

Запускаем Main.py.
После того скрипт соберет все данные, откроется браузер с отображением топологии на странице - [http://localhost:8585/)](http://localhost:8585/).
