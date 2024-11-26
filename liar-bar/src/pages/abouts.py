# Copyright (c) 2024 King Jingxiang
# See the LICENSE file for license rights and limitations (MIT).
import streamlit as st


def about_page():
    # 设置页面配置
    st.set_page_config(page_title="关于我们", layout="wide")
    st.title("🌟 关于我们的项目 🌟")

    # 项目简介
    st.header("💡 项目简介 💡")
    st.write("""
    欢迎来到 **AI欺诈游戏** 项目！🚀 这是一个通过多智能体系统（Multi-Agent Systems, MAS）来模拟和参与欺诈游戏的案例。在这个游戏中，不同的AI角色扮演者会根据各自的策略来进行游戏，尝试欺骗对手并赢得比赛。每个角色都有其独特的性格特点和玩法，比如胆小鬼、占卜师、大胆赌徒、冷静分析者以及狡黠骗子。这些角色在游戏中彼此互动，创造了一个充满策略和心理战的环境。
    """)

    # 项目特色
    st.header("✨ 项目特色 ✨")
    st.write("""
    - **多智能体互动** 🤖：体验不同AI角色之间的策略博弈。
    - **动态游戏环境** 🔄：每局游戏都是独一无二的，增加了游戏的可玩性和挑战性。
    - **角色多样性** 🎭：每个角色都有独特的性格和策略，为游戏增添了丰富的层次感。
    - **开放源代码** 📚：项目完全开源，欢迎社区贡献和改进。
    """)

    # 项目状态
    st.header("🛠️ 项目状态 🛠️")
    st.write("""
    目前，该项目还在持续开发和完善中。我们已经实现了基本的游戏框架和多个角色的逻辑，但仍然有一些功能需要进一步完善，例如：
    - 更复杂的AI决策机制
    - 用户界面的优化
    - 游戏规则的扩展
    我们非常欢迎大家提出宝贵的意见和建议，一起让这个游戏变得更加有趣和完善！
    """)

    # 如何参与
    st.header("🤝 如何参与 🤝")
    st.write("""
    如果您对这个项目感兴趣，或者有任何想法和建议，请随时访问我们的GitHub仓库，并在Issues板块提交您的反馈。我们非常期待与您一起合作，共同推进这个项目的进展！

    [GitHub Repository](https://github.com/king-jingxiang/ai-liar-games)
    """)


if __name__ == "__main__":
    about_page()
