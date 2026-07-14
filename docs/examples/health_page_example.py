import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("API_BASE_URL", "")
USER_ID = os.environ.get("LOCAL_USER_ID", "tami-dev")


def show():
    st.title("🌅 System Health Check")
    st.caption(f"Logged in as: {USER_ID}")
    st.divider()

    if st.button("Run Health Check", type="primary"):
        with st.spinner("Checking all services..."):
            try:
                response = requests.get(
                    f"{BASE_URL}/health",
                    headers=headers,
                    timeout=10
                )
                data = response.json()

            except Exception as e:
                st.error(f"Could not reach the API — {str(e)}")
                return

        # ─── Overall Status ───
        status = data.get("status", "unknown")
        if status == "ok":
            st.success("✅ All systems operational")
        else:
            st.error("❌ System degraded — check services below")

        st.divider()

        # ─── Services ───
        st.subheader("Services")
        services = data.get("services", {})
        col1, col2, col3 = st.columns(3)

        with col1:
            dynamo = services.get("dynamoDB", {})
            dynamo_status = dynamo.get("status", "unknown")
            if dynamo_status == "connected":
                st.success("✅ DynamoDB")
            else:
                st.error("❌ DynamoDB")
            st.caption(f"Table: {dynamo.get('tableName', 'unknown')}")

        with col2:
            cw = services.get("cloudWatch", {})
            cw_status = cw.get("status", "unknown")
            if cw_status == "connected":
                st.success("✅ CloudWatch")
            else:
                st.error("❌ CloudWatch")
            for log in cw.get("logGroups", []):
                st.caption(log)

        with col3:
            apigw = services.get("apiGateway", {})
            apigw_status = apigw.get("status", "unknown")
            if apigw_status == "connected":
                st.success("✅ API Gateway")
            else:
                st.error("❌ API Gateway")
            st.caption(apigw.get("endpoint", "unknown"))

        st.divider()

        # ─── Routes ───
        st.subheader("API Routes")
        routes = data.get("routes", {})
        col_a, col_b = st.columns(2)
        route_list = list(routes.items())
        half = len(route_list) // 2

        with col_a:
            for route, status in route_list[:half]:
                st.markdown(f"✅ `{route}`")

        with col_b:
            for route, status in route_list[half:]:
                st.markdown(f"✅ `{route}`")

        st.divider()

        # ─── Raw JSON ───
        with st.expander("View raw response"):
            st.json(data)

    