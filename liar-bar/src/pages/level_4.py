import os
import random
import time

import agentscope
import streamlit as st
from game.game import Game


def display_player_status(player, game):
    """显示指定玩家的状态信息"""
    st.markdown(f"## {player}")
    if game.current_player == player:
        st.markdown('<h1 style="color:red;font-size:30px;">现在轮到你出牌！</h1>', unsafe_allow_html=True)
    if not game.player_status[player]["is_alive"]:
        st.write("你已经出局")
    else:
        st.write(f"本轮的目标牌为: {game.target_card}!")
        st.write(f"现在手枪里还有{game.player_status[player]['elimination_factor']}/5发子弹")
        if game.player_status[player]["style"] == "user":
            st.write(f"你手里牌分别为: [{', '.join(game.player_cards[player])}]")
        else:
            st.write(f"你现在手里有 {len(game.player_cards[player])} 张牌")
            st.write(f"你现在的扮演的角色为: ？？？")
            if game.current_player == player:
                st.markdown('<h3 style="color:blue;font-size:30px;">智能体思考中……</h3>', unsafe_allow_html=True)
        # 显示最近一次出牌情况
        for play in reversed(game.current_round):
            if play["player"] == player:
                st.write(f'<h3 style="color:green;font-size:30px;">刚刚你打出了{len(play['cards'])}张目标牌</h3>',
                         unsafe_allow_html=True)
                break  # 只显示最后一次
    st.write("---")


def init_model(api_key):
    # 初始化模型配置
    model_configs = [
        {
            "model_type": "openai_chat",
            "client_args": {
                "base_url": "https://aistudio.baidu.com/llm/lmapi/v3",
            },
            "config_name": "aistudio",
            "model_name": "ernie-4.0-8k",
            "api_key": os.environ.get("AI_STUDIO_API_KEY", api_key),
            "generate_args": {"temperature": 0.2},
            "max_tokens": 8192,
            "messages_key": "input",
            "stream": True,
        }
    ]
    agentscope.init(model_configs=model_configs, logger_level="TRACE")


# 定义主函数
def main():
    # 初始化游戏
    if "game" not in st.session_state:
        st.session_state["game"] = Game()
        st.session_state["game_started"] = False  # 标记游戏是否开始

    game = st.session_state["game"]

    # Streamlit应用
    st.set_page_config(page_title="Card Game Interface", layout="wide")
    st.title("🎴 卡牌游戏界面")
    st.write(
        "这一关将不会标记每个智能体所扮演的角色，也不会把智能体思考的过程公开，并且会随机选择智能体！本局游戏你作为Player2，请尽情玩耍吧！！！")
    st.write('tips: 有时候可能会卡住没有刷新最新的结果，请点击"点我刷新"按钮手动刷新')
    with st.sidebar:
        api_key = st.text_input("AIStudio API Key", key="chatbot_api_key", type="password")
        "[Get an AIStudio API key](https://aistudio.baidu.com/account/accessToken)"
        "[View the source code](https://github.com/king-jingxiang/ai-liar-games)"

    # 创建两列布局
    col1, col2 = st.columns([1, 2])  # 左窄右宽

    # 左侧：出牌记录和角色对话
    with col1:
        st.subheader("📝 出牌记录和角色对话")
        st.markdown("**出牌记录**")
        st.markdown(game.get_game_logs(debug=False), unsafe_allow_html=True)
        st.markdown("**质疑信息**")
        st.markdown(game.get_challenge_info(), unsafe_allow_html=True)

    # 右侧：每个角色的牌以2×2布局展示
    with col2:
        st.subheader("🎮 当前出牌情况")
        start_button = st.button("开始游戏")
        refresh_button = st.button("点我刷新")
        if start_button:
            if not os.environ.get("AI_STUDIO_API_KEY", api_key):
                st.error("请填写您的API Key")
                return
            init_model(api_key)
            game.initialize_agents()
            random.seed(time.time())
            game.initialize_players([random.choice(game.agents)["name"], "user",
                                     random.choice(game.agents)["name"], random.choice(game.agents)["name"]])
            st.session_state["game_started"] = True
            game.start_new_round()  # 点击开始按钮后，启动游戏

        grid_columns = st.columns(2)  # 分为两列
        for i, player in enumerate(game.players):
            with grid_columns[i % 2]:  # 在两列中交替显示
                if st.session_state["game_started"]:  # 游戏开始后显示信息
                    display_player_status(player, game)

        # 用户输入框（仅当当前玩家是用户时显示）
        st.subheader("🚀 你的行动")
        user_input = st.text_input("请输入您的出牌指令（例如：直接出牌: A K Q/提出质疑: challenge）", key="user_action")
        if st.button("提交"):
            if not game.current_player_is_user():
                st.warning("现在还没轮到你出牌！")
            else:
                if user_input.strip():
                    try:
                        if user_input.strip().startswith(game.action_space[1]):
                            game.play(game.action_space[1], None)
                        else:
                            cards = user_input.strip().split()
                            if game.check_played_cards(cards):
                                game.play(game.action_space[0], cards)
                            else:
                                st.warning("出牌无效，请重新输入！")
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"输入无效：{e}")
                else:
                    st.warning("请先输入有效指令！")

    # 游戏循环
    while st.session_state["game_started"] and not game.is_over():
        if game.current_player_is_user():
            break  # 等待用户输入
        else:
            game.display_player_cards()
            action, cards, thought, dialog = game.player_think()
            if action == game.action_space[1]:
                game.play(action, cards, thought, dialog)
                time.sleep(5)
            else:
                game.play(action, cards, thought, dialog)
            st.experimental_rerun()

    # 游戏结束
    if st.session_state["game_started"] and game.is_over():
        winner = game.get_winner()
        st.success(f"🏆 游戏结束！{winner} 获胜！")


# 启动主函数
if __name__ == "__main__":
    main()
