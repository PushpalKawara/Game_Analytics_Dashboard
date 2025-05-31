# import streamlit as st
# import pandas as pd
# import numpy as np
# import re
# import datetime
# import matplotlib.pyplot as plt
# from io import BytesIO
# import xlsxwriter
# from openpyxl import Workbook
# from openpyxl.drawing.image import Image as OpenpyxlImage
# from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
# from openpyxl.utils import get_column_letter
# import tempfile


# Keep only one copy of these imports:
import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt  # <-- Keep this one
from io import BytesIO
import xlsxwriter
from openpyxl import Workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import tempfile
# =============================================
#              AUTHENTICATION
# =============================================
USERNAME = "Pushpal@2025"
PASSWORD = "Pushpal@202512345"

def check_auth():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.form("login"):
            st.subheader("🔐 Login Required")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login = st.form_submit_button("Login")

            if login:
                if username == USERNAME and password == PASSWORD:
                    st.session_state.logged_in = True
                    st.success("Logged in successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Incorrect credentials")
        st.stop()

# =============================================
#              DP1GAME METRIX APP
# =============================================
def dp1game_metrix_app():
    st.set_page_config(page_title="DP1GAME METRIX", layout="wide")
    st.title("📊 DP1GAME METRIX Dashboard")

    def generate_excel(df_summary, df_summary_Progression, retention_fig, drop_fig):
        df_summary_Progression = df_summary_Progression.drop_duplicates(subset='Level', keep='first').reset_index(drop=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_summary.to_excel(writer, index=False, sheet_name='Summary', startrow=0, startcol=0)
            df_summary_Progression.to_excel(writer, index=False, sheet_name='Summary', startrow=0, startcol=3)

            workbook = writer.book
            worksheet = writer.sheets['Summary']

            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#D9E1F2',
                'border': 1
            })

            cell_format = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter'
            })

            highlight_format = workbook.add_format({
                'font_color': 'red',
                'bg_color': 'yellow',
                'align': 'center',
                'valign': 'vcenter'
            })

            for col_num, value in enumerate(df_summary.columns):
                worksheet.write(0, col_num, value, header_format)

            for col_num, value in enumerate(df_summary_Progression.columns):
                worksheet.write(0, col_num + 3, value, header_format)

            for row_num in range(1, len(df_summary) + 1):
                for col_num in range(len(df_summary.columns)):
                    worksheet.write(row_num, col_num, df_summary.iloc[row_num - 1, col_num], cell_format)

            for row_num in range(1, len(df_summary_Progression) + 1):
                for col_num in range(len(df_summary_Progression.columns)):
                    value = df_summary_Progression.iloc[row_num - 1, col_num]
                    col_name = df_summary_Progression.columns[col_num]
                    if col_name == 'Drop' and pd.notna(value) and value >= 3:
                        worksheet.write(row_num, col_num + 3, value, highlight_format)
                    else:
                        worksheet.write(row_num, col_num + 3, value, cell_format)

            worksheet.freeze_panes(1, 0)

            for i, col in enumerate(df_summary.columns):
                column_len = max(df_summary[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)

            for i, col in enumerate(df_summary_Progression.columns):
                column_len = max(df_summary_Progression[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i + 3, i + 3, column_len)

            retention_img = BytesIO()
            retention_fig.savefig(retention_img, format='png')
            retention_img.seek(0)
            worksheet.insert_image('H2', 'retention_chart.png', {'image_data': retention_img})

            drop_img = BytesIO()
            drop_fig.savefig(drop_img, format='png')
            drop_img.seek(0)
            worksheet.insert_image('H37', 'drop_chart.png', {'image_data': drop_img})

        output.seek(0)
        return output

    def main():
        st.subheader("Step 1: Upload Files")
        col1, col2 = st.columns(2)

        with col1:
            file1 = st.file_uploader("📥 Upload Retention Base File", type=["csv"])
        with col2:
            file2 = st.file_uploader("📥 Upload Ad Event File", type=["csv"])

        st.subheader("📝 Editable Fields")
        version = st.text_input("Enter Version (e.g. v1.2.3)", value="v1.0.0")
        date_selected = st.date_input("Date Selected", value=datetime.date.today())
        check_date = st.date_input("Check Date", value=datetime.date.today() + datetime.timedelta(days=1))

        if file1 and file2:
            df1 = pd.read_csv(file1)
            df1.columns = df1.columns.str.strip().str.upper()
            level_columns = ['LEVEL','Level' ,  'LEVELPLAYED', 'TOTALLEVELPLAYED', 'TOTALLEVELSPLAYED']
            level_col = next((col for col in df1.columns if col in level_columns), None)

            if level_col and 'USERS' in df1.columns:
                df1 = df1[[level_col, 'USERS']]

                def clean_level(x):
                    try:
                        return int(re.search(r"(\d+)", str(x)).group(1))
                    except:
                        return None

                df1['LEVEL_CLEAN'] = df1[level_col].apply(clean_level)
                df1.dropna(inplace=True)
                df1['LEVEL_CLEAN'] = df1['LEVEL_CLEAN'].astype(int)
                df1.sort_values('LEVEL_CLEAN', inplace=True)

                level1_users = df1[df1['LEVEL_CLEAN'] == 1]['USERS'].values[0] if 1 in df1['LEVEL_CLEAN'].values else 0
                level2_users = df1[df1['LEVEL_CLEAN'] == 2]['USERS'].values[0] if 2 in df1['LEVEL_CLEAN'].values else 0
                max_users = level2_users if level2_users > level1_users else level1_users

                df1['Retention %'] = round((df1['USERS'] / max_users) * 100, 2)
                df1['Drop'] = ((df1['USERS'] - df1['USERS'].shift(-1)) / df1['USERS']).fillna(0) * 100
                df1['Drop'] = df1['Drop'].round(2)

                retention_20 = round(df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0], 2) if 20 in df1['LEVEL_CLEAN'].values else 0
                retention_50 = round(df1[df1['LEVEL_CLEAN'] == 50]['Retention %'].values[0], 2) if 50 in df1['LEVEL_CLEAN'].values else 0
                retention_75 = round(df1[df1['LEVEL_CLEAN'] == 75]['Retention %'].values[0], 2) if 75 in df1['LEVEL_CLEAN'].values else 0
                retention_100 = round(df1[df1['LEVEL_CLEAN'] == 100]['Retention %'].values[0], 2) if 100 in df1['LEVEL_CLEAN'].values else 0
                retention_150 = round(df1[df1['LEVEL_CLEAN'] == 150]['Retention %'].values[0], 2) if 150 in df1['LEVEL_CLEAN'].values else 0
                retention_200 = round(df1[df1['LEVEL_CLEAN'] == 200]['Retention %'].values[0], 2) if 200 in df1['LEVEL_CLEAN'].values else 0
            else:
                st.error("❌ Required columns not found in file 1.")
                return

            df2 = pd.read_csv(file2)
            df2.columns = df2.columns.str.strip()

            if 'EVENT' in df2.columns and 'USERS' in df2.columns:
                df2 = df2[['EVENT', 'USERS']]
                df2['EVENT_CLEAN'] = df2['EVENT'].apply(
                    lambda x: int(re.search(r"_(\d+)", str(x)).group(1)) if re.search(r"_(\d+)", str(x)) else None
                )
                df2.dropna(inplace=True)
                df2['EVENT_CLEAN'] = df2['EVENT_CLEAN'].astype(int)
                df2 = df2.sort_values('EVENT_CLEAN').reset_index(drop=True)

                level1_users = df1[df1['LEVEL_CLEAN'] == 1]['USERS'].values[0] if 1 in df1['LEVEL_CLEAN'].values else 0
                level2_users = df1[df1['LEVEL_CLEAN'] == 2]['USERS'].values[0] if 2 in df1['LEVEL_CLEAN'].values else 0
                max_users = level2_users if level2_users > level1_users else level1_users

                first_row = pd.DataFrame({'EVENT': ['Assumed_0'], 'USERS': [max_users], 'EVENT_CLEAN': [0]})
                df2 = pd.concat([first_row, df2], ignore_index=True).sort_values('EVENT_CLEAN').reset_index(drop=True)

                df2['% of Users at Ad'] = round((df2['USERS'] / max_users) * 100, 2)

                ad10 = df2[df2['EVENT_CLEAN'] == 10]['% of Users at Ad'].values[0] if 10 in df2['EVENT_CLEAN'].values else 0
                ad20 = df2[df2['EVENT_CLEAN'] == 20]['% of Users at Ad'].values[0] if 20 in df2['EVENT_CLEAN'].values else 0
                ad40 = df2[df2['EVENT_CLEAN'] == 40]['% of Users at Ad'].values[0] if 40 in df2['EVENT_CLEAN'].values else 0
                ad70 = df2[df2['EVENT_CLEAN'] == 70]['% of Users at Ad'].values[0] if 70 in df2['EVENT_CLEAN'].values else 0
                ad100 = df2[df2['EVENT_CLEAN'] == 100]['% of Users at Ad'].values[0] if 100 in df2['EVENT_CLEAN'].values else 0

                df2['Diff of Ads'] = df2['EVENT_CLEAN'].diff().fillna(df2['EVENT_CLEAN']).astype(int)
                df2['Multi1'] = df2['USERS'] * df2['Diff of Ads']
                sum1 = df2['Multi1'].sum()
                df2['Avg Diff Ads'] = df2['Diff of Ads'] / 2
                df2['Diff of Users'] = df2['USERS'].shift(1) - df2['USERS']
                df2['Diff of Users'] = df2['Diff of Users'].fillna(0).astype(int)
                df2['Multi2'] = df2['Avg Diff Ads'] * df2['Diff of Users']
                sum2 = df2['Multi2'].sum()
                avg_ads_per_user = round((sum1 + sum2) / max_users, 2)
            else:
                st.error("❌ Required columns not found in file 2.")
                return

            st.subheader("📈 Retention Chart (Levels 1–100)")
            retention_fig, ax = plt.subplots(figsize=(15, 7))
            df1_100 = df1[df1['LEVEL_CLEAN'] <= 100]

            ax.plot(df1_100['LEVEL_CLEAN'], df1_100['Retention %'],
                    linestyle='-', color='#F57C00', linewidth=2, label='RETENTION')

            ax.set_xlim(1, 100)
            ax.set_ylim(0, 120)
            ax.set_xticks(np.arange(1, 101, 1))
            ax.set_yticks(np.arange(0, 121, 10))

            ax.set_xlabel("Level", labelpad=15)
            ax.set_ylabel("% Of Users", labelpad=15)

            ax.set_title(f"Retention Chart (Levels 1 - 100) | Version {version} | Date: {date_selected.strftime('%d-%m-%Y')}",
                         fontsize=12, fontweight='bold')

            xtick_labels = []
            for val in np.arange(1, 101, 1):
                if val % 5 == 0:
                    xtick_labels.append(f"$\\bf{{{val}}}$")
                else:
                    xtick_labels.append(str(val))
            ax.set_xticklabels(xtick_labels, fontsize=6)

            ax.tick_params(axis='x', labelsize=6)
            ax.grid(True, linestyle='--', linewidth=0.5)

            for x, y in zip(df1_100['LEVEL_CLEAN'], df1_100['Retention %']):
                ax.text(x, -5, f"{int(y)}", ha='center', va='top', fontsize=7)

            ax.legend(loc='lower left', fontsize=8)
            plt.tight_layout(rect=[0, 0.03, 1, 0.97])
            st.pyplot(retention_fig)

            st.subheader("📉 Drop Chart (Levels 1–100)")
            drop_fig, ax2 = plt.subplots(figsize=(15, 6))
            bars = ax2.bar(df1_100['LEVEL_CLEAN'], df1_100['Drop'], color='#EF5350', label='DROP RATE')

            ax2.set_xlim(1, 100)
            ax2.set_ylim(0, max(df1_100['Drop'].max(), 10) + 10)
            ax2.set_xticks(np.arange(1, 101, 1))
            ax2.set_yticks(np.arange(0, max(df1_100['Drop'].max(), 10) + 11, 5))
            ax2.set_xlabel("Level")
            ax2.set_ylabel("% Of Users Dropped")
            ax2.set_title(f"Drop Chart (Levels 1 - 100) | Version {version} | Date: {date_selected.strftime('%d-%m-%Y')}",
                          fontsize=12, fontweight='bold')

            ax2.set_xticklabels(xtick_labels, fontsize=6)
            ax2.tick_params(axis='x', labelsize=6)
            ax2.grid(True, linestyle='--', linewidth=0.5)

            for bar in bars:
                x = bar.get_x() + bar.get_width() / 2
                y = bar.get_height()
                ax2.text(x, -2, f"{y:.0f}", ha='center', va='top', fontsize=7)

            ax2.legend(loc='upper right', fontsize=8)
            plt.tight_layout()
            st.pyplot(drop_fig)

            default_summary_data = {
                "Version": version,
                "Date Selected": date_selected.strftime("%d-%b-%y"),
                "Check Date": check_date.strftime("%d-%b-%y"),
                "Level 2 Users": int(max_users),
                "Total Level Retention (20)": f"{retention_20}%",
                "Total Level Retention (50)": f"{retention_50}%",
                "Total Level Retention (75)": f"{retention_75}%",
                "Total Level Retention (100)": f"{retention_100}%",
                "Total Level Retention (150)": f"{retention_150}%",
                "Total Level Retention (200)": f"{retention_200}%",
                "% of Users at Ad 10": f"{ad10}%",
                "% of Users at Ad 20": f"{ad20}%",
                "% of Users at Ad 40": f"{ad40}%",
                "% of Users at Ad 70": f"{ad70}%",
                "% of Users at Ad 100": f"{ad100}%",
                "Avg Ads per User": avg_ads_per_user
            }

            df_summary = pd.DataFrame(list(default_summary_data.items()), columns=["Metric", "Value"])

            tab1, tab2 = st.tabs(["📥 Manual Input", "📋 Copy Summary"])
            with tab1:
                st.markdown("### 🔧 Enter Manual Metrics Here:")
                day1_retention = st.text_input("Day 1 Retention (%)", value="29.56%")
                day3_retention = st.text_input("Day 3 Retention (%)", value="13.26%")
                session_length = st.text_input("Session Length (in sec)", value="264.5")
                playtime_length = st.text_input("Playtime Length (in sec)", value="936.6")

                if st.button("Update Summary Table"):
                    df_summary = df_summary.set_index("Metric")
                    df_summary.loc["Day 1 Retention"] = day1_retention
                    df_summary.loc["Day 3 Retention"] = day3_retention
                    df_summary.loc["Session Length"] = f"{session_length} s"
                    df_summary.loc["Playtime Length"] = f"{playtime_length} s"
                    df_summary = df_summary.reset_index()

            df_summary_Progression = df1[['LEVEL_CLEAN', 'USERS', 'Retention %', 'Drop']].rename(columns={'LEVEL_CLEAN': 'Level'})

            st.subheader("⬇️ Download Excel Report")
            st.dataframe(df_summary)

            excel_data = generate_excel(df_summary, df_summary_Progression, retention_fig, drop_fig)
            st.download_button(
                 label="📥 Download Excel Report",
                 data=excel_data,
                 file_name=f"DP1_METRIX_Report_{version}.xlsx",
                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    main()

# =============================================
#          GAME PROGRESSION APP
# =============================================
def game_progression_app():
    st.set_page_config(page_title="GAME PROGRESSION", layout="wide")
    st.title("📊 GAME PROGRESSION Dashboard")

    def generate_excel(df_export, retention_fig, drop_fig, drop_comb_fig):
        df_export = df_export.drop_duplicates(subset='Level', keep='first').reset_index(drop=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, sheet_name='Summary', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Summary']

            header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#D9E1F2', 'border': 1})
            cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})

            for col_num, value in enumerate(df_export.columns):
                worksheet.write(0, col_num, value, header_format)

            for row_num in range(1, len(df_export) + 1):
                for col_num in range(len(df_export.columns)):
                    value = df_export.iloc[row_num - 1, col_num]
                    col_name = df_export.columns[col_num]

                    if isinstance(value, (np.generic, np.bool_)):
                        value = value.item()
                    if pd.isna(value):
                        value = ""

                    try:
                        if col_name in ['Game Play Drop', 'Popup Drop', 'Total Level Drop'] and isinstance(value, (int, float)):
                            if value >= 10:
                                format_to_apply = workbook.add_format({'bg_color': '#8B0000', 'font_color': 'white', 'align': 'center', 'valign': 'vcenter', 'bold': True})
                            elif value >= 5:
                                format_to_apply = workbook.add_format({'bg_color': '#CD5C5C', 'font_color': 'white', 'align': 'center', 'valign': 'vcenter', 'bold': True})
                            elif value >= 3:
                                format_to_apply = workbook.add_format({'bg_color': '#FFC0CB', 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'bold': True})
                            else:
                                format_to_apply = cell_format
                            worksheet.write(row_num, col_num, value, format_to_apply)
                        else:
                            worksheet.write(row_num, col_num, value, cell_format)
                    except Exception as e:
                        st.warning(f"⚠️ Could not write value at row {row_num} col {col_num}: {e}")

            worksheet.freeze_panes(1, 0)

            for i, col in enumerate(df_export.columns):
                column_len = max(df_export[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)

            retention_img = BytesIO()
            retention_fig.savefig(retention_img, format='png', dpi=300, bbox_inches='tight')
            retention_img.seek(0)
            worksheet.insert_image('M2', 'retention_chart.png', {'image_data': retention_img})

            drop_img = BytesIO()
            drop_fig.savefig(drop_img, format='png', dpi=300, bbox_inches='tight')
            drop_img.seek(0)
            worksheet.insert_image('M37', 'drop_chart.png', {'image_data': drop_img})

            drop_comb_img = BytesIO()
            drop_comb_fig.savefig(drop_comb_img, format='png', dpi=300, bbox_inches='tight')
            drop_comb_img.seek(0)
            worksheet.insert_image('M67', 'drop_comb_chart.png', {'image_data': drop_comb_img})

        output.seek(0)
        return output

    def main():
        start_file = st.file_uploader("📂 Upload Start Level File", type=["xlsx", "csv"])
        complete_file = st.file_uploader("📂 Upload Complete Level File", type=["xlsx", "csv"])
        version = st.text_input("📌 Game Version", value="1.0.0")
        date_selected = st.date_input("📅 Select Date", value=datetime.date.today())

        if start_file and complete_file:
            df_start = pd.read_excel(start_file) if start_file.name.endswith(".xlsx") else pd.read_csv(start_file)
            df_complete = pd.read_excel(complete_file) if complete_file.name.endswith(".xlsx") else pd.read_csv(complete_file)

            df_start.columns = df_start.columns.str.strip().str.upper()
            level_columns = ['LEVEL', 'LEVELPLAYED', 'TOTALLEVELPLAYED', 'TOTALLEVELSPLAYED']
            level_col_start = next((col for col in df_start.columns if col in level_columns), None)
            user_col_start = next((col for col in df_start.columns if 'USER' in col), None)

            if level_col_start and user_col_start:
                df_start = df_start[[level_col_start, user_col_start]]

                def clean_level(x):
                    try:
                        return int(re.search(r"(\d+)", str(x)).group(1))
                    except:
                        return None

                df_start['LEVEL_CLEAN'] = df_start[level_col_start].apply(clean_level)
                df_start.dropna(inplace=True)
                df_start['LEVEL_CLEAN'] = df_start['LEVEL_CLEAN'].astype(int)
                df_start.sort_values('LEVEL_CLEAN', inplace=True)
                df_start.rename(columns={user_col_start: 'Start Users'}, inplace=True)
            else:
                st.error("❌ Required columns not found in start file.")
                return

            df_complete.columns = df_complete.columns.str.strip().str.upper()
            level_col_complete = next((col for col in df_complete.columns if col in level_columns), None)
            user_col_complete = next((col for col in df_complete.columns if 'USER' in col), None)

            additional_columns = ['PLAYTIME_AVG', 'HINT_USED_SUM', 'RETRY_COUNT_SUM', 'SKIPPED_SUM', 'ATTEMPT_SUM','PREFAB_NAME']
            available_additional_cols = [col for col in additional_columns if col in df_complete.columns]
            df_complete[available_additional_cols] = df_complete[available_additional_cols].round(2)

            if level_col_complete and user_col_complete:
                cols_to_keep = [level_col_complete, user_col_complete] + available_additional_cols
                df_complete = df_complete[cols_to_keep]

                df_complete['LEVEL_CLEAN'] = df_complete[level_col_complete].apply(clean_level)
                df_complete.dropna(inplace=True)
                df_complete['LEVEL_CLEAN'] = df_complete['LEVEL_CLEAN'].astype(int)
                df_complete.sort_values('LEVEL_CLEAN', inplace=True)
                df_complete.rename(columns={user_col_complete: 'Complete Users'}, inplace=True)
            else:
                st.error("❌ Required columns not found in complete file.")
                return

            df = pd.merge(df_start, df_complete, on='LEVEL_CLEAN', how='outer').sort_values('LEVEL_CLEAN')
            base_users = df[df['LEVEL_CLEAN'].isin([1, 2])]['Start Users'].max()

            df['Game Play Drop'] = ((df['Start Users'] - df['Complete Users']) / df['Start Users']) * 100
            df['Popup Drop'] = ((df['Complete Users'] - df['Start Users'].shift(-1)) / df['Complete Users']) * 100
            df['Total Level Drop'] = df['Game Play Drop'] + df['Popup Drop']
            df['Retention %'] = (df['Start Users'] / base_users) * 100

            if 'RETRY_COUNT_SUM' in df.columns:
                df['Attempt'] = df['RETRY_COUNT_SUM'] / df['Complete Users']

            metric_cols = ['Game Play Drop', 'Popup Drop', 'Total Level Drop', 'Retention %']
            if 'Attempt' in df.columns:
                metric_cols.append('Attempt')

            df[metric_cols] = df[metric_cols].round(2)

            df_100 = df[df['LEVEL_CLEAN'] <= 100]

            xtick_labels = []
            for val in np.arange(1, 101, 1):
                if val % 5 == 0:
                    xtick_labels.append(f"$\\bf{{{val}}}$")
                else:
                    xtick_labels.append(str(val))

            st.subheader("📈 Retention Chart (Levels 1-100)")
            retention_fig, ax = plt.subplots(figsize=(15, 7))
            df_100 = df[df['LEVEL_CLEAN'] <= 100]

            ax.plot(df_100['LEVEL_CLEAN'], df_100['Retention %'],
                    linestyle='-', color='#F57C00', linewidth=2, label='RETENTION')

            ax.set_xlim(1, 100)
            ax.set_ylim(0, 110)
            ax.set_xticks(np.arange(1, 101, 1))
            ax.set_yticks(np.arange(0, 110, 5))

            ax.set_xlabel("Level", labelpad=15)
            ax.set_ylabel("% Of Users", labelpad=15)

            ax.set_title(f"Retention Chart (Levels 1-100) | Version {version} | Date: {date_selected.strftime('%d-%m-%Y')}",
                         fontsize=12, fontweight='bold')

            ax.set_xticklabels(xtick_labels, fontsize=6)
            ax.tick_params(axis='x', labelsize=6)
            ax.grid(True, linestyle='--', linewidth=0.5)

            for x, y in zip(df_100['LEVEL_CLEAN'], df_100['Retention %']):
                if not np.isnan(y):
                    ax.text(x, -5, f"{int(y)}", ha='center', va='top', fontsize=7)

            ax.legend(loc='lower left', fontsize=8)
            plt.tight_layout(rect=[0, 0.03, 1, 0.97])
            st.pyplot(retention_fig)

            st.subheader("📉 Total Drop Chart (Levels 1-100)")
            drop_fig, ax2 = plt.subplots(figsize=(15, 6))
            bars = ax2.bar(df_100['LEVEL_CLEAN'], df_100['Total Level Drop'], color='#EF5350', label='DROP RATE')

            ax2.set_xlim(1, 100)
            ax2.set_ylim(0, max(df_100['Total Level Drop'].max(), 10) + 10)
            ax2.set_xticks(np.arange(1, 101, 1))
            ax2.set_yticks(np.arange(0, max(df_100['Total Level Drop'].max(), 10) + 11, 5))
            ax2.set_xlabel("Level")
            ax2.set_ylabel("% Of Users Drop")
            ax2.set_title(f"Total Level Drop Chart | Version {version} | Date: {date_selected.strftime('%d-%m-%Y')}",
                          fontsize=12, fontweight='bold')

            ax2.set_xticklabels(xtick_labels, fontsize=6)
            ax2.tick_params(axis='x', labelsize=6)
            ax2.grid(True, linestyle='--', linewidth=0.5)

            for bar in bars:
                x = bar.get_x() + bar.get_width() / 2
                y = bar.get_height()
                ax2.text(x, -2, f"{y:.0f}", ha='center', va='top', fontsize=7)

            ax2.legend(loc='upper right', fontsize=8)
            plt.tight_layout()
            st.pyplot(drop_fig)

            st.subheader("📉 Combo Drop Chart (Levels 1-100)")
            drop_comb_fig, ax3 = plt.subplots(figsize=(15, 6))

            width = 0.4
            x = df_100['LEVEL_CLEAN']
            ax3.bar(x + width/2, df_100['Game Play Drop'], width, color='#66BB6A', label='Game Play Drop')
            ax3.bar(x - width/2, df_100['Popup Drop'], width, color='#42A5F5', label='Popup Drop')

            ax3.set_xlim(1, 100)
            max_drop = max(df_100['Game Play Drop'].max(), df_100['Popup Drop'].max())
            ax3.set_ylim(0, max(max_drop, 10) + 10)
            ax3.set_xticks(np.arange(1, 101, 1))
            ax3.set_yticks(np.arange(0, max(max_drop, 10) + 11, 5))
            ax3.set_xlabel("Level")
            ax3.set_ylabel("% Of Users Dropped")
            ax3.set_title(f"Game Play  & Popup Drop Chart | Version {version} | Date: {date_selected.strftime('%d-%m-%Y')}",
                          fontsize=12, fontweight='bold')

            ax3.set_xticklabels(xtick_labels, fontsize=6)
            ax3.tick_params(axis='x', labelsize=6)
            ax3.grid(True, linestyle='--', linewidth=0.5)
            ax3.legend(loc='upper right', fontsize=8)
            plt.tight_layout()
            st.pyplot(drop_comb_fig)

            st.subheader("⬇️ Download Excel Report")
            export_columns = ['LEVEL_CLEAN', 'Start Users', 'Complete Users',
                             'Game Play Drop', 'Popup Drop', 'Total Level Drop',
                             'Retention %'] + available_additional_cols

            df_export = df[export_columns].rename(columns={'LEVEL_CLEAN': 'Level'})
            st.dataframe(df_export)

            excel_data = generate_excel(df_export, retention_fig, drop_fig, drop_comb_fig)
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_data,
                file_name=f"GAME_PROGRESSION_Report_{version}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    main()

# =============================================
#          GAME ANALYTICS TOOL APP
# =============================================
def game_analytics_app():
    st.set_page_config(page_title="Game Analytics Tool", layout="wide")
    st.title("🎮 Game Level Data Analyzer")

    def clean_level(level):
        if pd.isna(level):
            return 0
        return int(re.sub(r'\D', '', str(level)))

    def process_files(start_df, complete_df):
        def get_column(df, possible_names):
            for col in df.columns:
                if col.strip().lower() in [name.lower() for name in possible_names]:
                    return col
            return None

        level_col = get_column(start_df, ['LEVEL', 'TOTALLEVELS', 'STAGE'])
        game_col = get_column(start_df, ['GAME_ID', 'CATEGORY', 'Game_name'])
        diff_col = get_column(start_df, ['DIFFICULTY', 'mode'])

        playtime_col = get_column(complete_df, ['PLAY_TIME_AVG', 'PLAYTIME', 'PLAYTIME_AVG', 'playtime_avg'])
        hint_col = get_column(complete_df, ['HINT_USED_SUM', 'HINT_USED', 'HINT'])
        skipped_col = get_column(complete_df, ['SKIPPED_SUM', 'SKIPPED', 'SKIP'])
        attempts_col = get_column(complete_df, ['ATTEMPTS_SUM', 'ATTEMPTS', 'TRY_COUNT'])

        for df in [start_df, complete_df]:
            if level_col:
                df[level_col] = df[level_col].apply(clean_level)
                df.sort_values(level_col, inplace=True)

        rename_dict_start = {'USERS': 'Start Users'}
        if level_col:
            rename_dict_start[level_col] = 'LEVEL'
        if game_col:
            rename_dict_start[game_col] = 'GAME_ID'
        if diff_col:
            rename_dict_start[diff_col] = 'DIFFICULTY'
        start_df.rename(columns=rename_dict_start, inplace=True)

        rename_dict_complete = {}
        if level_col:
            rename_dict_complete[level_col] = 'LEVEL'
        if game_col:
            rename_dict_complete[game_col] = 'GAME_ID'
        if diff_col:
            rename_dict_complete[diff_col] = 'DIFFICULTY'
        if playtime_col:
            rename_dict_complete[playtime_col] = 'PLAY_TIME_AVG'
        if hint_col:
            rename_dict_complete[hint_col] = 'HINT_USED_SUM'
        if skipped_col:
            rename_dict_complete[skipped_col] = 'SKIPPED_SUM'
        if attempts_col:
            rename_dict_complete[attempts_col] = 'ATTEMPTS_SUM'
        rename_dict_complete['USERS'] = 'Complete Users'
        complete_df.rename(columns=rename_dict_complete, inplace=True)

        merge_cols = []
        if 'GAME_ID' in start_df.columns:
            merge_cols.append('GAME_ID')
        if 'DIFFICULTY' in start_df.columns:
            merge_cols.append('DIFFICULTY')
        if 'LEVEL' in start_df.columns:
            merge_cols.append('LEVEL')
        merged = pd.merge(start_df, complete_df, on=merge_cols, how='outer', suffixes=('_start', '_complete'))

        keep_cols = []
        if 'GAME_ID' in merged.columns:
            keep_cols.append('GAME_ID')
        if 'DIFFICULTY' in merged.columns:
            keep_cols.append('DIFFICULTY')
        if 'LEVEL' in merged.columns:
            keep_cols.append('LEVEL')
        keep_cols.extend(['Start Users', 'Complete Users'])
        if playtime_col and 'PLAY_TIME_AVG' in merged.columns:
            keep_cols.append('PLAY_TIME_AVG')
        if hint_col and 'HINT_USED_SUM' in merged.columns:
            keep_cols.append('HINT_USED_SUM')
        if skipped_col and 'SKIPPED_SUM' in merged.columns:
            keep_cols.append('SKIPPED_SUM')
        if attempts_col and 'ATTEMPTS_SUM' in merged.columns:
            keep_cols.append('ATTEMPTS_SUM')

        merged = merged[[col for col in keep_cols if col in merged.columns]]

        if 'Start Users' in merged.columns and 'Complete Users' in merged.columns:
            merged['Game Play Drop'] = ((merged['Start Users'] - merged['Complete Users']) / merged['Start Users'].replace(0, np.nan)) * 100
            merged['Popup Drop'] = ((merged['Complete Users'] - merged['Start Users'].shift(-1)) / merged['Complete Users'].replace(0, np.nan)) * 100
        else:
            merged['Game Play Drop'] = 0
            merged['Popup Drop'] = 0

        def calculate_retention(group):
            if 'Start Users' not in group.columns:
                group['Retention %'] = 0
                return group
            base_users = group[group['LEVEL'].isin([1, 2])]['Start Users'].max()
            if base_users == 0 or pd.isnull(base_users):
                base_users = group['Start Users'].max()
            group['Retention %'] = (group['Start Users'] / base_users) * 100
            return group

        group_cols = []
        if 'GAME_ID' in merged.columns:
            group_cols.append('GAME_ID')
        if 'DIFFICULTY' in merged.columns:
            group_cols.append('DIFFICULTY')
        if not group_cols:
            merged['All Data'] = 'All Data'
            group_cols = ['All Data']
        merged = merged.groupby(group_cols, group_keys=False).apply(calculate_retention)

        fill_cols = ['Start Users', 'Complete Users']
        key_columns = ['PLAY_TIME_AVG', 'HINT_USED_SUM', 'SKIPPED_SUM', 'ATTEMPTS_SUM']
        for col in key_columns:
            if col in merged.columns:
                fill_cols.append(col)
        merged.fillna({col: 0 for col in fill_cols}, inplace=True)

        if 'Game Play Drop' in merged.columns and 'Popup Drop' in merged.columns:
            merged['Total Level Drop'] = merged['Game Play Drop'] + merged['Popup Drop']
        else:
            merged['Total Level Drop'] = 0

        return merged

    def create_charts(df, game_name):
        charts = {}
        df_100 = df[df['LEVEL'] <= 100]

        xtick_labels = []
        for val in np.arange(1, 101, 1):
            if val % 5 == 0:
                xtick_labels.append(f"$\\bf{{{val}}}$")
            else:
                xtick_labels.append(str(val))

        fig1, ax1 = plt.subplots(figsize=(15, 5))
        if 'Retention %' in df_100.columns and not df_100['Retention %'].dropna().empty:
            ax1.plot(df_100['LEVEL'], df_100['Retention %'],
                     linestyle='-', color='#F57C00', linewidth=2, label='Retention')

            ax1.set_xlim(1, 100)
            ax1.set_ylim(0, 110)
            ax1.set_xticks(np.arange(1, 101, 1))
            ax1.set_yticks(np.arange(0, 111, 5))
            ax1.set_xticklabels(xtick_labels, fontsize=4)
            ax1.tick_params(axis='x', labelsize=6)
            ax1.grid(True, linestyle='--', linewidth=0.5)

            ax1.set_xlabel("Level", labelpad=15)
            ax1.set_ylabel("% Of Users", labelpad=15)
            ax1.set_title(f"{game_name} | Retention Chart (Levels 1–100)",
                          fontsize=12, fontweight='bold')
            ax1.legend(loc='lower left', fontsize=8)

            for x, y in zip(df_100['LEVEL'], df_100['Retention %']):
                if not np.isnan(y):
                    ax1.text(x, -5, f"{int(y)}", ha='center', va='top', fontsize=5)

        charts['retention'] = fig1

        fig2, ax2 = plt.subplots(figsize=(15, 5))
        if 'Total Level Drop' in df_100.columns and not df_100['Total Level Drop'].dropna().empty:
            bars = ax2.bar(df_100['LEVEL'], df_100['Total Level Drop'],
                           color='#EF5350', label='Drop Rate')

            drop_max = df_100['Total Level Drop'].max()
            drop_max = drop_max if not pd.isna(drop_max) else 0
            ymax = max(drop_max, 10) + 10

            ax2.set_xlim(1, 100)
            ax2.set_ylim(0, ymax)
            ax2.set_xticks(np.arange(1, 101, 1))
            ax2.set_yticks(np.arange(0, ymax + 1, 5))
            ax2.set_xticklabels(xtick_labels, fontsize=4)
            ax2.tick_params(axis='x', labelsize=6)
            ax2.grid(True, linestyle='--', linewidth=0.5)

            ax2.set_xlabel("Level")
            ax2.set_ylabel("% Of Users Drop")
            ax2.set_title(f"{game_name} | Total Drop Chart (Levels 1–100)",
                          fontsize=12, fontweight='bold')
            ax2.legend(loc='upper right', fontsize=8)

            for bar in bars:
                x = bar.get_x() + bar.get_width() / 2
                y = bar.get_height()
                ax2.text(x, -2, f"{y:.0f}", ha='center', va='top', fontsize=5)

        charts['total_drop'] = fig2

        fig3, ax3 = plt.subplots(figsize=(15, 5))
        if ('Game Play Drop' in df_100.columns and
            'Popup Drop' in df_100.columns and
            not df_100['Game Play Drop'].dropna().empty and
            not df_100['Popup Drop'].dropna().empty):

            width = 0.4
            x = df_100['LEVEL']
            ax3.bar(x - width/2, df_100['Popup Drop'], width,
                    color='#42A5F5', label='Popup Drop')
            ax3.bar(x + width/2, df_100['Game Play Drop'], width,
                    color='#66BB6A', label='Game Play Drop')

            gpd_max = df_100['Game Play Drop'].max()
            pd_max = df_100['Popup Drop'].max()
            gpd_max = gpd_max if not pd.isna(gpd_max) else 0
            pd_max = pd_max if not pd.isna(pd_max) else 0
            max_drop = max(gpd_max, pd_max, 10) + 10

            ax3.set_xlim(1, 100)
            ax3.set_ylim(0, max_drop)
            ax3.set_xticks(np.arange(1, 101, 1))
            ax3.set_yticks(np.arange(0, max_drop + 1, 5))
            ax3.set_xticklabels(xtick_labels, fontsize=4)
            ax3.tick_params(axis='x', labelsize=6)
            ax3.grid(True, linestyle='--', linewidth=0.5)

            ax3.set_xlabel("Level")
            ax3.set_ylabel("% Of Users Dropped")
            ax3.set_title(f"{game_name} | Game Play & Popup Drop (Levels 1–100)",
                          fontsize=10, fontweight='bold')
            ax3.legend(loc='upper right', fontsize=6)

        charts['combined_drop'] = fig3

        return charts

    def generate_excel(processed_data):
        wb = Workbook()
        wb.remove(wb.active)

        main_sheet = wb.create_sheet("MAIN_TAB")
        main_headers = ["Index", "Sheet Name", "Game Play Drop Count", "Popup Drop Count",
                        "Total Level Drop Count", "LEVEL_Start", "Start Users",
                        "LEVEL_End", "USERS_END", "Link to Sheet"]
        main_sheet.append(main_headers)

        for col in main_sheet[1]:
            col.font = Font(bold=True, color="FFFFFF")
            col.fill = PatternFill("solid", fgColor="4F81BD")

        for idx, (game_key, df) in enumerate(processed_data.items(), start=1):
            sheet_name = str(game_key)[:31]
            ws = wb.create_sheet(sheet_name)

            headers = ["=HYPERLINK(\"#MAIN_TAB!A1\", \"Back to Main\")", "Start Users", "Complete Users",
                       "Game Play Drop", "Popup Drop", "Total Level Drop", "Retention %",
                       "PLAY_TIME_AVG", "HINT_USED_SUM", "SKIPPED_SUM", "ATTEMPTS_SUM"]
            ws.append(headers)
            ws['A1'].font = Font(color="0000FF", underline="single", bold=True, size=14)
            ws['A1'].fill = PatternFill("solid", fgColor="FFFF00")
            ws.column_dimensions['A'].width = 25

            for _, row in df.iterrows():
                row_values = [
                    row.get('LEVEL', 0),
                    row.get('Start Users', 0),
                    row.get('Complete Users', 0),
                    round(row.get('Game Play Drop', 0), 2),
                    round(row.get('Popup Drop', 0), 2),
                    round(row.get('Total Level Drop', 0), 2),
                    round(row.get('Retention %', 0), 2),
                    round(row.get('PLAY_TIME_AVG', 0), 2),
                    round(row.get('HINT_USED_SUM', 0), 2),
                    round(row.get('SKIPPED_SUM', 0), 2),
                    round(row.get('ATTEMPTS_SUM', 0), 2),
                ]
                ws.append(row_values)

            apply_sheet_formatting(ws)
            apply_conditional_formatting(ws, df.shape[0])
            charts = create_charts(df, sheet_name)
            add_charts_to_excel(ws, charts)

            main_row = [
                idx, sheet_name,
                sum(df.get('Game Play Drop', 0) >= 3),
                sum(df.get('Popup Drop', 0) >= 3),
                sum(df.get('Total Level Drop', 0) >= 3),
                df.get('LEVEL', 0).min(),
                df.get('Start Users', 0).max(),
                df.get('LEVEL', 0).max(),
                df.get('Complete Users', 0).iloc[-1] if not df.empty else 0,
                f'=HYPERLINK("#{sheet_name}!A1", "View")'
            ]
            main_sheet.append(main_row)

        for row in main_sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if cell.row == 1:
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill("solid", fgColor="4F81BD")

        column_widths = [8, 25, 20, 18, 20, 12, 15, 12, 15, 15]
        for i, width in enumerate(column_widths, start=1):
            main_sheet.column_dimensions[get_column_letter(i)].width = width

        return wb

    def apply_sheet_formatting(sheet):
        sheet.freeze_panes = 'A2'
        for cell in sheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="DDDDDD")
        if sheet.title != "MAIN_TAB":
            a1_cell = sheet['A1']
            a1_cell.font = Font(color="0000FF", underline="single", bold=True, size=11)
            a1_cell.fill = PatternFill("solid", fgColor="FFFF00")
            sheet.column_dimensions['A'].width = 14
            cell.alignment = Alignment(horizontal='center', vertical='center')

        for col in sheet.columns:
            if col[0].column == 1 and sheet.title != "MAIN_TAB":
                continue
            max_length = max(len(str(cell.value)) for cell in col)
            sheet.column_dimensions[get_column_letter(col[0].column)].width = max_length + 2

    def apply_conditional_formatting(sheet, num_rows):
        for row in sheet.iter_rows(min_row=2, max_row=num_rows+1):
            for cell in row:
                if cell.column_letter in ['D', 'E', 'F'] and isinstance(cell.value, (int, float)):
                    if cell.value >= 10:
                        cell.fill = PatternFill(start_color='990000', end_color='990000', fill_type='solid')
                        cell.font = Font(color="FFFFFF")
                    elif cell.value >= 7:
                        cell.fill = PatternFill(start_color='CC3333', end_color='CC3333', fill_type='solid')
                        cell.font = Font(color="FFFFFF")
                    elif cell.value >= 3:
                        cell.fill = PatternFill(start_color='FF6666', end_color='FF6666', fill_type='solid')
                        cell.font = Font(color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center')

    def add_charts_to_excel(worksheet, charts):
        img_positions = {'retention': 'M2', 'total_drop': 'M52', 'combined_drop': 'M98'}
        for chart_type, pos in img_positions.items():
            if chart_type in charts:
                img_data = BytesIO()
                charts[chart_type].savefig(img_data, format='png', dpi=150, bbox_inches='tight')
                img_data.seek(0)
                img = OpenpyxlImage(img_data)
                worksheet.add_image(img, pos)
                plt.close(charts[chart_type])

    def main():
        st.sidebar.header("Upload Files")
        start_file = st.sidebar.file_uploader("LEVEL_START.csv", type="csv")
        complete_file = st.sidebar.file_uploader("LEVEL_COMPLETE.csv", type="csv")

        if start_file and complete_file:
            with st.spinner("Processing data..."):
                try:
                    start_df = pd.read_csv(start_file)
                    complete_df = pd.read_csv(complete_file)
                    merged = process_files(start_df, complete_df)

                    group_cols = []
                    if 'GAME_ID' in merged.columns:
                        group_cols.append('GAME_ID')
                    if 'DIFFICULTY' in merged.columns:
                        group_cols.append('DIFFICULTY')
                    if not group_cols:
                        if 'All Data' not in merged.columns:
                            merged['All Data'] = 'All Data'
                        group_cols = ['All Data']

                    processed_data = {}
                    for group_key, group_df in merged.groupby(group_cols):
                        key = '_'.join(map(str, group_key)) if isinstance(group_key, tuple) else str(group_key)
                        processed_data[key] = group_df

                    wb = generate_excel(processed_data)
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        wb.save(tmp.name)
                        with open(tmp.name, "rb") as f:
                            excel_bytes = f.read()

                    st.success("Processing complete!")
                    st.download_button(
                        label="📥 Download Consolidated Report",
                        data=excel_bytes,
                        file_name="Game_Analytics_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    with st.expander("Preview Processed Data"):
                        st.dataframe(merged.head(20))

                except Exception as e:
                    st.error(f"Error processing files: {str(e)}")

    main()

# =============================================
#          FOURTH APP (PLACEHOLDER)
# =============================================
def fourth_app():
    st.set_page_config(page_title="Fourth App", layout="wide")
    st.title("📊 Fourth Application")
    st.write("This is a placeholder for the fourth application.")
    st.info("Work in progress - coming soon!")

# =============================================
#              MAIN APP ROUTER
# =============================================
def main_app():
    st.sidebar.title("Navigation")
    app_choice = st.sidebar.radio("Select Application", [
        "DP1GAME METRIX",
        "GAME PROGRESSION",
        "Game Analytics Tool",
        "Fourth App"
    ])

    if app_choice == "DP1GAME METRIX":
        dp1game_metrix_app()
    elif app_choice == "GAME PROGRESSION":
        game_progression_app()
    elif app_choice == "Game Analytics Tool":
        game_analytics_app()
    elif app_choice == "Fourth App":
        fourth_app()

# =============================================
#              RUN THE APPLICATION
# =============================================
if __name__ == "__main__":
    check_auth()
    main_app()
