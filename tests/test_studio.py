from pytest import approx, raises

from studio import (
    INK,
    TYPE_RATIOS,
    best_on_ink,
    closest_pair,
    contrast_ratio,
    css_variables,
    delta_e76,
    hex_to_hsl,
    json_tokens,
    lab_query,
    mix_hex,
    palette_from_seed,
    pairing_table,
    passes_aa,
    passes_aaa,
    recommend_body,
    scss_map,
    shade,
    tailwind_theme,
    tint,
    type_scale,
)


def test_palette_from_seed_is_deterministic_and_hex():
    first = palette_from_seed("asteria")
    second = palette_from_seed("asteria")
    other = palette_from_seed("northline")

    assert first == second
    assert first != other
    assert len(first) == 5
    for color in first:
        assert color.startswith("#")
        assert len(color) == 7
        int(color[1:], 16)


def test_palette_from_seed_snapshot():
    assert palette_from_seed("asteria") == [
        "#66381f",
        "#a76538",
        "#a9be5c",
        "#83d1db",
        "#a4b0d9",
    ]


def test_contrast_ratio_wcag_extremes():
    assert contrast_ratio("#ffffff", "#000000") == approx(21.0)
    assert contrast_ratio("#000", "#fff") == approx(21.0)
    assert contrast_ratio("#101418", "#101418") == approx(1.0)


def test_contrast_ratio_rejects_invalid_hex():
    with raises(ValueError):
        contrast_ratio("blue", "#000000")


def test_passes_aa_thresholds():
    assert passes_aa("#ffffff", "#000000") is True
    assert passes_aa("#888888", "#ffffff") is False
    assert passes_aa("#888888", "#ffffff", large=True) is True
    assert passes_aa("#999999", "#ffffff", large=True) is False


def test_passes_aaa_thresholds():
    assert passes_aaa("#ffffff", "#000000") is True
    assert passes_aaa("#ffffff", "#000000", large=True) is True
    assert passes_aaa("#888888", "#ffffff") is False
    assert passes_aaa("#888888", "#ffffff", large=True) is False
    assert passes_aaa("#595959", "#ffffff") is True
    assert passes_aaa("#777777", "#ffffff", large=True) is False
    assert passes_aaa("#767676", "#ffffff", large=True) is True
    assert passes_aaa("#767676", "#ffffff") is False


def test_css_variables_snapshot():
    css = css_variables(palette_from_seed("asteria"))
    assert css.splitlines()[0] == (
        ":root { --studio-1: #66381f; --studio-2: #a76538; "
        "--studio-3: #a9be5c; --studio-4: #83d1db; --studio-5: #a4b0d9; "
        "--studio-ink: #101418; }"
    )


def test_scss_map_snapshot():
    assert scss_map(palette_from_seed("asteria")) == (
        '$studio: ("1": #66381f, "2": #a76538, "3": #a9be5c, '
        '"4": #83d1db, "5": #a4b0d9, "ink": #101418);'
    )


def test_best_on_ink_asteria():
    palette = palette_from_seed("asteria")
    best = best_on_ink(palette)
    assert best["hex"] == "#83d1db"
    assert best["ratio"] == approx(contrast_ratio("#83d1db", INK))
    assert best["aa"] is True
    assert best["aaa"] is True
    assert set(best) == {"hex", "ratio", "aa", "aaa"}


def test_best_on_ink_tie_keeps_first():
    tied = ["#c8c8c8", "#c8c8c8"]
    best = best_on_ink(tied)
    assert best["hex"] == "#c8c8c8"
    lighter = best_on_ink(["#444444", "#f2f2f2", "#e8e8e8"])
    assert lighter["hex"] == "#f2f2f2"


def test_recommend_body_asteria_has_no_aa_pair():
    assert recommend_body(palette_from_seed("asteria")) is None


def test_recommend_body_first_consecutive_aa_pair():
    palette = ["#111111", "#222222", "#f7f7f7", "#eeeeee"]
    recommended = recommend_body(palette)
    assert recommended is not None
    assert recommended["fg"] == "#222222"
    assert recommended["bg"] == "#f7f7f7"
    assert recommended["aa"] is True
    assert recommended["aaa"] is passes_aaa("#222222", "#f7f7f7")
    assert recommended["ratio"] == approx(contrast_ratio("#222222", "#f7f7f7"))


def test_pairing_table_ink_and_neighbors():
    palette = palette_from_seed("asteria")
    rows = pairing_table(palette)
    assert len(rows) == 9
    for row in rows:
        assert set(row) == {"fg", "bg", "ratio", "aa", "aaa"}
        assert row["ratio"] == approx(contrast_ratio(row["fg"], row["bg"]))
        assert row["aa"] is passes_aa(row["fg"], row["bg"])
        assert row["aaa"] is passes_aaa(row["fg"], row["bg"])
    for index, color in enumerate(palette):
        assert rows[index]["fg"] == color
        assert rows[index]["bg"] == INK
    for index in range(len(palette) - 1):
        neighbor = rows[len(palette) + index]
        assert neighbor["fg"] == palette[index]
        assert neighbor["bg"] == palette[index + 1]


