from random import randint


class Answer:
    '''
    This class implements storage for an answer you want to conceil
    and give clues 1 letter at a time.

    '''

    def __init__(self, answer='None'):
        self._answer = answer
        self._masked_answer = str()

        for i in self._answer:
            if i.isalnum():
                self._masked_answer += '*'
            else:
                self._masked_answer += i

    def give_clue(self):
        ''' Returns the masked string after revealing
        a letter and saving the mask.
        '''
        if self._answer == self._masked_answer:
            return self._masked_answer

        letter = ' '

        while not letter.isalnum():
            index = randint(0, len(self._answer)-1)
            letter = self._answer[index]
            if self._masked_answer[index] == letter:
                letter = ' '

        temp = list(self._masked_answer)

        temp[index] = letter

        self._masked_answer = "".join(temp)

        return self._masked_answer

    def current_clue(self):
        return self._masked_answer

    def set_answer(self, new_answer):
        '''Makes this object reusable,
        sets a new answer and clue mask.
        '''
        self.__init__(answer=new_answer)

    def _reveal(self):
        '''Returns the answer string.'''
        return self._answer

    answer = property(_reveal)
