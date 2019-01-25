#!/usr/bin/env python3

import abc
import random
import re
import sys

from collections import deque
from enum import Enum
from typing import Iterable, Type


class GuessingStrategy(Enum):
    FREQUENCY = 'frequency'
    RANDOM = 'random'
    REGEX = 'regex'


DEFAULT_STRATEGY = GuessingStrategy.REGEX


class HangmanSolver(abc.ABC):

    ALL_LETTERS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    letters_by_frequency = deque('ETAOINSRHDLUCMFYWGPBVKXQJZ')

    def __init__(self, answer_length: int) -> None:
        self.solution = '_' * answer_length
        self.guessed_letters = set()
        self.last_guess = None
        self.solved = False

    @abc.abstractmethod
    def _guess(self) -> str:
        raise NotImplemented

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

    def _guess(self) -> str:
        choices = list(self.ALL_LETTERS - self.guessed_letters)
        if not choices:
            raise RuntimeError('no letters left to guess!')
        return random.choice(choices)


class FrequencyHangmanSolver(HangmanSolver):

    def _guess(self) -> str:
        if not self.letters_by_frequency:
            raise RuntimeError('no letters left to guess!')
        return self.letters_by_frequency.popleft()


class DictionaryHangmanSolver(HangmanSolver):

    def __init__(self, answer_length: int) -> None:
        super().__init__(answer_length)
        with open('words.txt') as f:
            self.words = set(word.upper().strip() for word in f.readlines() if word)

    def _guess(self) -> str:
        raise NotImplemented


class RegexHangmanSolver(DictionaryHangmanSolver):

    def _get_regex(self) -> re.Pattern:
        possible_letters = self.ALL_LETTERS - self.guessed_letters
        wildcard_regex = f'[{"".join(possible_letters)}]'
        word_regex = '^' + ''.join(wildcard_regex if letter == '_' else letter for letter in self.solution) + '$'
        return re.compile(word_regex)

    def _guess(self) -> str:
        regex = self._get_regex()
        self.words = set(word for word in self.words if regex.match(word) is not None)
        if not self.words:
            raise RuntimeError('no words match!')
        if len(self.words) > 1:
            msg = f'Evaluating {len(self.words)} candidates'
            if len(self.words) <= 20:
                msg += f' ({", ".join(sorted(self.words))})'
            print(msg)
        letters_in_candidates = set(''.join(self.words))
        letters_to_guess = list(letters_in_candidates - self.guessed_letters)
        if not letters_to_guess:
            raise RuntimeError('no letters left to guess!')
        return sorted(letters_to_guess, key=lambda c: self.letters_by_frequency.index(c))[0]


def get_solver(strategy: GuessingStrategy) -> Type[HangmanSolver]:
    if strategy == GuessingStrategy.FREQUENCY:
        return FrequencyHangmanSolver
    if strategy == GuessingStrategy.RANDOM:
        return RandomHangmanSolver
    return RegexHangmanSolver


class Game:

    def __init__(self, word: str, strategy: GuessingStrategy = DEFAULT_STRATEGY) -> None:
        self.answer = word.upper()
        self.strategy = strategy
        self.solver = get_solver(strategy)(len(self.answer))

    def play(self) -> None:
        print('The correct answer is:', self.answer)
        print(f"Starting solver with the '{self.strategy.value}' strategy...")
        previous_solution = self.solver.solution
        wrong_guesses = 0
        while not self.solver.solved:
            if self.solver.solution != previous_solution:
                print('Working solution:', ' '.join(self.solver.solution))
                previous_solution = self.solver.solution
            guess = self.solver.guess_letter()
            print('Solver guessed:', guess)
            indices = [i for i in range(len(self.answer)) if self.answer[i] == guess]
            if not indices:
                wrong_guesses += 1
            self.solver.receive_feedback(indices)
        print('DONE!')
        print('Solver says:', self.solver.solution)
        print('Letters guessed:', len(self.solver.guessed_letters))
        print('Wrong guesses:', wrong_guesses)


def main() -> None:
    argc = len(sys.argv)
    if argc > 3:
        print('Usage:', sys.argv[0], '<word> [<strategy>]')
        sys.exit(1)
    if argc == 3:
        strategy = GuessingStrategy[sys.argv[2].upper()]
    else:
        strategy = DEFAULT_STRATEGY
    if argc > 1:
        word = sys.argv[1]
    else:
        word = 'test'
    Game(word, strategy).play()


if __name__ == '__main__':
    main()
