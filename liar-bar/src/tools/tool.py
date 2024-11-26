import random
import time
from typing import List

from agentscope.service import (
    ServiceResponse,
    ServiceExecStatus,
)


def execute_divination(cards: List[str], target_card: str) -> ServiceResponse:
    """
    执行占卜函数，根据传入的卡牌序列决定出牌或质疑，并返回占卜结果。

    Args:
        cards (List[str]): 玩家手中的卡牌序列，例如 ['A', 'A', 'K', 'K', 'Joker']
        target_card (str): 本轮目标牌, 例如: 'K'
    """
    random.seed(time.time())
    # 计算真牌和假牌的数量
    true_cards = [card for card in cards if card == target_card or card.lower() == 'joker']
    num_true_cards = len(true_cards)
    num_false_cards = len(cards) - num_true_cards

    # 随机决定出牌或质疑
    actions = ['出牌', '质疑']
    action = random.choice(actions)

    # 如果决定出牌，再随机决定出真牌或假牌
    if action == '出牌':
        if num_true_cards > 0 and num_false_cards > 0:
            # 如果既有真牌也有假牌，随机选择
            is_true_card = random.choice([True, False])
        elif num_true_cards > 0:
            # 只有真牌
            is_true_card = True
        else:
            # 只有假牌
            is_true_card = False

        # 随机决定出牌数量
        if is_true_card:
            number_of_cards = random.randint(1, min(3, num_true_cards))
        else:
            number_of_cards = random.randint(1, min(3, num_false_cards))
    else:
        is_true_card = None
        number_of_cards = None

    result = f"本轮占卜结果: 选择{action}"
    if action == '出牌':
        result += f", 出{number_of_cards}张{('真' if is_true_card else '假')}牌。"

    return ServiceResponse(status=ServiceExecStatus.SUCCESS, content=result)
