import json
import math
from random import choice, random, randrange

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class Tuner:
    def __init__(
        self,
        ruleset,
        webpages,
        initial_temperature=5000,
        cooling_steps=5000,
        cooling_fraction=0.95,
        steps_per_temp=1000,
    ):
        self.ruleset = ruleset
        self.webpages = webpages
        self.initial_temperature = initial_temperature
        self.cooling_steps = cooling_steps
        self.cooling_fraction = cooling_fraction
        self.steps_per_temp = steps_per_temp
        self.boltzmanns = 1.3806485279e-23

        self.facts = self.ruleset.fact_set.facts.all()

    def anneal(self):
        try:
            self.driver = webdriver.Remote(
                command_executor='http://selenium:4444/wd/hub',
                desired_capabilities=DesiredCapabilities.FIREFOX,
            )

            temperature = self.initial_temperature
            current_solution = self.initial_solution()
            best_solution = current_solution
            current_cost = self.solution_cost(current_solution)
            best_cost = current_cost

            seen_solutions = {}
            for i in range(self.cooling_steps):
                start_cost = current_cost
                for j in range(self.steps_per_temp):
                    new_solution = self.random_transition(current_solution)
                    new_solution_key = tuple(new_solution)
                    if new_solution_key in seen_solutions:
                        new_cost = seen_solutions[new_solution_key]
                    else:
                        new_cost = self.solution_cost(new_solution)
                        seen_solutions[new_solution_key] = new_cost

                    if new_cost < current_cost:
                        # Always take improvements
                        current_cost = new_cost
                        current_solution = new_solution
                        if new_cost < best_cost:
                            best_cost = new_cost
                            best_solution = new_solution
                    else:
                        # Sometimes take non-improvements
                        minus_delta = current_cost - new_cost
                        merit = math.exp(minus_delta / (self.boltzmanns * temperature))
                        if merit > random():
                            current_cost = new_cost
                            current_solution = new_solution

                    # Exit if we're not moving
                    if start_cost == current_cost:
                        break
                temperature *= self.cooling_fraction
            return (best_solution, best_cost)
        finally:
            self.driver.close()

    def initial_solution(self):
        self.driver.get('about:blank')
        self.driver.execute_script(self.ruleset.code)
        initial_solution = self.driver.execute_script(
            'return window.ruleset.initialCoefficients();',
        )
        return initial_solution

    def solution_cost(self, solution):
        results = list(map(lambda webpage: self.test_solution(solution, webpage), self.webpages))
        success_count = sum(results)  # Booleans are integers, who knew?
        return (len(results) - success_count) / len(results)

    def test_solution(self, solution, webpage):
        # String representation of lists happens to be the same for JS and Python
        fact_names = list(map(lambda fact: fact.key, self.facts))

        webpage_facts = webpage.webpagefact_set.filter(fact__in=self.facts)

        self.driver.get(f'http://webserver:8000{webpage.get_absolute_url()}')
        self.driver.execute_script(self.ruleset.code)
        result = self.driver.execute_script(
            f'return window.ruleset.extractFacts(window.document, {fact_names}, {solution})'
        )

        for webpage_fact in webpage_facts:
            if result[webpage_fact.fact.key] != json.loads(webpage_fact.fact_answer):
                return False

        return True

    def random_transition(self, solution):
        randomized_solution = solution.copy()
        index = randrange(0, len(randomized_solution))
        randomized_solution[index] = randomized_solution[index] + choice((1, -1))
        return randomized_solution
