"""
Poker card and deck management system
"""
import random
from enum import Enum
from typing import List, Tuple, Optional
from dataclasses import dataclass
from itertools import combinations


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


@dataclass
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        rank_str = {
            Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4", Rank.FIVE: "5",
            Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8", Rank.NINE: "9",
            Rank.TEN: "10", Rank.JACK: "J", Rank.QUEEN: "Q", Rank.KING: "K", Rank.ACE: "A"
        }
        return f"{rank_str[self.rank]}{self.suit.value}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))


class Deck:
    def __init__(self):
        self.cards: List[Card] = []
        self.reset()

    def reset(self):
        """Reset deck with all 52 cards"""
        self.cards = [Card(rank, suit) for rank in Rank for suit in Suit]

    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)

    def deal_card(self) -> Optional[Card]:
        """Deal one card from the top of the deck"""
        if self.cards:
            return self.cards.pop()
        return None

    def cards_remaining(self) -> int:
        """Get number of cards remaining in deck"""
        return len(self.cards)


class HandEvaluator:
    """Evaluates poker hands and determines winners"""

    HAND_RANKINGS = {
        'high_card': 1,
        'pair': 2,
        'two_pair': 3,
        'three_of_a_kind': 4,
        'straight': 5,
        'flush': 6,
        'full_house': 7,
        'four_of_a_kind': 8,
        'straight_flush': 9,
        'royal_flush': 10
    }

    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[str, List[int]]:
        """
        Evaluate a 5-card poker hand
        Returns: (hand_type, tie_breakers)
        tie_breakers is a list of ranks for comparison in case of ties
        """
        if len(cards) != 5:
            raise ValueError("Hand must contain exactly 5 cards")

        # Sort cards by rank (highest first)
        sorted_cards = sorted(cards, key=lambda x: x.rank.value, reverse=True)
        ranks = [card.rank.value for card in sorted_cards]
        suits = [card.suit for card in sorted_cards]

        # Check for flush
        is_flush = len(set(suits)) == 1

        # Check for straight
        is_straight = HandEvaluator._is_straight(ranks)

        # Count ranks
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1

        # Sort by count, then by rank
        count_groups = {}
        for rank, count in rank_counts.items():
            if count not in count_groups:
                count_groups[count] = []
            count_groups[count].append(rank)

        # Sort each group by rank (highest first)
        for count in count_groups:
            count_groups[count].sort(reverse=True)

        # Determine hand type
        counts = sorted(rank_counts.values(), reverse=True)

        if is_straight and is_flush:
            if ranks[0] == Rank.ACE.value and ranks[1] == Rank.KING.value:
                return 'royal_flush', ranks
            return 'straight_flush', ranks
        elif counts[0] == 4:
            return 'four_of_a_kind', [count_groups[4][0], count_groups[1][0]]
        elif counts == [3, 2]:
            return 'full_house', [count_groups[3][0], count_groups[2][0]]
        elif is_flush:
            return 'flush', ranks
        elif is_straight:
            if ranks == [14, 5, 4, 3, 2]: # Ace-low straight
                return 'straight', [5, 4, 3, 2, 1]
            return 'straight', ranks
        elif counts[0] == 3:
            return 'three_of_a_kind', [count_groups[3][0]] + sorted(count_groups[1], reverse=True)
        elif counts == [2, 2, 1]:
            pairs = sorted(count_groups[2], reverse=True)
            return 'two_pair', pairs + [count_groups[1][0]]
        elif counts[0] == 2:
            return 'pair', [count_groups[2][0]] + sorted(count_groups[1], reverse=True)
        else:
            return 'high_card', ranks

    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        """Check if ranks form a straight"""
        # Handle ace-low straight (A-2-3-4-5)
        if sorted(ranks) == [2, 3, 4, 5, 14]:
            return True
        
        unique_ranks = sorted(list(set(ranks)), reverse=True)
        if len(unique_ranks) < 5:
            return False

        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i] - unique_ranks[i+4] == 4:
                return True
        return False

    @staticmethod
    def evaluate_best_hand(all_cards: List[Card]) -> Tuple[str, List[int], List[Card]]:
        """
        Evaluates the best 5-card hand from a list of cards.
        Returns: (hand_type, tie_breakers, best_hand_cards)
        """
        if len(all_cards) < 5:
            raise ValueError("Must have at least 5 cards to evaluate.")

        best_hand_combination = None
        best_hand_type = ''
        best_tiebreakers = []
        best_rank = -1

        for hand_combination in combinations(all_cards, 5):
            hand_list = list(hand_combination)
            hand_type, tiebreakers = HandEvaluator.evaluate_hand(hand_list)
            rank = HandEvaluator.HAND_RANKINGS[hand_type]

            if rank > best_rank:
                best_rank = rank
                best_hand_type = hand_type
                best_tiebreakers = tiebreakers
                best_hand_combination = hand_list
            elif rank == best_rank:
                # Compare tiebreakers for hands of the same rank
                for i in range(len(tiebreakers)):
                    if tiebreakers[i] > best_tiebreakers[i]:
                        best_hand_type = hand_type
                        best_tiebreakers = tiebreakers
                        best_hand_combination = hand_list
                        break
                    elif tiebreakers[i] < best_tiebreakers[i]:
                        break
        
        return best_hand_type, best_tiebreakers, best_hand_combination

    @staticmethod
    def get_winners(player_hands: List[Tuple[str, List[Card]]]) -> List[str]:
        """
        Compare multiple hands and determine the winner(s)
        player_hands: A list of tuples, each containing (player_id, cards)
        Returns: A list of player_ids who are winners
        """
        if not player_hands:
            return []

        best_hands = {}  # player_id -> (hand_type, tiebreakers)

        for player_id, all_cards in player_hands:
            hand_type, tiebreakers, _ = HandEvaluator.evaluate_best_hand(all_cards)
            best_hands[player_id] = (hand_type, tiebreakers)

        winners = []
        best_hand_so_far = None

        for player_id, hand_info in best_hands.items():
            if not best_hand_so_far:
                best_hand_so_far = hand_info
                winners = [player_id]
                continue

            hand_rank = HandEvaluator.HAND_RANKINGS[hand_info[0]]
            best_rank = HandEvaluator.HAND_RANKINGS[best_hand_so_far[0]]

            if hand_rank > best_rank:
                best_hand_so_far = hand_info
                winners = [player_id]
            elif hand_rank == best_rank:
                # Same hand type, compare tiebreakers
                tiebreakers = hand_info[1]
                best_tiebreakers = best_hand_so_far[1]
                is_tie = True
                for i in range(len(tiebreakers)):
                    if tiebreakers[i] > best_tiebreakers[i]:
                        best_hand_so_far = hand_info
                        winners = [player_id]
                        is_tie = False
                        break
                    elif tiebreakers[i] < best_tiebreakers[i]:
                        is_tie = False
                        break
                if is_tie:
                    winners.append(player_id)
        
        return winners