# hangman

This project explores various strategies for solving hangman puzzles programmatically.

So far I have implemented the following strategies:

* **random** (guess letters at random)
* **frequency-based** (guess letters based on their frequency in the English language)
* **regex-based** (guess letters based on frequency, using a dictionary and regex search to filter the candidate words)

By default, the regex strategy will be used.

## Usage

```
$ ./hangman.py [-s <strategy>] <phrase>
```

Examples:

```
$ ./hangman.py pepperoni calzone
```

```
$ ./hangman.py -s random bananas and strawberries
```

```
$ ./hangman.py -s frequency spicy habaneros
```

```
$ ./hangman.py -s regex chocolate cheesecake
```
