import asyncio
import json

import streamlit as st

from app.errors import PlatformError
from app.services.ccass import get_ccass_service

st.set_page_config(page_title="Joe CCASS Tool", page_icon="📊", layout="wide")
st.title("Joe 港股 CCASS 數據工具")
st.caption("研究用途｜資料日期及 T+2 限制會隨結果顯示")

with st.form("ccass-query"):
    code = st.text_input("港股編號", placeholder="例如：0700")
    limit = st.slider("顯示券商數量", min_value=5, max_value=50, value=15, step=5)
    submitted = st.form_submit_button("查詢", type="primary")

if submitted:
    try:
        with st.spinner("正在查詢及核對 issue ID…"):
            result = asyncio.run(get_ccass_service().get_stock_data(code, holdings_limit=limit))
        data = result.model_dump(mode="json")
        metadata = data["metadata"]
        summary = data["holdings_summary"]

        st.subheader(f"{metadata.get('code')}｜{metadata.get('name') or '名稱待核實'}")
        st.info(
            f"Holdings date：{metadata.get('holdings_date') or '未能取得'}｜"
            f"Issue ID：{metadata.get('issue_id')}｜{metadata.get('settlement_note')}"
        )
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total in CCASS", f"{summary.get('total_in_ccass_pct_of_issued') or 0:.2f}%")
        col2.metric("Top 5／已發行", f"{summary.get('top5_pct_of_issued') or 0:.2f}%")
        col3.metric("Top 10／已發行", f"{summary.get('top10_pct_of_issued') or 0:.2f}%")
        col4.metric("參與者數量", summary.get("participant_count", 0))

        if data["data_quality_warnings"]:
            for warning in data["data_quality_warnings"]:
                st.warning(warning)

        st.dataframe(data["holdings"], use_container_width=True, hide_index=True)
        encoded = json.dumps(data, ensure_ascii=False, indent=2)
        st.download_button("下載 JSON", encoded, file_name=f"{metadata['code']}_ccass.json")
        with st.expander("原始 JSON"):
            st.json(data)
        st.caption(metadata["attribution"])
    except PlatformError as exc:
        st.error(f"{exc.code}: {exc.message}")
        if exc.retry_recommended:
            st.info(f"建議稍後重試；等待約 {exc.retry_after_seconds or 30} 秒。")
    except Exception as exc:
        st.error(f"UNEXPECTED_ERROR: {type(exc).__name__}")
