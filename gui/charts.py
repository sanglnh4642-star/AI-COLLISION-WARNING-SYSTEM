
"""
charts.py - Người 4: Trực quan hóa dữ liệu mô phỏng

Tương thích với dashboard.py:
    - render_all(df): biểu đồ dữ liệu theo thời gian.
    - scenario_comparison_chart(rows): so sánh các tình huống.

Thư viện sử dụng: pandas, streamlit.
Không cần cài thêm matplotlib hoặc plotly.
"""

import math

import pandas as pd
import streamlit as st


def _prepare_history(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa dữ liệu lịch sử trước khi vẽ biểu đồ."""
    if df is None or df.empty:
        return pd.DataFrame()

    data = df.copy()

    numeric_columns = [
        "t", "speed", "distance", "d_stop",
        "d_warning", "ttc"
    ]

    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column], errors="coerce"
            )

    if "t" in data.columns:
        data = data.sort_values("t")

    return data


def render_all(df: pd.DataFrame) -> None:
    """Hiển thị các biểu đồ dữ liệu mô phỏng."""

    data = _prepare_history(df)

    st.subheader("Biểu đồ diễn biến mô phỏng")

    if data.empty:
        st.info("Chưa có dữ liệu mô phỏng để hiển thị biểu đồ.")
        return

    if "t" in data.columns:
        chart_data = data.set_index("t")
        chart_data.index.name = "Thời gian (s)"
    else:
        chart_data = data.copy()
        chart_data.index.name = "Lần ghi nhận"

    # 1. Tốc độ và khoảng cách
    st.markdown("#### 1. Tốc độ và khoảng cách theo thời gian")

    available_columns = [
        column for column in ["speed", "distance"]
        if column in chart_data.columns
    ]

    if available_columns:
        st.line_chart(
            chart_data[available_columns],
            height=260,
            y_label="Giá trị"
        )
        st.caption(
            "Tốc độ được tính bằng km/h, "
            "khoảng cách được tính bằng mét."
        )
    else:
        st.caption("Không có dữ liệu tốc độ hoặc khoảng cách.")

    # 2. TTC
    st.markdown("#### 2. Thời gian còn lại trước va chạm (TTC)")

    if "ttc" in chart_data.columns:
        ttc_data = chart_data[["ttc"]].copy()

        ttc_data["ttc"] = ttc_data["ttc"].replace(
            [float("inf"), float("-inf")], float("nan")
        )

        ttc_data = ttc_data.dropna()

        if not ttc_data.empty:
            st.line_chart(
                ttc_data,
                height=220,
                y_label="TTC (giây)"
            )
            st.caption(
                "TTC càng thấp thì nguy cơ va chạm càng gần."
            )
        else:
            st.caption("Chưa có giá trị TTC hữu hạn để vẽ.")
    else:
        st.caption("Không có cột TTC trong dữ liệu.")

    # 3. Quãng đường dừng và ngưỡng cảnh báo
    st.markdown("#### 3. Quãng đường dừng và ngưỡng cảnh báo")

    distance_columns = [
        column for column in ["d_stop", "d_warning"]
        if column in chart_data.columns
    ]

    if distance_columns:
        st.line_chart(
            chart_data[distance_columns],
            height=240,
            y_label="Khoảng cách (m)"
        )
        st.caption(
            "So sánh quãng đường dừng cần thiết với "
            "khoảng cách tương ứng ngưỡng TTC cảnh báo."
        )
    else:
        st.caption("Chưa đủ dữ liệu quãng đường để vẽ.")

    # 4. Thống kê mức cảnh báo
    st.markdown("#### 4. Thống kê mức cảnh báo")

    if "level" in data.columns:
        alert_counts = (
            data["level"]
            .fillna("Không xác định")
            .astype(str)
            .value_counts()
        )

        if not alert_counts.empty:
            alert_df = alert_counts.rename(
                "Số lần xuất hiện"
            ).to_frame()

            st.bar_chart(
                alert_df,
                height=250,
                y_label="Số lần"
            )
        else:
            st.info("Chưa có dữ liệu mức cảnh báo.")
    else:
        st.caption("Không có cột mức cảnh báo trong dữ liệu.")


def scenario_comparison_chart(rows: list) -> None:
    """
    So sánh kết quả giữa các tình huống mô phỏng.

    rows: Danh sách dictionary chứa thông tin các tình huống.
    """

    st.subheader("So sánh các tình huống mô phỏng")

    if not rows:
        st.info("Chưa có dữ liệu để so sánh các tình huống.")
        return

    df = pd.DataFrame(rows)

    # Các tên cột có thể được dashboard sử dụng
    column_aliases = {
        "scenario": ["scenario", "name", "scenario_name", "Tên tình huống"],
        "speed": ["speed", "speed_kmh", "Tốc độ"],
        "distance": ["distance", "distance_m", "Khoảng cách"],
        "ttc": ["ttc", "ttc_s", "TTC"],
        "d_stop": ["d_stop", "stopping_distance", "Quãng đường dừng"],
    }

    def find_column(key):
        for column in column_aliases[key]:
            if column in df.columns:
                return column
        return None

    name_col = find_column("scenario")

    if name_col is None:
        df["scenario_label"] = [
            f"Tình huống {i + 1}" for i in range(len(df))
        ]
        name_col = "scenario_label"

    speed_col = find_column("speed")
    distance_col = find_column("distance")
    ttc_col = find_column("ttc")
    stop_col = find_column("d_stop")

    # 1. So sánh tốc độ
    st.markdown("#### 1. So sánh tốc độ giữa các tình huống")

    if speed_col:
        speed_df = df.set_index(name_col)[[speed_col]].copy()
        speed_df[speed_col] = pd.to_numeric(
            speed_df[speed_col], errors="coerce"
        )
        speed_df.columns = ["Tốc độ (km/h)"]

        st.bar_chart(speed_df, height=220)
    else:
        st.caption("Không có dữ liệu tốc độ để so sánh.")

    # 2. So sánh khoảng cách
    st.markdown("#### 2. So sánh khoảng cách")

    if distance_col:
        distance_df = df.set_index(name_col)[[distance_col]].copy()
        distance_df[distance_col] = pd.to_numeric(
            distance_df[distance_col], errors="coerce"
        )
        distance_df.columns = ["Khoảng cách (m)"]

        st.bar_chart(distance_df, height=220)
    else:
        st.caption("Không có dữ liệu khoảng cách để so sánh.")

    # 3. So sánh TTC
    st.markdown("#### 3. So sánh thời gian TTC")

    if ttc_col:
        ttc_df = df.set_index(name_col)[[ttc_col]].copy()

        ttc_df[ttc_col] = pd.to_numeric(
            ttc_df[ttc_col], errors="coerce"
        )

        ttc_df[ttc_col] = ttc_df[ttc_col].replace(
            [float("inf"), float("-inf")], float("nan")
        )

        ttc_df.columns = ["TTC (giây)"]

        if not ttc_df.dropna().empty:
            st.bar_chart(ttc_df, height=220)
        else:
            st.caption("Không có giá trị TTC hữu hạn để so sánh.")
    else:
        st.caption("Không có dữ liệu TTC để so sánh.")

    # 4. So sánh quãng đường dừng
    st.markdown("#### 4. So sánh quãng đường dừng")

    if stop_col:
        stop_df = df.set_index(name_col)[[stop_col]].copy()
        stop_df[stop_col] = pd.to_numeric(
            stop_df[stop_col], errors="coerce"
        )
        stop_df.columns = ["Quãng đường dừng (m)"]

        st.bar_chart(stop_df, height=220)
    else:
        st.caption("Không có dữ liệu quãng đường dừng để so sánh.")

    # Bảng dữ liệu tổng hợp
    st.markdown("#### 5. Bảng dữ liệu so sánh")
    st.dataframe(df, use_container_width=True, hide_index=True)
