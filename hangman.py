#!/usr/bin/env python3.7

import abc
import argparse
import random
import re
import sys

from collections import deque
from enum import Enum
from typing import Iterable, List, Type


class GuessingStrategy(Enum):
    FREQUENCY = 'frequency'
    RANDOM = 'random'
    REGEX = 'regex'


DEFAULT_STRATEGY = GuessingStrategy.REGEX


class HangmanSolver(abc.ABC):

    ALL_LETTERS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    letters_by_frequency = deque('ETAOINSRHDLUCMFYWGPBVKXQJZ')

    def __init__(self, answer_word_lengths: Iterable[int]) -> None:
        self.solution = ['_' * word_length for word_length in answer_word_lengths]
        self.guessed_letters = set()
        self.last_guess = None
        self.solved = False

    @abc.abstractmethod
    def _guess(self) -> str:
        raise NotImplemented

    @property
    def solution_str(self) -> str:
        return ' '.join(self.solution)

    def guess_letter(self) -> str:
        if self.last_guess is not None:
            raise RuntimeError('must provide feedback before guessing another letter!')
        choice = self._guess()
        self.last_guess = choice
        self.guessed_letters.add(choice)
        return choice

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

    def __init__(self, answer_word_lengths: Iterable[int]) -> None:
        super().__init__(answer_word_lengths)
        with open('words.txt') as f:
            self.words = set(word.upper().strip() for word in f.readlines())

    def _guess(self) -> str:
        raise NotImplemented


class RegexHangmanSolver(DictionaryHangmanSolver):

    def __init__(self, answer_word_lengths: Iterable[int]) -> None:
        super().__init__(answer_word_lengths)
        self.word_candidates = [self.words.copy() for _ in self.solution]

    def _get_regex(self, word: str) -> re.Pattern:
        possible_letters = self.ALL_LETTERS - self.guessed_letters
        wildcard_regex = f'[{"".join(possible_letters)}]'
        word_regex = '^' + ''.join(wildcard_regex if letter == '_' else letter for letter in word) + '$'
        return re.compile(word_regex)

    def _guess(self) -> str:
        for i, word in enumerate(self.solution):
            word_regex = self._get_regex(word)
            self.word_candidates[i] = set(word for word in self.word_candidates[i] if word_regex.match(word))
            if not self.word_candidates[i]:
                raise RuntimeError(f'no words match! (word #{i + 1})')
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
    def render(cls, solution: Iterable[str], wrong_guesses: Iterable[str]) -> None:
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
        print(' '.join('|'.join(solution)))


class Game:

    max_wrong_guesses = len(HangmanRenderer.updates)

    def __init__(self, phrase: Iterable[str], strategy: GuessingStrategy = DEFAULT_STRATEGY) -> None:
        self.answer = [word.upper() for word in phrase]
        self.strategy = strategy
        self.solver = get_solver(strategy)(map(len, self.answer))
        self.wrong_guesses = set()

    @property
    def answer_str(self) -> str:
        return ' '.join(self.answer)

    def play(self) -> None:
        print('The correct answer is:', self.answer_str)
        print(f"Starting solver with the '{self.strategy.value}' strategy...")
        while not self.solver.solved and len(self.wrong_guesses) < self.max_wrong_guesses:
            guess = self.solver.guess_letter()
            indices = [[i for i, char in enumerate(word) if char == guess] for word in self.answer]
            if not any(indices):
                self.wrong_guesses.add(guess)
            self.solver.receive_feedback(indices)
            HangmanRenderer.render(self.solver.solution, self.wrong_guesses)
            print()
        if self.solver.solved:
            print('Solver says:', self.solver.solution_str)
            print('Wrong guesses:', len(self.wrong_guesses))
        else:
            print('Solver lost!')


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Solve hangman puzzles.')
    parser.add_argument('phrase', nargs='+', help='The word or phrase for the solver to guess')
    parser.add_argument('-s', '--strategy', choices=[s.value for s in GuessingStrategy], default='regex',
                        help='The strategy to use to solve the puzzle')
    return parser.parse_args(args)


def main() -> None:
    parsed_args = parse_args(sys.argv[1:])
    strategy = GuessingStrategy[parsed_args.strategy.upper()]
    phrase = parsed_args.phrase
    Game(phrase, strategy).play()


if __name__ == '__main__':
    main()
