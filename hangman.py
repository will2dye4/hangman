#!/usr/bin/env python3

import abc
import random
import sys

from collections import deque
from enum import Enum
from typing import Iterable


class GuessingStrategy(Enum):
    FREQUENCY = 'frequency'
    RANDOM = 'random'


class HangmanSolver(abc.ABC):

    def __init__(self, answer_length: int) -> None:
        # with open('words.txt') as f:
        #     self.words = set(word.upper().strip() for word in f.readlines() if word)
        self.solution = '_' * answer_length
        self.guessed_letters = set()
        self.last_guess = None
        self.solved = False

    @abc.abstractmethod
    def _guess(self) -> str:
        pass

    def guess_letter(self) -> str:
        if self.last_guess is not None:
            raise RuntimeError('must provide feedback before guessing another letter!')
        choice = self._guess()
        self.last_guess = choice
        self.guessed_letters.add(choice)
        return choice

    def receive_feedback(self, matching_indices: Iterable[int]) -> None:
        if self.last_guess is None:
            raise RuntimeError('must guess a letter before sending feedback!')
        for index in matching_indices:
            self.solution = self.solution[:index] + self.last_guess + self.solution[index+1:]
        self.last_guess = None
        if '_' not in self.solution:
            self.solved = True


class RandomHangmanSolver(HangmanSolver):

    ALL_LETTERS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    def _guess(self) -> str:
        choices = list(self.ALL_LETTERS - self.guessed_letters)
        if not choices:
            raise RuntimeError('no letters left to guess!')
        return random.choice(choices)


class FrequencyHangmanSolver(HangmanSolver):

    letters_by_frequency = deque('ETAOINSRHDLUCMFYWGPBVKXQJZ')

    def _guess(self) -> str:
        if not self.letters_by_frequency:
            raise RuntimeError('no letters left to guess!')
        return self.letters_by_frequency.popleft()


def get_solver(strategy: GuessingStrategy, answer_length: int) -> HangmanSolver:
    if strategy == GuessingStrategy.FREQUENCY:
        return FrequencyHangmanSolver(answer_length)
    return RandomHangmanSolver(answer_length)


class Game:

    def __init__(self, word: str, strategy: GuessingStrategy = GuessingStrategy.FREQUENCY) -> None:
        self.answer = word.upper()
        self.solver = get_solver(strategy, len(self.answer))

    def play(self) -> None:
        print('The correct answer is:', self.answer)
        print('Starting solver...')
        previous_solution = self.solver.solution
        while not self.solver.solved:
            if self.solver.solution != previous_solution:
                print('Working solution:', ' '.join(self.solver.solution))
                previous_solution = self.solver.solution
            guess = self.solver.guess_letter()
            print('Solver guessed:', guess)
            indices = [i for i in range(len(self.answer)) if self.answer[i] == guess]
            self.solver.receive_feedback(indices)
        print('DONE!')
        print('Solver says:', self.solver.solution)
        print('Letters guessed:', len(self.solver.guessed_letters))


def main() -> None:
    argc = len(sys.argv)
    if argc > 3:
        print('Usage:', sys.argv[0], '<word> [<strategy>]')
        sys.exit(1)
    if argc == 3:
        strategy = GuessingStrategy[sys.argv[2].upper()]
    else:
        strategy = GuessingStrategy.FREQUENCY
    if argc > 1:
        word = sys.argv[1].upper()
    else:
        word = 'TEST'
    Game(word, strategy).play()


if __name__ == '__main__':
    main()