def test_type_ratios():
    assert TYPE_RATIOS == {
        "minor-third": 1.2,
        "major-third": 1.25,
        "perfect-fourth": 1.333,
        "perfect-fifth": 1.5,
    }


def test_type_scale_major_third():
    assert type_scale() == [16.0, 20.0, 25.0, 31.25, 39.06, 48.83]
    assert type_scale(base_px=18, ratio=1.2, steps=3) == [18.0, 21.6, 25.92]


def test_type_scale_rejects_empty():
    with raises(ValueError):
        type_scale(steps=0)


def test_mix_hex_midpoint_rounds_like_hsl():
    # Linear sRGB 0..1; channels use floor(x * 255 + 0.5) like _hsl_to_hex.
    # 0.5 * 255 = 127.5 → 128 → #808080, not truncated #7f7f7f.
    assert mix_hex("#000000", "#ffffff", 0.5) == "#808080"
    assert mix_hex("#000", "#fff", 0.5) == "#808080"
    assert mix_hex("#ffffff", "#000000", 0.5) == "#808080"
    assert mix_hex("#ff0000", "#0000ff", 0) == "#ff0000"
    assert mix_hex("#ff0000", "#0000ff", 1) == "#0000ff"
    assert mix_hex("#000000", "#ffffff", -1) == "#000000"
    assert mix_hex("#000000", "#ffffff", 2) == "#ffffff"


def test_shade_and_tint_extremes():
    assert shade("#ffffff", 1) == "#000000"
    assert tint("#000000", 1) == "#ffffff"
    assert shade("#ffffff", 0) == "#ffffff"
    assert tint("#000000", 0) == "#000000"
    assert shade("#ffffff") == mix_hex("#ffffff", "#000000", 0.15)
    assert tint("#000000") == mix_hex("#000000", "#ffffff", 0.15)


def test_lab_query_quote_plus():
    assert lab_query("asteria") == "seed=asteria&ratio=major-third"
    assert lab_query("asteria", "perfect-fifth") == "seed=asteria&ratio=perfect-fifth"
    assert lab_query("hello world", "major-third") == "seed=hello+world&ratio=major-third"
    assert lab_query("a&b") == "seed=a%26b&ratio=major-third"


def test_hex_to_hsl_primaries_and_gray():
    assert hex_to_hsl("#000000") == {"h": 0, "s": 0, "l": 0}
    assert hex_to_hsl("#ffffff") == {"h": 0, "s": 0, "l": 100}
    assert hex_to_hsl("#ff0000") == {"h": 0, "s": 100, "l": 50}
    assert hex_to_hsl("#00ff00") == {"h": 120, "s": 100, "l": 50}
    assert hex_to_hsl("#0000ff") == {"h": 240, "s": 100, "l": 50}
    assert hex_to_hsl("#808080") == {"h": 0, "s": 0, "l": 50}
    assert hex_to_hsl("#000") == {"h": 0, "s": 0, "l": 0}


def test_delta_e76_black_white_and_identical():
    assert delta_e76("#000000", "#000000") == approx(0.0)
    assert delta_e76("#ffffff", "#ffffff") == approx(0.0)
    assert delta_e76("#000000", "#ffffff") == approx(100.0, abs=0.05)
    assert delta_e76("#ffffff", "#000000") == approx(delta_e76("#000000", "#ffffff"))
    assert delta_e76("#ff0000", "#00ff00") > 50


def test_closest_pair_scan_order_and_none():
    assert closest_pair([]) is None
    assert closest_pair(["#ff0000"]) is None
    tied = closest_pair(["#111111", "#222222", "#111111"])
    assert tied is not None
    assert tied["i"] == 0
    assert tied["j"] == 2
    assert tied["a"] == "#111111"
    assert tied["b"] == "#111111"
    assert tied["delta_e"] == approx(0.0)
    assert set(tied) == {"a", "b", "i", "j", "delta_e"}


def test_closest_pair_asteria_is_min_delta():
    palette = palette_from_seed("asteria")
    pair = closest_pair(palette)
    assert pair is not None
    assert pair["delta_e"] == approx(delta_e76(pair["a"], pair["b"]))
    for i in range(len(palette)):
        for j in range(i + 1, len(palette)):
            assert pair["delta_e"] <= delta_e76(palette[i], palette[j]) + 1e-12
    assert pair["i"] < pair["j"]
    assert pair["a"] == palette[pair["i"]]
    assert pair["b"] == palette[pair["j"]]


def test_json_tokens_and_tailwind_asteria():
    palette = palette_from_seed("asteria")
    assert json_tokens(palette) == (
        '{"ink":"#101418","studio":{"1":"#66381f","2":"#a76538",'
        '"3":"#a9be5c","4":"#83d1db","5":"#a4b0d9"}}'
    )
    assert tailwind_theme(palette) == (
        "theme: { extend: { colors: { studio: { "
        "1: '#66381f', 2: '#a76538', 3: '#a9be5c', "
        "4: '#83d1db', 5: '#a4b0d9', ink: '#101418' "
        "} } } }"
    )
    assert json_tokens([]) == '{"ink":"#101418","studio":{}}'
