import streamlit as st
st.set_page_config(layout="wide")
import re
from helper import load_data, load_users, convert_to_df, get_prices_batch, highlight_pl, process_uploaded
import constants

def main():
    mock = True #Variable for mocking and not reaching rate limiting
    __PATH = "/Users/bigdawgs/stock-dashboard/data/"
        
    # Use session state to control the "popup"
    if "show_uploader" not in st.session_state:
        st.session_state.show_uploader = False

    col1, col2 = st.columns([10, 1]) 
    
    with col1:
        st.title("Stock Dashboard")
        all_users = load_users(__PATH)
        
    with col2:
        if st.button("📤 Upload File"):
            st.session_state.show_uploader = True

    if st.session_state.show_uploader:
        with st.expander("Upload your file", expanded=True):
            uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
            if uploaded_file is not None:
                st.success("✅ File uploaded!")
                # You can now read the file with pandas, etc.
                # df = pd.read_csv(uploaded_file)
                # Logic to parse the file here
                process_uploaded(uploaded_file)

            # Option to cancel
            if st.button("❌ Cancel Upload"):
                st.session_state.show_uploader = False
                st.rerun()

    if "selected_users" not in st.session_state:
        st.session_state.selected_users = []
        
    unselected_usernames = [u for u in all_users if u not in st.session_state.selected_users]

    st.write("## User Selection")
    if unselected_usernames:
        selected_user = st.selectbox("Select a user", [""] + unselected_usernames, key="user_selectbox")

        if selected_user and selected_user not in st.session_state.selected_users:
            st.session_state.selected_users.append(selected_user)
            st.rerun()
    else:
        st.info("All users have been selected.")
        
    col1, col2 = st.columns([12, 1])

    with col1:
        if st.button("Select All"):
            st.session_state.selected_users = all_users.copy()
            st.rerun()

    with col2:
        clear_button_pressed = st.button("Clear Selection")
        if clear_button_pressed:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # 🟦 Display selected users with remove buttons
    st.write("### ✅ Currently Selected Users:")

    if st.session_state.selected_users:
        for user in st.session_state.selected_users:
            col1, col2 = st.columns([0.85, 0.15])
            col1.write(user)
            if col2.button("❌", key=f"remove_{user}"):
                st.session_state.selected_users.remove(user)
                st.rerun()
    else:
        st.write("_No users selected yet._")
    
    
    selected_users_data = []
        
    if st.session_state.selected_users:
        for user in st.session_state.selected_users:
            selected_users_data.append(convert_to_df(load_data(user, __PATH)))
            
    #Now need to create a Master df which have all the information
    if selected_users_data:
        master_df = selected_users_data[0]
        master_df.set_index(constants.name, inplace=True)
        for df in selected_users_data[1:]:
            df.set_index(constants.name, inplace=True)
            for name, row in df.iterrows():
                if name in master_df.index:
                    master_row = master_df.loc[name]
                    new_row = {}
                    new_row[constants.name] = name
                    new_row[constants.symbol] = row[constants.symbol]
                    new_row[constants.quantity] = row[constants.quantity] + master_row[constants.quantity]
                    new_row[constants.buy_price] = (row[constants.quantity]*row[constants.buy_price] + master_row[constants.quantity]*master_row[constants.buy_price])/new_row[constants.quantity]
                    master_df.loc[name] = new_row
                else:
                    master_df.loc[name] = row
                     
        master_df.reset_index(inplace=True)
                
        if mock:
            master_df[constants.current_price] = master_df[constants.buy_price] * 1.10
        else:    
            symbols = master_df[constants.symbol].unique().tolist()
            symbol_to_price = get_prices_batch(symbols)
            master_df[constants.current_price] = master_df[constants.symbol].map(symbol_to_price)
        
        master_df[constants.investment_value] = master_df[constants.buy_price] * master_df[constants.quantity]
        master_df[constants.current_value] = master_df[constants.current_price] * master_df[constants.quantity]
        master_df[constants.pnl] = master_df[constants.current_value] - master_df[constants.investment_value]
        master_df[constants.pnl_percentage] = ((master_df[constants.current_price] - master_df[constants.buy_price]) / master_df[constants.buy_price]) * 100

        # Optional: round for cleaner output
        master_df[constants.pnl] = master_df[constants.pnl].round(2)
        master_df[constants.pnl_percentage] = master_df[constants.pnl_percentage].round(2)
        master_df[constants.investment_value] = master_df[constants.investment_value].round(2)
        master_df[constants.current_value] = master_df[constants.current_value].round(2)

        st.title("📈 Stock Portfolio Overview")
        
        search_query = st.text_input("🔍 Search by Symbol or Name").strip()

        # Ensure empty query doesn't break or fetch all rows
        if search_query:
            search_query_clean = re.escape(search_query.lower())  

            filtered_df = master_df[
                master_df[constants.symbol].str.contains(search_query_clean, case=False, na=False) |
                master_df[constants.name].str.contains(search_query_clean, case=False, na=False)
            ]
        else:
            filtered_df = master_df 
        
        # ---- Styled table ----
        st.dataframe(
            filtered_df.style
            .map(highlight_pl, subset=[constants.pnl, constants.pnl_percentage])
            .format({
                constants.buy_price: '₹{:.2f}',
                constants.current_price: '₹{:.2f}',
                constants.quantity: '{:.0f}',
                constants.investment_value: '₹{:.2f}',
                constants.current_value: '₹{:.2f}',
                constants.pnl: '₹{:.2f}',
                constants.pnl_percentage: '{:.2f}%',
            }),
            use_container_width=True
        )


        #### Footer Section
        total_invested = master_df[constants.investment_value].sum()
        total_current = master_df[constants.current_value].sum()
        total_pnl = master_df[constants.pnl].sum()
        total_pnl_percentage = (total_pnl / total_invested * 100) if total_invested else 0.0

        st.markdown("---")
        st.markdown("### 📊 Portfolio Summary")

        col1, col2, col3 = st.columns(3)

        col1.markdown(
            f"<h2 style='text-align: center;'>₹{total_invested:,.2f}</h2><p style='text-align: center;'>Total Invested</p>",
            unsafe_allow_html=True
        )
        col2.markdown(
            f"<h2 style='text-align: center;'>₹{total_current:,.2f}</h2><p style='text-align: center;'>Current Value</p>",
            unsafe_allow_html=True
        )

        pnl_color = "green" if total_pnl >= 0 else "red"
        col3.markdown(
            f"""
            <div style='text-align: center;'>
                <h2 style='color:{pnl_color};'>₹{total_pnl:,.2f}</h2>
                <p style='color:{pnl_color}; font-size: 18px;'>({total_pnl_percentage:.2f}%)</p>
                <p>Total P&L</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        
if __name__ == "__main__":
    main()
