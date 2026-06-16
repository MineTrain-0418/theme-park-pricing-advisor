import anthropic
import sys


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


def ask(prompt: str, valid_options: list[str] | None = None) -> str:
    while True:
        value = input(prompt).strip()
        if not value:
            print("  入力してください。")
            continue
        if valid_options and value not in valid_options:
            print(f"  次のいずれかを入力してください: {' / '.join(valid_options)}")
            continue
        return value


def ask_int(prompt: str, min_val: int, max_val: int) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if min_val <= value <= max_val:
                return value
            print(f"  {min_val}〜{max_val} の整数を入力してください。")
        except ValueError:
            print("  整数を入力してください。")


def collect_inputs() -> dict:
    print("\n" + "=" * 60)
    print("  テーマパーク価格戦略シミュレーター")
    print("=" * 60)
    print("以下の項目を順に入力してください。\n")

    park_type = ask(
        "1. パーク種別を選んでください (ディズニー系 / USJ系 / その他): ",
        ["ディズニー系", "USJ系", "その他"],
    )

    ticket_price_str = ask("2. 現在のチケット価格（円）を入力してください: ")
    while True:
        try:
            ticket_price = int(ticket_price_str.replace(",", "").replace("，", ""))
            if ticket_price > 0:
                break
            print("  正の整数を入力してください。")
        except ValueError:
            print("  半角数字で入力してください。")
        ticket_price_str = input("2. 現在のチケット価格（円）を入力してください: ").strip()

    congestion = ask_int(
        "3. 想定混雑度を1〜10で入力してください (1=空いている, 10=超混雑): ", 1, 10
    )

    visitors_str = ask("4. 年間来場者数（万人）を入力してください: ")
    while True:
        try:
            visitors = float(visitors_str.replace(",", "").replace("，", ""))
            if visitors > 0:
                break
            print("  正の数を入力してください。")
        except ValueError:
            print("  数値で入力してください。")
        visitors_str = input("4. 年間来場者数（万人）を入力してください: ").strip()

    season = ask(
        "5. 時期を選んでください (繁忙期 / 閑散期): ",
        ["繁忙期", "閑散期"],
    )

    dynamic_pricing = ask(
        "6. ダイナミックプライシング導入済みですか？ (はい / いいえ): ",
        ["はい", "いいえ"],
    )

    return {
        "park_type": park_type,
        "ticket_price": ticket_price,
        "congestion": congestion,
        "visitors": visitors,
        "season": season,
        "dynamic_pricing": dynamic_pricing,
    }


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
    mock_mode = "--mock" in sys.argv

    inputs = collect_inputs()

    print("\n分析中です。しばらくお待ちください...\n")
    print("=" * 60)
    print("  価格戦略アドバイス")
    print("=" * 60 + "\n")

    if mock_mode:
        for char in MOCK_RESPONSE:
            print(char, end="", flush=True)
    else:
        client = anthropic.Anthropic()
        prompt = build_prompt(inputs)

        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)

    print("\n\n" + "=" * 60)
    print("  分析完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
