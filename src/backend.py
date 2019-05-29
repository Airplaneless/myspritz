import re
import numpy as np
from math import ceil, sqrt


class Reader:
    """
    Implements Reader for text files
    """
    def __init__(self, fpath, settings):
        """
        Reader constructor
        :param fpath: str
            Path to text file
        :param settings: dict
            Reader settings
        """
        with open(fpath, 'r') as f:
            self.lines = f.readlines()
        self.wpm = settings["wpm"]  # Word per minute
        self.wps = 0.25  # Word position percentage
        self.wpf = settings["wpf"]  # Word pef frame
        # Here this pattern finds one word with punctuations, or
        # word with one char.
        # For example, pattern in "I travel the world and the seven seas"
        # "I travel", not "I", "travel", will be matched
        # I personally think it would be better
        self.wordpattern = re.compile("([\w][\s]*[\w]+[\s,.-:?!]*|[\w$])")

    def getWords(self, line):
        """
        :param line: str
            One line
        :return: list(str)
            Return words from line
        """
        words = self.wordpattern.findall(line)
        return words

    def getWordPos(self, word):
        """
        Find position of marked char
        :param word: str
            Word, maybe with one char
        :return: int
            Position of marked char
        """
        if len(word) == 1:
            return 0
        if len(word) < 12:
            res = ceil(len(word) * self.wps)
            if word[res] == ' ':
                res += 1
            return res
        else:
            res = ceil(12 * self.wps)
            if word[res] == ' ':
                res += 1
            return res

    def getWordCount(self, word):
        """
        Find time, for which word is shown
        :param word: str
        :return: float
            time in ms
        """
        res = len(word) * 0.01
        return 60.0/self.wpm + sqrt(res)

    def wordList(self):
        """
        Return chunks of all text, with respect to wpf (Word per frame)
        :return: list(str)
            all chunks
        """
        words = list()
        for line in self.lines:
            ws = self.getWords(line)
            if len(ws) >= self.wpf:
                # Here np.array_split used, which join all words
                # from one line with respect to word per frame
                for chunk in np.array_split(ws, len(ws) / self.wpf):
                    tmp = "".join(chunk)
                    words.append(tmp)
        return words

    def getFeatures(self, word):
        """
        Return word positions, and position of marked char
        :return str, int, float
            word, position of marked char, time
        """
        w = word.strip()
        pos = self.getWordPos(word)
        t = self.getWordCount(word)
        return w, pos, t
