"""
Aggressive Bot - Plays loose and aggressive
Bets and raises frequently, plays many hands
"""
from typing import List, Dict, Any
import random

from bot_api import PokerBotAPI, PlayerAction, GameInfoAPI
from engine.cards import Card, Rank, HandEvaluator
from engine.poker_game import GameState


class AggressiveBot(PokerBotAPI):
    """
    An aggressive bot that plays loose and raises frequently.
    Good example of an aggressive playing style.
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self.hands_played = 0
        self.raise_frequency = 0.5  # Default raise frequency
        self.play_frequency = 0.8   # Play 80% of hands
        
    def get_action(self, game_state: GameState, hole_cards: List[Card], 
                   legal_actions: List[PlayerAction], min_bet: int, max_bet: int) -> tuple:
        """Play aggressively - bet and raise often"""
        
        if game_state.round_name == "preflop":
            return self._preflop_strategy(game_state, hole_cards, legal_actions, min_bet, max_bet)
        else:
            return self._postflop_strategy(game_state, hole_cards, legal_actions, min_bet, max_bet)

    def _preflop_strategy(self, game_state: GameState, hole_cards: List[Card], legal_actions: List[PlayerAction], 
                          min_bet: int, max_bet: int) -> tuple:
        """Aggressive pre-flop strategy"""
        if random.random() > self.play_frequency:
            if PlayerAction.CHECK in legal_actions:
                return PlayerAction.CHECK, 0
            return PlayerAction.FOLD, 0

        # High probability of raising
        if PlayerAction.RAISE in legal_actions and random.random() < self.raise_frequency:
            # Raise 3-4x the big blind
            raise_amount = min(random.randint(3, 4) * game_state.big_blind, max_bet)
            raise_amount = max(raise_amount, min_bet)
            
            # Ensure raise amount is actually greater than current_bet if raising
            if raise_amount > game_state.current_bet:
                return PlayerAction.RAISE, raise_amount
            elif PlayerAction.CALL in legal_actions:
                return PlayerAction.CALL, 0
            elif PlayerAction.CHECK in legal_actions:
                return PlayerAction.CHECK, 0
        
        if PlayerAction.CALL in legal_actions:
            return PlayerAction.CALL, 0
            
        if PlayerAction.CHECK in legal_actions:
            return PlayerAction.CHECK, 0

        return PlayerAction.FOLD, 0

    def _postflop_strategy(self, game_state: GameState, hole_cards: List[Card], 
                           legal_actions: List[PlayerAction], min_bet: int, max_bet: int) -> tuple:
        """Aggressive post-flop strategy"""
        all_cards = hole_cards + game_state.community_cards
        hand_type, _, _ = HandEvaluator.evaluate_best_hand(all_cards)
        hand_rank = HandEvaluator.HAND_RANKINGS[hand_type]

        # Strong hand (top pair or better)
        if hand_rank >= HandEvaluator.HAND_RANKINGS['pair']:
            if PlayerAction.RAISE in legal_actions:
                # Bet 2/3 to full pot
                raise_amount = min(game_state.pot, max_bet)
                raise_amount = max(raise_amount, min_bet)
                
                if raise_amount > game_state.current_bet:
                    return PlayerAction.RAISE, raise_amount
                elif PlayerAction.CALL in legal_actions:
                    return PlayerAction.CALL, 0
                elif PlayerAction.CHECK in legal_actions:
                    return PlayerAction.CHECK, 0
            
            if PlayerAction.CALL in legal_actions:
                return PlayerAction.CALL, 0
            if PlayerAction.CHECK in legal_actions:
                return PlayerAction.CHECK, 0
        
        # Strong draw - play aggressively (semi-bluff)
        if self._has_strong_draw(all_cards):
            if PlayerAction.RAISE in legal_actions:
                 # Bet half pot on a draw
                raise_amount = min(game_state.pot // 2, max_bet)
                raise_amount = max(raise_amount, min_bet)
                
                if raise_amount > game_state.current_bet:
                    return PlayerAction.RAISE, raise_amount
                elif PlayerAction.CALL in legal_actions:
                    return PlayerAction.CALL, 0
                elif PlayerAction.CHECK in legal_actions:
                    return PlayerAction.CHECK, 0
            
            if PlayerAction.CALL in legal_actions:
                return PlayerAction.CALL, 0
            if PlayerAction.CHECK in legal_actions:
                return PlayerAction.CHECK, 0

        # Bluffing opportunity?
        # If no one has bet, take a stab at the pot
        if game_state.current_bet == 0 and PlayerAction.RAISE in legal_actions:
            bluff_raise = min(game_state.pot // 2, max_bet)
            bluff_raise = max(bluff_raise, min_bet)
            if random.random() < 0.25: # Bluff 25% of the time
                if bluff_raise > game_state.current_bet:
                    return PlayerAction.RAISE, bluff_raise
                elif PlayerAction.CHECK in legal_actions:
                    return PlayerAction.CHECK, 0
        
        if PlayerAction.CHECK in legal_actions:
            return PlayerAction.CHECK, 0
        
        return PlayerAction.FOLD, 0

    def _has_strong_draw(self, all_cards: List[Card]) -> bool:
        """Check for strong drawing hands (flush or open-ended straight)"""
        # Flush draw
        suits = [card.suit for card in all_cards]
        for suit in set(suits):
            if suits.count(suit) == 4:
                return True
        
        # Open-ended straight draw
        ranks = sorted(list(set(card.rank.value for card in all_cards)))
        for i in range(len(ranks) - 3):
            if ranks[i+3] - ranks[i] == 3 and len(ranks) >=4 :
                return True
            if set(ranks).issuperset({2,3,4,5}) or set(ranks).issuperset({14,2,3,4}):
                 return True
        return False
    
    def hand_complete(self, game_state: GameState, hand_result: Dict[str, Any]):
        self.hands_played += 1
        if 'winners' in hand_result and self.name in hand_result['winners']:
            # Won - be more aggressive
            self.raise_frequency = min(0.7, self.raise_frequency + 0.02)
        else:
            # Lost - tone it down
            self.raise_frequency = max(0.3, self.raise_frequency - 0.01)
    
    def tournament_start(self, players: List[str], starting_chips: int):
        super().tournament_start(players, starting_chips)
        if len(players) <= 4:
            self.raise_frequency = 0.6
            self.play_frequency = 0.9
        elif len(players) >= 8:
            self.raise_frequency = 0.4
            self.play_frequency = 0.7