"""
Conservative Bot - Plays very tight and safe
Only plays strong hands and folds most of the time
"""
from typing import List, Dict, Any

from bot_api import PokerBotAPI, PlayerAction, GameInfoAPI
from engine.cards import Card, Rank
from engine.poker_game import GameState


class ConservativeBot(PokerBotAPI):
    """
    A conservative bot that only plays very strong hands.
    Good example of a tight playing style.
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self.hands_played = 0
        self.hands_won = 0
        
        # Define strong starting hands
        self.premium_hands = [
            (Rank.ACE, Rank.ACE), (Rank.KING, Rank.KING), (Rank.QUEEN, Rank.QUEEN),
            (Rank.JACK, Rank.JACK), (Rank.TEN, Rank.TEN), (Rank.NINE, Rank.NINE),
            (Rank.ACE, Rank.KING), (Rank.ACE, Rank.QUEEN), (Rank.ACE, Rank.JACK),
            (Rank.KING, Rank.QUEEN), (Rank.KING, Rank.JACK), (Rank.QUEEN, Rank.JACK)
        ]
    
    def get_action(self, game_state: GameState, hole_cards: List[Card], 
                   legal_actions: List[PlayerAction], min_bet: int, max_bet: int) -> tuple:
        """Play very conservatively - only strong hands"""
        
        if len(hole_cards) != 2:
            return PlayerAction.FOLD, 0
        
        card1, card2 = hole_cards
        
        # Check if we have a premium hand
        hand_tuple1 = (card1.rank, card2.rank)
        hand_tuple2 = (card2.rank, card1.rank)  # Check both orders
        
        is_premium = (hand_tuple1 in self.premium_hands or 
                     hand_tuple2 in self.premium_hands)
        
        # Also consider suited premium hands
        is_suited_premium = (card1.suit == card2.suit and 
                           (hand_tuple1 in self.premium_hands or 
                            hand_tuple2 in self.premium_hands))
        
        # Check for high pocket pairs
        is_high_pocket_pair = (card1.rank == card2.rank and 
                              card1.rank.value >= 9)  # 9s or better
        
        # Only play premium hands or high pocket pairs
        if not (is_premium or is_suited_premium or is_high_pocket_pair):
            return PlayerAction.FOLD, 0
        
        # We have a good hand - decide what to do
        # Prioritize actions: RAISE, then CALL, then CHECK, otherwise FOLD

        if PlayerAction.RAISE in legal_actions:
            # Conservative raise - don't go too big
            current_pot = game_state.pot
            # Ensure raise amount is at least min_bet and within max_bet
            # Attempt to raise by a third of the pot, but adjust if it's too small or too large
            # The current_bet + 2 * big_blind is a common minimum raise amount
            min_raise_amount = game_state.current_bet + game_state.big_blind
            suggested_raise = max(min_raise_amount, game_state.current_bet + current_pot // 3)
            raise_amount = min(suggested_raise, max_bet)
            
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
        
        # If no other legal action, fold as fallback (should be handled by game engine anyway)
        return PlayerAction.FOLD, 0
    
    def hand_complete(self, game_state: GameState, hand_result: Dict[str, Any]):
        """Track conservative play results"""
        self.hands_played += 1
        
        if 'winners' in hand_result and self.name in hand_result['winners']:
            self.hands_won += 1
        
        # Log statistics every round
        if self.hands_played % 8 == 0:
            win_rate = self.hands_won / self.hands_played if self.hands_played > 0 else 0
            self.logger.info(f"Conservative play: {self.hands_won}/{self.hands_played} wins ({win_rate:.2%})")