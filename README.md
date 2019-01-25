# hangman

This project explores various strategies for solving hangman puzzles programmatically.

So far I have implemented the following strategies:

* **random** (guess letters at random)
* **frequency-based** (guess letters based on their frequency in the English language)
* **regex-based** (guess letters based on frequency, using a dictionary and regex search to filter the candidate words)

## Usage

```
$ ./hangman.py <word> [<strategy>]
```

Examples:

```
$ ./hangman.py pizza
```

```
$ ./hangman.py bananas random
```

```
$ ./hangman.py habaneros frequency
```

```
$ ./hangman.py cheesecake regex
```
