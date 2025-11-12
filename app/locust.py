import random

from locust import HttpUser, between, task


class ExcursionUser(HttpUser):
    wait_time = between(1, 3)  # Пауза между запросами
    
    @task(3)  # Вес задачи - чаще выполняем
    def get_excursions(self):
        # Получаем список экскурсий
        self.client.get("/excursions")
    
    @task(2)
    def get_excursion_details(self):
        # Получаем детали случайной экскурсии
        excursion_id = random.randint(1, 10)
        self.client.get(f"/excursions/{excursion_id}")
    
    @task(1)  # Реже выполняем
    def search_excursions(self):
        # Поиск экскурсий
        search_terms = ["горные", "морские", "природа", "городские"]
        term = random.choice(search_terms)
        self.client.get(f"/excursions/search/?q={term}")
    
    @task(1)
    def get_excursion_full(self):
        # Полная информация об экскурсии
        excursion_id = random.randint(1, 10)
        self.client.get(f"/excursions/{excursion_id}/full")

    def on_start(self):
        # Выполняется при "входе" пользователя
        self.get_excursions()
