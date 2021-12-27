import operator


class Statistics:
    """
    This class saves the best in the server since it began to run
    """

    def __init__(self):
        self.bestPlayer = ""
        self.worstPlayers = ""
        self.fastPlayer = ""
        self.bestScore = 20
        self.mostGamePlayer = ""
        self.all_winners = {}
        self.all_losers = {}
        self.all_players = {}

    def update(self, scores):
        """
        Checks if best score should be updated and updates
        :param best_team: New team name
        :param best_score: New team's score
        :return:
        """
        winner = min(scores.items(), key=operator.itemgetter(1))[0]
        looser = max(scores.items(), key=operator.itemgetter(1))[0]
        bestScore = min(scores.items(), key=operator.itemgetter(1))[1]
        print(scores)
        print(looser)
        print(bestScore)


        if bestScore < self.bestScore:
            self.bestScore = bestScore
            self.fastPlayer = winner

        if winner not in self.all_winners:
            self.all_winners[winner] = 1
        else:
            self.all_winners[winner] += 1
        self.bestPlayer = max(self.all_winners.items(), key=operator.itemgetter(1))[0]

        if looser not in self.all_losers:
            self.all_losers[looser] = 1
        else:
            self.all_losers[looser] += 1
        self.worstPlayers = max(self.all_losers.items(), key=operator.itemgetter(1))[0]

        if winner not in self.all_players:
            self.all_players[winner] = 1
        else:
            self.all_players[winner] += 1
        if looser not in self.all_players:
            self.all_players[looser] = 1
        else:
            self.all_players[looser] += 1
        self.mostGamePlayer = max(self.all_players.items(), key=operator.itemgetter(1))[0]

    def printStatistic(self):
        msg = '\n'
        msg += "Best player ever : " + self.bestPlayer + '\n'
        msg += "Fastest player ever :" + self.fastPlayer + '\n'
        msg += "Most game player : " + self.mostGamePlayer + '\n'
        msg += "Worst player ever : " + self.worstPlayers + '\n'
        return msg
