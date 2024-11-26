# Copyright (c) 2024 King Jingxiang
# See the LICENSE file for license rights and limitations (MIT).
import copy
import random
import time

import prompts as rule
import tools.tool as tools
from agents.dict_dialog_agent import DictDialogAgent
from agentscope.message import Msg
from agentscope.parsers.json_object_parser import MarkdownJsonDictParser


class GameError(Exception):
    """自定义异常类，用于表示游戏中的错误情况。"""
    pass


class Game:
    def __init__(self):
        self.player_status = {
            "player1": {"is_alive": True, "style": "coward", "elimination_factor": 5, "agent": None},
            "player2": {"is_alive": True, "style": "coward", "elimination_factor": 5, "agent": None},
            "player3": {"is_alive": True, "style": "coward", "elimination_factor": 5, "agent": None},
            "player4": {"is_alive": True, "style": "coward", "elimination_factor": 5, "agent": None},
        }
        self.total_rounds = []
        self.current_round = []
        self.player_cards = {}
        self.player_dialog = []
        self.challenge_info = []
        self.game_logs = []
        self.current_player = "player1"
        self.total_cards = ["A", "K", "Q"] * 6
        self.target_card = ""
        self.players = ["player1", "player2", "player3", "player4"]
        self.agents = []
        self.model_configuration_name = "aistudio"
        self.action_space = ["trust", "challenge"]

    def initialize_agents(self):

        agents = [
            DictDialogAgent("coward", rule.rule + "\n" + rule.coward_role, self.model_configuration_name,
                            use_memory=False),
            DictDialogAgent("augur", rule.rule + "\n" + rule.augur_role, self.model_configuration_name,
                            use_memory=False),
            DictDialogAgent("bold_gambler", rule.rule + "\n" + rule.bold_gambler_rule, self.model_configuration_name,
                            use_memory=False),
            DictDialogAgent("cool_analyzer", rule.rule + "\n" + rule.cool_analyzer_rule, self.model_configuration_name,
                            use_memory=False),
            DictDialogAgent("cunning_liar", rule.rule + "\n" + rule.cunning_liar_rule, self.model_configuration_name,
                            use_memory=False),
        ]

        parser = MarkdownJsonDictParser(
            content_hint={
                "thought": "What you thought?",
                "action": "What will you do? Choose from [trust, challenge]",
                "cards": "Which cards will you play? Select from ['A', 'K', 'Q'], e.g., ['Q', 'Q']",
                "misleading_statements": "What statements will you make to mislead the opponent?",
            },
            required_keys=["thought", "action", "cards"],
            keys_to_content=["thought", "action", "cards", "misleading_statements"])

        for agent in agents:
            agent.set_parser(parser)
        self.agents = agents

    def initialize_players(self, styles=None):
        """初始化玩家状态"""
        if styles is None:
            styles = ["normal", "user", "normal", "normal"]

        # 确保玩家数量与风格列表长度匹配
        assert len(self.players) == len(styles), "玩家数量与风格列表长度不匹配"
        agent_map = {agent.name: agent for agent in self.agents}
        # 使用enumerate来获取索引和玩家
        for i, player in enumerate(self.players):
            self.player_status[player]["style"] = styles[i]
            if styles[i] != "user":
                agent = agent_map.get(styles[i])
                if agent is not None:
                    self.player_status[player]["agent"] = agent
                else:
                    # 处理没有找到匹配代理的情况
                    print(f"Warning: No agent found with name {styles[i]}")

    def get_current_player_prompt(self):
        """提示词构造"""
        cards = self.player_cards[self.current_player]
        cards_str = ', '.join(cards)
        round_info = self.get_current_round()
        if len(self.current_round) > 0:
            num = len(self.current_round[-1]["cards"])
            prompt = rule.current_player_prompt.format(player=self.current_player, target_card=self.target_card,
                                                       cards=cards_str, last_player_play_num=num, round_info=round_info)
        else:
            prompt = rule.first_player_prompt.format(player=self.current_player, target_card=self.target_card,
                                                     cards=cards_str)
        return prompt

    def check_played_cards(self, played_cards):
        """检查玩家是否 played_cards 是否合法"""
        try:
            user_cards = copy.deepcopy(self.player_cards[self.current_player])
            for c in played_cards:
                user_cards.remove(c)
            return True
        except ValueError:
            return False

    def get_player_dialogs(self):
        """获取玩家对话"""
        return "\n".join(self.player_dialog)

    def player_think(self, max_retry=3):
        # return "trust", self.player_cards[self.current_player][0], None, None
        agent = self.player_status[self.current_player]["agent"]
        prompt = self.get_current_player_prompt()
        if self.player_status[self.current_player]["style"] == "augur":
            response = tools.execute_divination(self.player_cards[self.current_player], self.target_card)
            prompt += f"\n{response.content}"
        msg = Msg(name="user", role="user", content=prompt)
        for attempt in range(max_retry + 1):  # +1 是因为range从0开始计数
            try:
                response = agent(msg)
                action = response.content["action"]
                # 检查动作是否合法
                if action not in self.action_space:
                    raise GameError(f"Invalid action: {action}")
                cards = response.content["cards"]
                if not self.check_played_cards(cards):  # 检查卡牌是否有效
                    raise GameError("Invalid cards")
                dialog = response.content.get("misleading_statements", None)
                thought = response.content.get("thought", None)
                if dialog:
                    self.player_dialog.append(f"{self.current_player}: {response.content['misleading_statements']}")
                return action, cards, thought, dialog  # 成功返回动作和卡牌
            except GameError as e:
                if attempt < max_retry:
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                else:
                    print(f"Failed after {max_retry} attempts. Giving up.")
        # 异常情况打出第0张牌
        return "trust", self.player_cards[self.current_player][0], None, None

    def current_player_is_user(self):
        return self.player_status[self.current_player]["style"] == "user"

    def _add_to_current_round(self, action, cards=None, thought=None, dialog=None):
        """添加当前轮次的玩家动作和卡牌"""
        self.current_round.append({"player": self.current_player, "action": action, "cards": cards or []})
        self.game_logs.append(
            {"player": self.current_player, "action": action, "cards": cards or [], "thought": thought,
             "dialog": dialog})

    def turn_new_round(self):
        """结束当前轮次并开始新的一轮"""
        self.total_rounds.append(self.current_round.copy())
        self.current_round.clear()
        self.start_new_round()

    def get_current_round(self):
        """获取当前轮次的信息"""
        info = ""
        for entry in self.current_round:
            info += f"{entry['player']} play {len(entry['cards'])}张目标牌{self.target_card}\n"
        return info

    def get_game_logs(self, debug=False):
        # 使用不同的颜色定义每条记录
        colors = ["#FF5733", "#33FF57", "#3357FF", "#FF33A1", "#C70039"]  # 示例颜色列表
        color_index = 0  # 用于循环选择颜色

        info = "<div>"
        for entry in self.game_logs:
            # 选择颜色，并确保颜色索引在有效范围内循环
            color = colors[color_index % len(colors)]
            color_index += 1

            # 构建基础信息
            if len(entry['cards']) == 0:
                log_info = f"<span style='color:{color}'>{entry['player']}选择了质疑!<br></span>"
            else:
                log_info = f"<span style='color:{color}'>{entry['player']} play {len(entry['cards'])}张目标牌{self.target_card}<br></span>"

            # 如果有对话，则添加到log_info
            if entry['dialog']:
                log_info += f"<span style='color:{color}'>{entry['player']} say: {entry['dialog']}<br></span>"

            # 如果是调试模式且有思考内容，则添加到log_info
            if debug and entry['thought']:
                log_info += f"<span style='color:{color}'>{entry['player']} thought: {entry['thought']}<br></span>"

            # 将当前记录添加到总信息中
            info += log_info

        info += "</div>"
        return info

    def get_challenge_info(self, html_format=True):
        if html_format:
            txt = "\n".join(self.challenge_info)
            return f"```\n{txt}\n```"
        else:
            return "\n".join(self.challenge_info)

    def get_game_info(self):
        info = ""
        for entry in self.current_round:
            info += f"{entry['player']} play {len(entry['cards'])}张目标牌{self.target_card}\n"
        return info

    def get_total_rounds(self):
        """获取所有轮次的信息"""
        result = ""
        info = ""
        for index, round in enumerate(self.total_rounds):
            for entry in round:
                info += f"{entry['player']} {entry['action']} {len(entry['cards'])}张目标牌\n"
            result += f"第{index + 1}轮:\n{info}\n"
        return result.strip()

    def update_current_player_cards(self, played_cards):
        """更新当前玩家的卡牌"""
        current_cards = self.player_cards[self.current_player]
        # 使用列表推导式去除已玩的卡片
        for card in played_cards:
            current_cards.remove(card)
        self.player_cards[self.current_player] = current_cards

    def start_new_round(self):
        """开始新游戏"""
        # 使用当前时间作为随机数生成器的种子，确保每次运行时生成的随机数序列不同
        random.seed(time.time())
        self.target_card = random.choice(self.total_cards)
        # 添加两张目标卡牌
        self.total_cards.extend([self.target_card, self.target_card])
        random.shuffle(self.total_cards)
        # 分发卡牌给每个玩家
        for i, player in enumerate(self.players):
            start_index = i * 5
            end_index = start_index + 5
            self.player_cards[player] = self.total_cards[start_index:end_index]

    def is_over(self):
        """检查游戏是否结束, user玩家出局或者产生最后一名玩家则结束"""
        alive_players = [player for player, status in self.player_status.items() if status["is_alive"]]
        for player, status in self.player_status.items():
            if status["style"] == "user":
                if not status["is_alive"]:
                    return True
        return len(alive_players) == 1

    def display_player_cards(self):
        """显示每个玩家的卡牌"""
        print(f"Target card: {self.target_card}")
        for player, cards in self.player_cards.items():
            print(f"{player} has cards: {cards}")

    def _eliminate_check(self, player):
        """检查玩家是否被淘汰"""
        select = random.randint(1, self.player_status[player]["elimination_factor"])
        return select == 1

    def get_winner(self):
        """检查是否有玩家胜利"""
        alive_players = [player for player, status in self.player_status.items() if status["is_alive"]]
        return alive_players[0]

    def _next_player(self, current_player):
        """下一个玩家出牌"""
        # 找到当前玩家在列表中的位置
        current_index = self.players.index(current_player)
        # 计算下一个玩家的索引，使用取余运算来循环遍历列表
        next_index = (current_index + 1) % len(self.players)
        while not self.player_status[self.players[next_index]]["is_alive"]:
            next_index = (next_index + 1) % len(self.players)
        # 返回下一个玩家
        return self.players[next_index]

    def play(self, action, cards=None, thought=None, dialog=None):
        """执行玩家动作"""
        self._add_to_current_round(action, cards, thought, dialog)
        # 正常出牌则轮到下一个玩家出牌
        if action == self.action_space[1]:
            self.challenge_info.clear()
            print(f"{self.current_player} challenges!")
            last_player_action = self.current_round[-2]
            last_player = last_player_action["player"]
            last_player_cards = last_player_action["cards"]
            self.challenge_info.append(f"{self.current_player}质疑{last_player}")
            # 质疑是否为目标牌
            all_target_cards = all(card == self.target_card for card in last_player_cards)
            self.challenge_info.append(
                f"{last_player}的出牌为: {','.join(last_player_cards)}, 本轮目标牌为: {self.target_card}")
            # 惩罚玩家
            punished_player = self.current_player if all_target_cards else last_player
            self.challenge_info.append(
                f"{self.current_player}质疑{'失败' if all_target_cards else '成功'}, {punished_player}将受到惩罚！")
            # 被惩罚玩家出牌
            self.current_player = punished_player
            if self._eliminate_check(punished_player):
                print(f"{punished_player} is eliminated!")
                self.player_status[punished_player]["is_alive"] = False
                # 出局则下一玩家出牌
                self.current_player = self._next_player(punished_player)
                self.challenge_info.append(f"{punished_player}不幸出局！")
            else:
                print(f"{punished_player} survives the challenge!")
                self.player_status[punished_player]["elimination_factor"] -= 1
                self.challenge_info.append(f"{punished_player}侥幸逃过一劫，游戏继续！")
                self.challenge_info.append(f"{punished_player}请继续出牌！")

            # 结束当前轮次
            self.turn_new_round()
            return all_target_cards, last_player_cards, punished_player, self.player_status[punished_player]["is_alive"]
        else:
            # 更新手里的牌
            self.update_current_player_cards(cards)
            self.current_player = self._next_player(self.current_player)
            return None, None, None, None
