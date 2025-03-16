# Дискорд бот, разработанный для упрощения управления турнирами по Osu!

## Описание
Soon


## Анализ применимости принципов проектирования в проекте

В данном проекте применены три ключевых принципа проектирования: **SOLID**, **KISS** и **DRY**. Их использование позволило создать гибкую, поддерживаемую и расширяемую систему управления турнирами.

---

## SOLID
Принципы SOLID направлены на улучшение структуры кода, обеспечение слабой связанности и высокой модульности. Рассмотрим, как каждый из них реализован в проекте.

### **S** (Single Responsibility Principle, Принцип единственной ответственности)
Каждый класс в проекте выполняет только одну задачу:
- `OsuTournamentManager` отвечает за управление турниром.
- `OsuMatchManager` управляет логикой матчей.
- `OsuAPIClient` предоставляет интерфейс для взаимодействия с osu! API.
- `OsuTournamentSheetsManager` отвечает за работу с Google Таблицами.

#### **Нарушение SRP**:
Без SRP код мог бы выглядеть так:
```python
class TournamentManager:
    def __init__(self):
        self.teams = []
        self.matches = []
    
    def register_team(self, team):
        self.teams.append(team)
    
    def create_match(self, team1, team2):
        match = {"team1": team1, "team2": team2, "status": "pending"}
        self.matches.append(match)
    
    def get_user_info(self, user_id):
        response = requests.get(f"https://osu.ppy.sh/api/v2/users/{user_id}")
        return response.json()
```
Этот класс занимается и командами, и матчами, и API-запросами, что делает его сложным в поддержке.

---

### **O** (Open/Closed Principle, Принцип открытости/закрытости)
Классы проекта открыты для расширения, но закрыты для модификации. Например, `MatchManager` является абстрактным классом, а `OsuMatchManager` расширяет его, не изменяя базовый код.

#### **Нарушение OCP**:
Без OCP пришлось бы менять код базового класса для добавления нового функционала:
```python
class MatchManager:
    def process_match(self, match):
        if match["type"] == "osu":
            # Логика обработки матчей osu!
        elif match["type"] == "dota":
            # Логика обработки матчей Dota 2
```
Правильный вариант - создать отдельные классы `OsuMatchManager` и `DotaMatchManager`, наследуемые от `MatchManager`.

---

### **L** (Liskov Substitution Principle, Принцип подстановки Барбары Лисков)
Любой подкласс может заменять родительский без изменения поведения. В коде `TournamentSheetsManager` и `OsuTournamentSheetsManager` это видно: клиент использует общий интерфейс `TournamentSheetsManager`, не зная деталей реализации.

---

### **I** (Interface Segregation Principle, Принцип разделения интерфейсов)
Разделение интерфейсов предотвращает добавление ненужных методов в классы. Например, `GameAPIClient` содержит только два метода (`get_user_info`, `get_match_info`), а `OsuAPIClient` реализует их конкретную логику.

#### **Нарушение ISP**:
```python
class APIClient:
    def get_user_info(self, user_id):
        pass
    def get_match_info(self, match_id):
        pass
    def upload_match_results(self, match_id, results):
        pass  # Этот метод не нужен в OsuAPIClient
```
Лишний метод `upload_match_results` вынуждает `OsuAPIClient` реализовывать ненужную функциональность.

---

### **D** (Dependency Inversion Principle, Принцип инверсии зависимостей)
В проекте высокоуровневые модули (`TournamentService`) не зависят от низкоуровневых (`OsuTournamentSheetsManager`), а используют абстракции (`TournamentSheetsManager`).

---

## KISS (Keep It Simple, Stupid)
Проект следует принципу KISS, избегая ненужной сложности:
- Используются `dataclass`, что уменьшает объем шаблонного кода.
- Декомпозиция логики управления турнирами на отдельные классы.
- Избегание избыточных условий и циклов.

#### **Нарушение KISS**:
```python
class Team:
    def __init__(self, members):
        if len(members) == 1:
            self.name = members[0].username
            self.avatar = members[0].avatar
        elif len(members) == 2:
            self.name = members[0].username + " & " + members[1].username
            self.avatar = members[0].avatar
        else:
            raise ValueError("Некорректное количество участников")
```
Проще:
```python
@dataclass
class Team:
    members: list
    name: str
    avatar: str
```

---

## DRY (Don't Repeat Yourself)
В проекте активно применяется принцип DRY:
- Функции `_convert_matches_for_updating` и `_convert_teams_for_updating` в `TournamentService` избавляют от дублирования кода обновления таблиц.
- `update_bracket` и `update_matches` используют уже имеющиеся методы, не дублируя логику обновления.

#### **Нарушение DRY**:
```python
if match.status == "Completed":
    update_match_results(match)
if match.status == "In Progress":
    update_match_results(match)
```
Правильный вариант:
```python
if match.status in ["Completed", "In Progress"]:
    update_match_results(match)
```

---

## Заключение
Проект грамотно использует принципы SOLID, KISS и DRY, что делает его гибким, удобным в сопровождении и расширяемым. Примеры нарушений показывают, как мог бы выглядеть код без этих принципов и почему их применение оправдано.

