from answer import Answer
import json
from os import listdir, path, makedirs
from random import choice
import config


class trivia:
    ''' This class implements the trivia game itself.
    Later on, I will finish documenting its methods here.
    '''
    def __init__(self, config):
        # We need an Answer class to hide the answers.
        self._answer = Answer()
        # Questions are trivial, so we just store the string.
        self._question = ''
        # Need to store the scores in a dict.
        self._scores = {}
        # Initialize the number of clues we've given.
        self._clue_number = 0
        # This should be more configurable.
        self._current_points = 5
        # Know where our questions are kept.
        self._questions_dir = config.Q_DIR
        # Loads the game.
        self._load_game()
        # Implements a voting counter.
        self._votes = 0
        # A list to hold on to who has voted.
        self._voters = []
        # Hold on to the configuration.
        self._config = config

    def play_game(self, msg):
        '''
        Implements the main loop of the game.
        '''
        points = {0: 5,
                  1: 3,
                  2: 2,
                  3: 1
                  }
        if self._clue_number == 0:
            self._votes = 0
            self._voters = []
            self._get_new_question()
            self._current_points = points[self._clue_number]
            # Blank line.
            msg("")
            msg("Next question:")
            msg(self._question)
            msg("Clue: %s" % self._answer.current_clue())
            self._clue_number += 1
        # we must be somewhere in between
        elif self._clue_number < 4:
            self._current_points = points[self._clue_number]
            msg("Question:")
            msg(self._question)
            msg('Clue: %s' % self._answer.give_clue())
            self._clue_number += 1
        # no one must have gotten it.
        else:
            msg('No one got it. The answer was: %s' %
                self._answer.answer)
            self._clue_number = 0
            self._get_new_question()

    def start_msg(self, msg, channel, nickname):
            msg('Welcome to %s!' % channel)
            msg("Have an admin start the game when you are ready.")
            msg("For how to use this bot, just say ?help or")
            msg("%s help." % nickname)

    def _help(self, args, user, channel):
        '''
        Tells people how to use the bot.
        Replies differently if you are an admin or a regular user.
        Only responds to the user since there could be a game in
        progress.

        Belongs in the game class.
        '''
        try:
            self._admins.index(user)
        except:
            self._cmsg(user, "I'm nameless's trivia bot.")
            self._cmsg(user, "Commands: score, giveclue, help, "
                       "next, source")
            return
        self._cmsg(user, "I'm nameless's trivia bot.")
        self._cmsg(user, "Commands: score, giveclue, help, next, "
                   "skip, source")
        self._cmsg("Admin commands: die, set <user> <score>, start, stop, "
                   "save")

    def _winner(self, user, channel):
        '''
        Congratulates the winner for guessing correctly and assigns
        points appropriately, then signals that it was guessed.

        Belongs in the game class.
        '''
        if channel != self._game_channel:
            self.msg(channel,
                     "I'm sorry, answers must be given in the game channel.")
            return
        self._gmsg("%s GOT IT!" % user.upper())
        try:
            self._scores[user] += self._current_points
        except:
            self._scores[user] = self._current_points
        if self._current_points == 1:
            self._gmsg("%s point has been added to your score!" %
                       str(self._current_points))
        else:
            self._gmsg("%s points have been added to your score!" %
                       str(self._current_points))
        self._clue_number = 0
        self._get_new_question()

    def _show_source(self, args, user, channel):
        '''
        Tells people how to use the bot.
        Only responds to the user since there could be a game in
        progress.
        '''
        self._cmsg(user, 'My source can be found at: '
                   'https://github.com/rawsonj/triviabot')

    def select_command(self, command, args, user, channel):
        '''
        Callback that responds to commands given to the bot.

        Need to differentiate between priviledged users and regular
        users.

        Belongs in the game class.
        '''
        # set up command dicts.
        unpriviledged_commands = {'score': self._score,
                                  'help': self._help,
                                  'source': self._show_source,
                                  'giveclue': self._give_clue,
                                  'next': self._next_vote,
                                  'skip': self._next_question
                                  }
        priviledged_commands = {'die': self._die,
                                'set': self._set_user_score,
                                'start': self._start,
                                'stop': self._stop,
                                'save': self._save_game,
                                }
        print(command, args, user, channel)
        try:
            self._admins.index(user)
            is_admin = True
        except:
            is_admin = False

        # the following takes care of sorting out functions and
        # priviledges.
        if not is_admin and command in priviledged_commands.keys():
            self.msg(channel, "%s: You don't tell me what to do." % user)
            return
        elif is_admin and command in priviledged_commands.keys():
            priviledged_commands[command](args, user, channel)
        elif command in unpriviledged_commands.keys():
            unpriviledged_commands[command](args, user, channel)
        else:
            self.describe(channel, '%slooks at %s oddly.' %
                          (self._config.COLOR_CODE, user))

    def _next_vote(self, args, user, channel):
        '''Implements user voting for the next question.
        Need to keep track of who voted, and how many votes.
        Should go in game class.
        '''
        if not self._lc.running:
            self._gmsg("We aren't playing right now.")
            return
        try:
            self._voters.index(user)
            self._gmsg("You already voted, %s, give someone else a chance to "
                       "hate this question" % user)
            return
        except:
            if self._votes < 2:
                self._votes += 1
                self._voters.append(user)
                print(self._voters)
                self._gmsg("%s, you have voted. %s more votes needed to "
                           "skip." % (user, str(3-self._votes)))
            else:
                self._votes = 0
                self._voters = []
                self._next_question(None, None, None)

    def _start(self, *args):
        '''
        Starts the trivia game.

        TODO: Load scores from last game, if any.

        This should try to be in a game class,
        but might have to stay here because it involves the loopback function.
        '''
        if self._lc.running:
            return
        else:
            self._lc.start(config.WAIT_INTERVAL)
            self.factory.running = True

    def _stop(self, *args):
        '''
        Stops the game and thanks people for playing,
        then saves the scores.
        Should be in game class.
        '''
        if not self._lc.running:
            return
        else:
            self._lc.stop()
            self._gmsg('Thanks for playing trivia!')
            self._gmsg('Current rankings were:')
            self._standings(None, self._game_channel, None)
            self._gmsg('''Scores have been saved, and see you next game!''')
            self._save_game()
            self.factory.running = False

    def _save_game(self, *args):
        '''
        Saves the game to the data directory.
        Should be in game class.
        '''
        if not path.exists(config.SAVE_DIR):
            makedirs(config.SAVE_DIR)
        with open(config.SAVE_DIR+'scores.json', 'w') as savefile:
            json.dump(self._scores, savefile)
            print("Scores have been saved.")

    def _load_game(self):
        '''
        Loads the running data from previous games.
        Game class.
        '''
        # ensure initialization
        self._scores = {}
        if not path.exists(config.SAVE_DIR):
            print("Save directory doesn't exist.")
            return
        try:
            with open(config.SAVE_DIR+'scores.json', 'r') as savefile:
                temp_dict = json.load(savefile)
        except:
            print("Save file doesn't exist.")
            return
        for name in temp_dict.keys():
            self._scores[str(name)] = int(temp_dict[name])
        print(self._scores)
        print("Scores loaded.")

    def _set_user_score(self, args, user, channel):
        '''
        Administrative action taken to adjust scores, if needed.

        TODO: Should handle relative increment/decrement.
        Should go in game class.
        '''
        try:
            self._scores[args[0]] = int(args[1])
        except:
            self._cmsg(user, args[0]+" not in scores database.")
            return
        self._cmsg(user, args[0]+" score set to "+args[1])

    def _score(self, args, user, channel):
        '''
        Tells the user their score.

        Should be in game class.
        '''
        try:
            self._cmsg(user, "Your current score is: %s" %
                       str(self._scores[user]))
        except:
            self._cmsg(user, "You aren't in my database.")

    def _next_question(self, args, user, channel):
        '''
        Administratively skips the current question.

        Should be in game class.
        '''
        if not self._lc.running:
            self._gmsg("We are not playing right now.")
            return
        self._gmsg("Question has been skipped. The answer was: %s" %
                   self._answer.answer)
        self._clue_number = 0
        self._lc.stop()
        self._lc.start(config.WAIT_INTERVAL)

    def _standings(self, args, user, channel):
        '''
        Tells the user the complete standings in the game.

        Goes in game class, but really isn't viable anymore.
        Should only give top 5 and the standing of the person who called
        it.
        '''
        self._cmsg(user, "The current trivia standings are: ")
        sorted_scores = sorted(self._scores.iteritems(), key=lambda k, v:
                               (v, k), reverse=True)
        for rank, (player, score) in enumerate(sorted_scores, start=1):
            formatted_score = "%s: %s: %s" % (rank, player, score)
            self._cmsg(user, str(formatted_score))

    def _give_clue(self, args, user, channel):
        ''' Repeats a clue. Really, should force the bot to advance the glue,
            even if it goes out of bounds.
            Should go in game class.
        '''
        if not self._lc.running:
            self._gmsg("we are not playing right now.")
            return
        self._cmsg(channel, "Question: ")
        self._cmsg(channel, self._question)
        self._cmsg(channel, "Clue: "+self._answer.current_clue())

    def _get_new_question(self):
        '''
        Selects a new question from the questions directory and
        sets it.

        Should be in game class.
        '''
        damaged_question = True
        while damaged_question:
            # randomly select file
            filename = choice(listdir(self._questions_dir))
            fd = open(config.Q_DIR+filename)
            lines = fd.read().splitlines()
            myline = choice(lines)
            fd.close()
            try:
                self._question, temp_answer = myline.split('`')
            except ValueError:
                print("Broken question:")
                print(myline)
                continue
            self._answer.set_answer(temp_answer.strip())
            damaged_question = False
