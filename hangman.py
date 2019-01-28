#!/usr/bin/env python3.7

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

    def _get_regex(self, word: str = None) -> re.Pattern:
        possible_letters = self.ALL_LETTERS - self.guessed_letters
        wildcard_regex = f'[{"".join(possible_letters)}]'
        if word is None:
            word = self.solution
        word_regex = '^' + ''.join(wildcard_regex if letter == '_' else letter for letter in word) + '$'
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
        return sorted(letters_to_guess, key=self.letters_by_frequency.index)[0]


class MultiWordRegexHangmanSolver(RegexHangmanSolver):

    def __init__(self, answer_word_lengths: Iterable[int]) -> None:
        super().__init__(0)
        self.solution = ['_' * word_length for word_length in answer_word_lengths]
        self.word_candidates = [self.words.copy() for _ in range(len(self.solution))]

    @property
    def solution_str(self) -> str:
        return ' '.join(self.solution)

    def receive_feedback(self, matching_word_indices: Iterable[Iterable[int]]) -> None:
        if self.last_guess is None:
            raise RuntimeError('must guess a letter before sending feedback!')
        for word_index, matching_indices in enumerate(matching_word_indices):
            for index in matching_indices:
                word = self.solution[word_index]
                self.solution[word_index] = word[:index] + self.last_guess + word[index+1:]
        self.last_guess = None
        if '_' not in self.solution_str:
            self.solved = True

    def _guess(self) -> str:
        for i, word in enumerate(self.solution):
            word_regex = self._get_regex(word)
            self.word_candidates[i] = set(word for word in self.words if word_regex.match(word) is not None)
            if not self.word_candidates[i]:
                raise RuntimeError(f'no words match! (word #{i + 1})')
        if all(len(candidates) == 1 for candidates in self.word_candidates):
            print('solution must be:', ' '.join(list(candidates)[0] for candidates in self.word_candidates))
        letters_in_candidates = set(''.join([''.join(words) for words in self.word_candidates]))
        letters_to_guess = list(letters_in_candidates - self.guessed_letters)
        if not letters_to_guess:
            raise RuntimeError('no letters left to guess!')
        return sorted(letters_to_guess, key=self.letters_by_frequency.index)[0]


def get_solver(strategy: GuessingStrategy) -> Type[HangmanSolver]:
    if strategy == GuessingStrategy.FREQUENCY:
        return FrequencyHangmanSolver
    if strategy == GuessingStrategy.RANDOM:
        return RandomHangmanSolver
    return RegexHangmanSolver


class HangmanRenderer:

    initial_state = [
        '        +----+      ',
        '        |           ',
        '        |           ',
        '        |           ',
        '        |           ',
        '    +---+---+       ',
    ]

    updates = [
        ('O', 1, 13),
        ('|', 2, 13),
        ('/', 2, 12),
        ('\\', 2, 14),
        ('|', 3, 13),
        ('/', 4, 12),
        ('\\', 4, 14),
    ]

    @classmethod
    def render(cls, solution: str, wrong_guesses: Iterable[str]) -> None:
        wrong_guesses = sorted(wrong_guesses)
        state = cls.initial_state.copy()
        for i in range(min(len(wrong_guesses), len(cls.updates))):
            letter, row, column = cls.updates[i]
            row_str = state[row]
            state[row] = row_str[:column] + letter + row_str[column+1:]
        for row in state:
            print(row)
        print('Wrong guesses:', ' '.join(wrong_guesses))
        print()
        print(' '.join(solution))


class Game:

    max_wrong_guesses = len(HangmanRenderer.updates)

    def __init__(self, word: str, strategy: GuessingStrategy = DEFAULT_STRATEGY) -> None:
        self.answer = word.upper()
        self.strategy = strategy
        self.solver = get_solver(strategy)(len(self.answer))
        self.wrong_guesses = set()

    def play(self) -> None:
        print('The correct answer is:', self.answer)
        print(f"Starting solver with the '{self.strategy.value}' strategy...")
        # previous_solution = self.solver.solution
        while not self.solver.solved and len(self.wrong_guesses) < self.max_wrong_guesses:
            # if self.solver.solution != previous_solution:
            #     print('Working solution:', ' '.join(self.solver.solution))
            #     previous_solution = self.solver.solution
            guess = self.solver.guess_letter()
            # print('Solver guessed:', guess)
            indices = [i for i in range(len(self.answer)) if self.answer[i] == guess]
            if not indices:
                self.wrong_guesses.add(guess)
            self.solver.receive_feedback(indices)
            HangmanRenderer.render(self.solver.solution, self.wrong_guesses)
            print()
        if self.solver.solved:
            print('Solver says:', self.solver.solution)
            print('Wrong guesses:', len(self.wrong_guesses))
        else:
            print('Solver lost!')


class MultiWordGame:

    max_wrong_guesses = len(HangmanRenderer.updates)

    def __init__(self, words: Iterable[str]) -> None:
        self.answer = [word.upper() for word in words]
        self.solver = MultiWordRegexHangmanSolver(map(len, self.answer))
        self.wrong_guesses = set()

    @property
    def answer_str(self) -> str:
        return ' '.join(self.answer)

    def play(self) -> None:
        print('The correct answer is:', self.answer_str)
        print(f"Starting multi-word solver...")
        # previous_solution = self.solver.solution
        while not self.solver.solved and len(self.wrong_guesses) < self.max_wrong_guesses:
            # if self.solver.solution != previous_solution:
            #     print('Working solution:', ' '.join(self.solver.solution))
            #     previous_solution = self.solver.solution
            guess = self.solver.guess_letter()
            # print('Solver guessed:', guess)
            indices = [[i for i in range(len(word)) if word[i] == guess] for word in self.answer]
            if not any(indices):
                self.wrong_guesses.add(guess)
            self.solver.receive_feedback(indices)
            HangmanRenderer.render('|'.join(self.solver.solution), self.wrong_guesses)
            print()
        if self.solver.solved:
            print('Solver says:', self.solver.solution_str)
            print('Wrong guesses:', len(self.wrong_guesses))
        else:
            print('Solver lost!')


def main() -> None:
    argc = len(sys.argv)
    # if argc > 3:
    #     print('Usage:', sys.argv[0], '<word> [<strategy>]')
    #     sys.exit(1)
    # if argc == 3:
    #     strategy = GuessingStrategy[sys.argv[2].upper()]
    # else:
    #     strategy = DEFAULT_STRATEGY
    # if argc > 1:
    #     word = sys.argv[1]
    # else:
    #     word = 'test'
    if argc < 2:
        print('Usage:', sys.argv[0], '<word or phrase>')
    MultiWordGame(sys.argv[1:]).play()


if __name__ == '__main__':
    main()
