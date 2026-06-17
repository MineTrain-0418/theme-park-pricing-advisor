import os

import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MOCK_RESPONSE = """
### 1. 現状の収益ポジション評価
現在のチケット価格は業界水準と比較して標準的な範囲内にあります。混雑度が高く繁忙期であることから、需要は旺盛で値上げ余地があると判断されます。

### 2. 価格最適化の提案
繁忙期の混雑度（7/10）を考慮すると、10〜15%の値上げ（約1,000〜1,500円）が現実的な選択肢です。ダイナミックプライシングの導入により、混雑ピーク時に最大20%のプレミアム価格を設定することを推奨します。

### 3. リスクとトレードオフの分析
値上げにより一部の価格感応度の高い来場者が離れる可能性がありますが、繁忙期においては需要の弾力性が低く、来場者数への影響は軽微と予想されます。ブランドイメージへの影響を最小化するため、値上げと同時にサービス品質の向上を訴求することが重要です。

### 4. 経営者向け一言サマリー
繁忙期の高混雑という好条件を活かし、段階的な値上げとダイナミックプライシングの導入を優先してください。まず5〜10%の価格調整から始め、来場者反応を見ながら最適価格を探ることが収益最大化への最短経路です。
""".strip()


def build_prompt(inputs: dict) -> str:
    dp_status = "導入済み" if inputs["dynamic_pricing"] == "はい" else "未導入"

    return f"""あなたはテーマパークの価格戦略コンサルタントです。
以下の経営データをもとに、収益最大化の観点から詳細な価格戦略アドバイスを日本語で提供してください。

## 入力データ
- パーク種別: {inputs["park_type"]}
- 現在のチケット価格: {inputs["ticket_price"]:,}円
- 想定混雑度: {inputs["congestion"]} / 10
- 年間来場者数: {inputs["visitors"]}万人
- 時期: {inputs["season"]}
- ダイナミックプライシング: {dp_status}

## 出力形式
以下の4項目について、それぞれ具体的かつ実践的なアドバイスを提供してください。

### 1. 現状の収益ポジション評価
業界水準や競合と比較した現状分析を記述してください。

### 2. 価格最適化の提案
値上げ・値下げ・ダイナミック化など、具体的な価格施策を提案してください。
可能であれば具体的な価格帯の目安も含めてください。

### 3. リスクとトレードオフの分析
提案する施策のリスク、来場者数への影響、ブランドへの影響などを分析してください。

### 4. 経営者向け一言サマリー
最も重要なアクションを一言（2〜3文）でまとめてください。"""


def main():
    st.set_page_config(
        page_title="テーマパーク価格戦略シミュレーター",
        page_icon="🎢",
        layout="centered",
    )

    st.title("🎢 テーマパーク価格戦略シミュレーター")
    st.caption("経営データを入力するとAIが価格戦略アドバイスを提供します。")

    with st.form("input_form"):
        st.subheader("パラメータ入力")

        park_type = st.selectbox(
            "1. パーク種別",
            ["ディズニー系", "USJ系", "その他"],
        )

        ticket_price = st.number_input(
            "2. 現在のチケット価格（円）",
            min_value=1,
            max_value=100_000,
            value=9_000,
            step=100,
        )

        congestion = st.slider(
            "3. 想定混雑度（1=空いている / 10=超混雑）",
            min_value=1,
            max_value=10,
            value=5,
        )

        visitors = st.number_input(
            "4. 年間来場者数（万人）",
            min_value=0.1,
            max_value=10_000.0,
            value=100.0,
            step=1.0,
            format="%.1f",
        )

        season = st.radio(
            "5. 時期",
            ["繁忙期", "閑散期"],
            horizontal=True,
        )

        dynamic_pricing = st.radio(
            "6. ダイナミックプライシング導入済み？",
            ["いいえ", "はい"],
            horizontal=True,
        )

        mock_mode = st.checkbox(
            "モックモード（APIを使わずサンプル回答を表示）",
            value=False,
        )

        submitted = st.form_submit_button("アドバイスを生成", type="primary", use_container_width=True)

    if submitted:
        inputs = {
            "park_type": park_type,
            "ticket_price": int(ticket_price),
            "congestion": congestion,
            "visitors": visitors,
            "season": season,
            "dynamic_pricing": dynamic_pricing,
        }

        st.divider()
        st.subheader("価格戦略アドバイス")

        with st.spinner("分析中です。しばらくお待ちください..."):
            if mock_mode:
                st.info("モックモードで表示しています。")
                st.markdown(MOCK_RESPONSE)
            else:
                try:
                    prompt = build_prompt(inputs)

                    def stream_response():
                        for chunk in client.models.generate_content_stream(
                            model="gemini-2.5-flash",
                            contents=prompt,
                        ):
                            if chunk.text:
                                yield chunk.text

                    st.write_stream(stream_response())
                except Exception as e:
                    st.error(f"APIエラーが発生しました: {e}")


if __name__ == "__main__":
    main()
