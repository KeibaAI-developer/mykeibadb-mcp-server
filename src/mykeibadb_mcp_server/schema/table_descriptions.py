"""テーブル・カラム説明辞書。63テーブルの説明とエンコーディング情報を含む。"""

from typing import Any

TABLE_DESCRIPTIONS: dict[str, dict[str, Any]] = {
    "RACE_SHOSAI": {
        "description": "レース詳細。レース名・距離・グレード・馬場状態等を含む。",
        "primary_key": "RACE_CODE",
        "date_column": {"year": "KAISAI_NEN", "monthday": "KAISAI_GAPPI"},
        "column_notes": {
            "RACE_CODE": "レースコード。12桁文字列（yyyykksrr: 年・場・回・日・R）。",
            "KAISAI_NEN": "開催年。4桁文字列（例: '2025'）。",
            "KAISAI_GAPPI": "開催月日。4桁文字列 mmdd形式（例: '0531'=5月31日）。",
            "KYORI": "距離（メートル）。整数文字列（例: '2000'=2000m）。",
            "GRADE_CODE": "グレードコード。'A'=GI, 'B'=GII, 'C'=GIII, 'D'=重賞, 'E'=特別競走, '_'=一般競走。",
            "TRACK_CODE": "トラックコード。'11'=芝・左, '23'=ダート・左 等。",
            "TENKO_CODE": "天候コード。'1'=晴, '2'=曇, '3'=雨, '4'=小雨, '5'=雪, '6'=小雪。",
            "BABAJOTAI_SHIBA": "芝馬場状態コード。'1'=良, '2'=稍重, '3'=重, '4'=不良。",
            "BABAJOTAI_DIRT": "ダート馬場状態コード。'1'=良, '2'=稍重, '3'=重, '4'=不良。",
            "HASSO_JIKOKU": "発走時刻。4桁文字列 HHMM形式（例: '1540'=15:40）。",
        },
    },
    "UMAGOTO_RACE_JOHO": {
        "description": "馬毎レース情報。出走馬ごとの着順・タイム・騎手・人気等。",
        "primary_key": ["RACE_CODE", "UMABAN"],
        "date_column": {"year": "KAISAI_NEN", "monthday": "KAISAI_GAPPI"},
        "column_notes": {
            "RACE_CODE": "レースコード。RACE_SHOSAIと結合キー。",
            "UMABAN": "馬番。2桁文字列ゼロ埋め（例: '01'=1番）。",
            "KAKUTEI_CHAKUJUN": (
                "確定着順。2桁文字列ゼロ埋め（例: '01'=1着）。"
                "失格・降着時は入線順位と異なる。0=出走取消・除外。"
            ),
            "KAISAI_NEN": "開催年。4桁文字列（例: '2025'）。",
            "KAISAI_GAPPI": "開催月日。4桁文字列 mmdd形式（例: '0531'=5月31日）。",
            "KETTO_TOROKU_BANGO": "血統登録番号。10桁文字列。先頭4桁が生年（例: '2022105081'→生年2022）。",
            "SOHA_TIME": (
                "走破タイム。4桁文字列 MSSS形式（例: '2315'=2分31秒5）。"
                "'0000'=未計測（NaN相当）。SQL例: time_to_seconds('2315')=151.5秒。"
            ),
            "KOHAN_3F": "後3ハロンタイム。3桁整数文字列、単位は0.1秒（例: '355'=35.5秒）。'999'=中止等。",
            "TANSHO_ODDS": "単勝オッズ。3桁整数文字列、単位は0.1倍（例: '152'=15.2倍）。",
            "TANSHO_NINKIJUN": "単勝人気順位。2桁文字列ゼロ埋め（例: '01'=1番人気）。",
            "FUTAN_JURYO": "負担重量。3桁整数、単位は0.1kg（例: '560'=56.0kg）。",
            "BATAIJU": "馬体重（kg）。3桁整数。'000'=未計測。",
            "ZOGEN_SA": "馬体重増減差。3桁整数（符号付き文字列）。'999'=計測不能。",
            "KYAKUSHITSU_HANTEI": "脚質判定。'1'=逃, '2'=先, '3'=差, '4'=追。",
        },
    },
    "WOODCHIP_CHOKYO": {
        "description": "ウッドチップ調教データ。美浦・栗東のウッドチップコースでの調教タイムを含む。",
        "primary_key": ["TRACEN_KUBUN", "CHOKYO_NENGAPPI", "CHOKYO_JIKOKU", "KETTO_TOROKU_BANGO"],
        "date_column": {"yyyymmdd": "CHOKYO_NENGAPPI"},
        "column_notes": {
            "TRACEN_KUBUN": "トレセン区分。'0'=美浦、'1'=栗東。",
            "CHOKYO_NENGAPPI": "調教年月日。8桁文字列 yyyymmdd形式。",
            "CHOKYO_JIKOKU": "調教時刻。4桁文字列 HHMM形式。",
            "KETTO_TOROKU_BANGO": "血統登録番号。UMAGOTO_RACE_JOHOと同じキーで馬を特定できる。",
            "TIME_GOKEI_6FURLONG": (
                "6ハロン(1200M→0M)の合計タイム。"
                "4桁文字列、単位は0.1秒（例: '0825'=82.5秒）。"
                "測定不良='0000'、99.9秒超='9999'。SQLでは CAST(... AS INTEGER) <= 825 のように比較。"
            ),
            "TIME_GOKEI_5FURLONG": (
                "5ハロン(1000M→0M)の合計タイム。"
                "4桁文字列、単位は0.1秒（例: '0668'=66.8秒）。"
                "測定不良='0000'、9999=99.9秒超。"
            ),
            "TIME_GOKEI_4FURLONG": (
                "4ハロン(800M→0M)の合計タイム。"
                "4桁文字列、単位は0.1秒（例: '0524'=52.4秒）。"
                "測定不良='0000'。"
            ),
            "LAPTIME_1FURLONG": (
                "ラスト1ハロン(200M→0M)のラップタイム。"
                "3桁文字列、単位は0.1秒（例: '115'=11.5秒）。"
                "測定不良='000'。SQLでは CAST(... AS INTEGER) <= 115 のように比較。"
            ),
            "LAPTIME_2FURLONG": "ラップタイム(400M→200M)。3桁文字列、単位は0.1秒。測定不良='000'。",
            "LAPTIME_3FURLONG": "ラップタイム(600M→400M)。3桁文字列、単位は0.1秒。測定不良='000'。",
        },
    },
    "HANRO_CHOKYO": {
        "description": "坂路調教データ。美浦・栗東の坂路コースでの調教タイムを含む。",
        "primary_key": ["TRACEN_KUBUN", "CHOKYO_NENGAPPI", "CHOKYO_JIKOKU", "KETTO_TOROKU_BANGO"],
        "date_column": {"yyyymmdd": "CHOKYO_NENGAPPI"},
        "column_notes": {
            "TRACEN_KUBUN": "トレセン区分。'0'=美浦、'1'=栗東。",
            "CHOKYO_NENGAPPI": "調教年月日。8桁文字列 yyyymmdd形式。",
            "CHOKYO_JIKOKU": "調教時刻。4桁文字列 HHMM形式。",
            "KETTO_TOROKU_BANGO": "血統登録番号。UMAGOTO_RACE_JOHOと同じキーで馬を特定できる。",
            "TIME_GOKEI_4FURLONG": (
                "4ハロン(800M→0M)の合計タイム。4桁文字列、単位は0.1秒。"
                "測定不良='0000'。SQLでは CAST(... AS INTEGER) <= 525 のように比較。"
            ),
            "LAP_TIME_1FURLONG": "ラスト1ハロンのラップタイム。3桁文字列、単位は0.1秒。測定不良='000'。",
            "LAP_TIME_2FURLONG": "ラップタイム(400M→200M)。3桁文字列、単位は0.1秒。測定不良='000'。",
            "LAP_TIME_3FURLONG": "ラップタイム(600M→400M)。3桁文字列、単位は0.1秒。測定不良='000'。",
            "LAP_TIME_4FURLONG": "ラップタイム(800M→600M)。3桁文字列、単位は0.1秒。測定不良='000'。",
        },
    },
    "BAMEI_IMI_YURAI": {
        "description": "馬名の意味・由来情報。馬名の読みと意味・由来テキストを含む。",
        "primary_key": "KETTO_TOROKU_BANGO",
        "date_column": {},
        "column_notes": {},
    },
    "BANUSHI_MASTER": {
        "description": "馬主マスタ。馬主コード・名称・勝負服カラーを含む。",
        "primary_key": "BANUSHI_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "BATAIJU": {
        "description": "馬体重。出走馬の計量時の体重と増減を管理するテーブル。",
        "primary_key": ["RACE_CODE", "UMABAN"],
        "date_column": {},
        "column_notes": {
            "BATAIJU": "馬体重（kg）。3桁整数。'000'=未計測。",
            "ZOGEN_SA": "馬体重増減差（前走比）。'999'=計測不能。",
            "ZOGEN_KUBUN": "増減区分。'+'=増加, '-'=減少, '='=同体重。",
        },
    },
    "CHOKYOSHI_MASTER": {
        "description": "調教師マスタ。調教師コード・名称・所属トレセン等を含む。",
        "primary_key": "CHOKYOSHI_CODE",
        "date_column": {},
        "column_notes": {
            "TRACEN_KUBUN": "所属トレセン。'0'=美浦、'1'=栗東。",
        },
    },
    "COURSE_HENKO": {
        "description": "コース変更情報。レース当日のコース変更（芝→ダート等）の記録。",
        "primary_key": "RACE_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "COURSE_JOHO": {
        "description": "コース情報。各競馬場・各コースの距離・形状・レコードタイム等。",
        "primary_key": ["KEIBAJO_CODE", "TRACK_CODE", "KYORI"],
        "date_column": {},
        "column_notes": {
            "RECORD_TIME": "コースレコードタイム。4桁文字列 MSSS形式。",
        },
    },
    "DATA_MINING_TAISEN": {
        "description": "データマイニング対戦情報。馬同士の対戦成績を集計したデータ。",
        "primary_key": ["KETTO_TOROKU_BANGO_1", "KETTO_TOROKU_BANGO_2"],
        "date_column": {},
        "column_notes": {},
    },
    "DATA_MINING_TIME": {
        "description": "データマイニングタイム情報。コース別の馬のタイム傾向データ。",
        "primary_key": ["KETTO_TOROKU_BANGO", "TRACK_CODE", "KYORI"],
        "date_column": {},
        "column_notes": {},
    },
    "HANSHOKUBA_MASTER2": {
        "description": "繁殖牝馬マスタ。繁殖牝馬の登録情報・血統等。",
        "primary_key": "KETTO_TOROKU_BANGO",
        "date_column": {},
        "column_notes": {},
    },
    "HARAIMODOSHI": {
        "description": "払戻情報。確定した各馬券種の払戻金額と的中組合せを含む。",
        "primary_key": "RACE_CODE",
        "date_column": {},
        "column_notes": {
            "TANSHO_HARAIMODOSHI_*": "単勝払戻金額。円単位整数。",
            "FUKUSHO_HARAIMODOSHI_*": "複勝払戻金額。円単位整数。",
        },
    },
    "HASSOJIKOKU_HENKO": {
        "description": "発走時刻変更情報。当初予定から変更になった発走時刻の記録。",
        "primary_key": "RACE_CODE",
        "date_column": {},
        "column_notes": {
            "HASSO_JIKOKU_AFTER": "変更後発走時刻。4桁文字列 HHMM形式。",
        },
    },
    "HYOSU1": {
        "description": "票数1（単勝・複勝・枠連・馬連・ワイド・馬単の各票数集計）。",
        "primary_key": "RACE_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "HYOSU1_FUKUSHO": {
        "description": "複勝票数。馬番ごとの複勝購入票数。",
        "primary_key": ["RACE_CODE", "UMABAN"],
        "date_column": {},
        "column_notes": {},
    },
    "HYOSU1_SANRENPUKU": {
        "description": "3連複票数。組み合わせごとの3連複購入票数。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2", "UMABAN_3"],
        "date_column": {},
        "column_notes": {},
    },
    "HYOSU1_TANSHO": {
        "description": "単勝票数。馬番ごとの単勝購入票数。",
        "primary_key": ["RACE_CODE", "UMABAN"],
        "date_column": {},
        "column_notes": {},
    },
    "HYOSU1_UMAREN": {
        "description": "馬連票数。組み合わせごとの馬連購入票数。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2"],
        "date_column": {},
        "column_notes": {},
    },
    "HYOSU1_UMATAN": {
        "description": "馬単票数。組み合わせごとの馬単購入票数。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2"],
        "date_column": {},
        "column_notes": {},
    },
    "HYOSU1_WAKUREN": {
        "description": "枠連票数。枠番組み合わせごとの枠連購入票数。",
        "primary_key": ["RACE_CODE", "WAKUBAN_1", "WAKUBAN_2"],
        "date_column": {},
        "column_notes": {},
    },
    "HYOSU1_WIDE": {
        "description": "ワイド票数。組み合わせごとのワイド購入票数。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2"],
        "date_column": {},
        "column_notes": {},
    },
    "HYOSU6": {
        "description": "票数6（3連単票数集計）。",
        "primary_key": "RACE_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "HYOSU6_SANRENTAN": {
        "description": "3連単票数。1・2・3着の組み合わせごとの3連単購入票数。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2", "UMABAN_3"],
        "date_column": {},
        "column_notes": {},
    },
    "KAISAI_SCHEDULE": {
        "description": "開催スケジュール。年間の競馬開催日程・場所・回次を含む。",
        "primary_key": ["KAISAI_NEN", "KEIBAJO_CODE", "KAISAI_KAI", "KAISAI_NICHI"],
        "date_column": {"year": "KAISAI_NEN"},
        "column_notes": {
            "KAISAI_NEN": "開催年。4桁文字列。",
            "KEIBAJO_CODE": "競馬場コード。'01'=札幌, '05'=東京, '06'=中山 等。",
        },
    },
    "KEITO_JOHO2": {
        "description": "血統系統情報。血統系統ID・系統名・説明を管理するマスタ。",
        "primary_key": "HANSHOKU_TOROKU_BANGO",
        "date_column": {},
        "column_notes": {
            "HANSHOKU_TOROKU_BANGO": "繁殖登録番号。",
            "KEITO_ID": "血統系統ID。",
            "KEITO_MEI": "血統系統名。",
            "KEITO_SETSUMEI": "血統系統の説明文。",
        },
    },
    "KISHU_HENKO": {
        "description": "騎手変更情報。出走馬の騎手が変更になった場合の記録。",
        "primary_key": ["RACE_CODE", "UMABAN"],
        "date_column": {},
        "column_notes": {},
    },
    "KISHU_MASTER": {
        "description": "騎手マスタ。騎手コード・名称・所属・見習い区分等。",
        "primary_key": "KISHU_CODE",
        "date_column": {},
        "column_notes": {
            "KISHU_MINARAI_CODE": "見習い区分。'0'=なし, '1'=2kg減, '2'=1kg減 等。",
            "TOZAI_SHOZOKU": "東西所属。'1'=東（美浦）, '2'=西（栗東）。",
        },
    },
    "KYOSOBA_JOGAI_JOHO": {
        "description": "競走馬除外情報。レース直前の除外・取消情報を含む。",
        "primary_key": ["RACE_CODE", "UMABAN"],
        "date_column": {},
        "column_notes": {},
    },
    "KYOSOBA_MASTER2": {
        "description": "競走馬マスタ2。競走馬の名前・生年・性別・毛色・血統登録番号等。",
        "primary_key": "KETTO_TOROKU_BANGO",
        "date_column": {},
        "column_notes": {
            "KETTO_TOROKU_BANGO": "血統登録番号。10桁文字列。先頭4桁が生年。",
            "BAMEI": "馬名（カタカナ）。",
            "SEIBETSU_CODE": "性別コード。'1'=牡, '2'=牝, '3'=セン。",
            "HINSHU_CODE": "品種コード。'1'=サラブレッド等。",
        },
    },
    "KYOSOBA_TORIHIKI_KAKAKU2": {
        "description": "競走馬取引価格2。セリ市・価格公開情報。",
        "primary_key": ["KETTO_TOROKU_BANGO", "TORIHIKI_NENGAPPI"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS1": {
        "description": "オッズ1（単勝・複勝・枠連・馬連・ワイド・馬単の確定オッズ集計）。",
        "primary_key": "RACE_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "ODDS1_FUKUSHO": {
        "description": "複勝確定オッズ。馬番ごとの複勝払戻倍率（上限・下限）。",
        "primary_key": ["RACE_CODE", "UMABAN"],
        "date_column": {},
        "column_notes": {
            "FUKUSHO_ODDS_MAX": "複勝オッズ上限。3桁整数文字列、単位は0.1倍。",
            "FUKUSHO_ODDS_MIN": "複勝オッズ下限。3桁整数文字列、単位は0.1倍。",
        },
    },
    "ODDS1_FUKUSHO_JIKEIRETSU": {
        "description": "複勝オッズ時系列。発走前の複勝オッズ変化を時系列で記録。",
        "primary_key": ["RACE_CODE", "UMABAN", "HAPPYO_JIKOKU"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS1_JIKEIRETSU": {
        "description": "オッズ時系列。発走前のオッズ変化を時系列で記録（単勝・複勝等）。",
        "primary_key": ["RACE_CODE", "HAPPYO_JIKOKU"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS1_TANSHO": {
        "description": "単勝確定オッズ。馬番ごとの単勝払戻倍率。",
        "primary_key": ["RACE_CODE", "UMABAN"],
        "date_column": {},
        "column_notes": {
            "TANSHO_ODDS": "単勝オッズ。3桁整数文字列、単位は0.1倍（例: '152'=15.2倍）。",
        },
    },
    "ODDS1_TANSHO_JIKEIRETSU": {
        "description": "単勝オッズ時系列。発走前の単勝オッズ変化を時系列で記録。",
        "primary_key": ["RACE_CODE", "UMABAN", "HAPPYO_JIKOKU"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS1_WAKUREN": {
        "description": "枠連確定オッズ。枠番組み合わせごとの枠連払戻倍率。",
        "primary_key": ["RACE_CODE", "WAKUBAN_1", "WAKUBAN_2"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS1_WAKUREN_JIKEIRETSU": {
        "description": "枠連オッズ時系列。発走前の枠連オッズ変化を時系列で記録。",
        "primary_key": ["RACE_CODE", "WAKUBAN_1", "WAKUBAN_2", "HAPPYO_JIKOKU"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS2_UMAREN": {
        "description": "馬連確定オッズ。馬番組み合わせごとの馬連払戻倍率。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS2_UMAREN_JIKEIRETSU": {
        "description": "馬連オッズ時系列。発走前の馬連オッズ変化を時系列で記録。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2", "HAPPYO_JIKOKU"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS3_WIDE": {
        "description": "ワイド確定オッズ。馬番組み合わせごとのワイド払戻倍率（上限・下限）。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS4_UMATAN": {
        "description": "馬単確定オッズ。1・2着の順序ありの組み合わせごとの馬単払戻倍率。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS5_SANRENPUKU": {
        "description": "3連複確定オッズ。3頭の組み合わせごとの3連複払戻倍率。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2", "UMABAN_3"],
        "date_column": {},
        "column_notes": {},
    },
    "ODDS6_SANRENTAN": {
        "description": "3連単確定オッズ。1・2・3着の順序ありの組み合わせごとの3連単払戻倍率。",
        "primary_key": ["RACE_CODE", "UMABAN_1", "UMABAN_2", "UMABAN_3"],
        "date_column": {},
        "column_notes": {},
    },
    "RECORD_MASTER": {
        "description": "レコードマスタ。各コースのコースレコード情報。",
        "primary_key": ["KEIBAJO_CODE", "TRACK_CODE", "KYORI"],
        "date_column": {},
        "column_notes": {
            "RECORD_TIME": "レコードタイム。4桁文字列 MSSS形式（例: '2315'=2:31.5）。",
        },
    },
    "SANKU_MASTER2": {
        "description": "産駒マスタ2。種牡馬の産駒成績集計情報。",
        "primary_key": "CHICHI_UMA_KETTO_TOROKU_BANGO",
        "date_column": {},
        "column_notes": {},
    },
    "SEISANSHA_MASTER2": {
        "description": "生産者マスタ2。生産者コード・名称・所在地等。",
        "primary_key": "SEISANSHA_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "SHOBUFUKU": {
        "description": "勝負服情報。馬主の勝負服の色・模様の定義。",
        "primary_key": "BANUSHI_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "SHUSSOBETSU_BABA": {
        "description": "出走別馬場成績。馬場状態ごとの累計成績（勝利数・出走数等）。",
        "primary_key": ["KETTO_TOROKU_BANGO", "BABAJOTAI_CODE"],
        "date_column": {},
        "column_notes": {},
    },
    "SHUSSOBETSU_BANUSHI": {
        "description": "出走別馬主成績。馬主ごとの累計成績（勝利数・出走数・収得賞金等）。",
        "primary_key": "BANUSHI_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "SHUSSOBETSU_CHOKYOSHI": {
        "description": "出走別調教師成績。調教師ごとの累計成績（勝利数・出走数等）。",
        "primary_key": "CHOKYOSHI_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "SHUSSOBETSU_KEIBAJO": {
        "description": "出走別競馬場成績。競馬場ごとの馬の累計成績。",
        "primary_key": ["KETTO_TOROKU_BANGO", "KEIBAJO_CODE"],
        "date_column": {},
        "column_notes": {},
    },
    "SHUSSOBETSU_KISHU": {
        "description": "出走別騎手成績。騎手ごとの累計成績（勝利数・出走数・勝率等）。",
        "primary_key": "KISHU_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "SHUSSOBETSU_KYORI": {
        "description": "出走別距離成績。距離ごとの馬の累計成績。",
        "primary_key": ["KETTO_TOROKU_BANGO", "KYORI"],
        "date_column": {},
        "column_notes": {},
    },
    "SHUSSOBETSU_SEISANSHA2": {
        "description": "出走別生産者成績2。生産者ごとの累計成績（勝利数・出走数等）。",
        "primary_key": "SEISANSHA_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "SHUSSOTORIKESHI_KYOSOJOGAI": {
        "description": "出走取消・競走除外情報。取消・除外の理由コードと対象馬情報。",
        "primary_key": ["RACE_CODE", "UMABAN"],
        "date_column": {},
        "column_notes": {},
    },
    "TENKO_BABA_JOTAI": {
        "description": "天候・馬場状態情報。レース当日の天候・馬場状態の変化を時系列で記録。",
        "primary_key": ["RACE_CODE", "HAPPYO_JIKOKU"],
        "date_column": {},
        "column_notes": {
            "TENKO_CODE": "天候コード。'1'=晴, '2'=曇, '3'=雨, '4'=小雨, '5'=雪, '6'=小雪。",
            "BABAJOTAI_SHIBA": "芝馬場状態コード。'1'=良, '2'=稍重, '3'=重, '4'=不良。",
            "BABAJOTAI_DIRT": "ダート馬場状態コード。'1'=良, '2'=稍重, '3'=重, '4'=不良。",
        },
    },
    "TOKUBETSU_TOROKUBA": {
        "description": "特別登録馬。特別競走への出走登録馬一覧。",
        "primary_key": ["RACE_CODE", "KETTO_TOROKU_BANGO"],
        "date_column": {},
        "column_notes": {},
    },
    "TOKUBETSU_TOROKUBAGOTO_JOHO": {
        "description": "特別登録馬ごとの情報。特別登録馬の詳細情報（騎手予定・予定斤量等）。",
        "primary_key": ["RACE_CODE", "KETTO_TOROKU_BANGO"],
        "date_column": {},
        "column_notes": {},
    },
    "WIN5": {
        "description": "WIN5情報。WIN5対象レースと結果情報。",
        "primary_key": "WIN5_CODE",
        "date_column": {},
        "column_notes": {},
    },
    "WIN5_HARAIMODOSHI": {
        "description": "WIN5払戻情報。WIN5の払戻金額と的中票数。",
        "primary_key": "WIN5_CODE",
        "date_column": {},
        "column_notes": {},
    },
}
