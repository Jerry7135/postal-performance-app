import streamlit as st
import pandas as pd

# ==========================================
# 1. 核心計算邏輯
# ==========================================
def clamp(val, min_v, max_v):
    """將數值限制在 [min_v, max_v] 區間"""
    return max(min_v, min(max_v, val))

class PostalPerformanceCalculator:
    def __init__(self):
        self.results = {}

    def calc_post_expenditure(self, actual, budget):
        if budget == 0: return 80.0
        ratio = (actual / budget) * 100.0
        score = clamp(80.0 - (ratio - 100.0) * 1.0, 60.0, 100.0)
        self.results["郵儲壽支出"] = {"score": score, "weight": 8}
        return score

    def calc_personnel_cost(self, actual, target_budget):
        if target_budget == 0: return 80.0
        diff_pct = ((actual - target_budget) / target_budget) * 100.0
        score = clamp(80.0 - diff_pct * 2.0, 60.0, 100.0)
        self.results["用人費用"] = {"score": score, "weight": 8}
        return score

    def calc_annual_leave_rate(self, taken_days, total_entitled_days):
        if total_entitled_days == 0: return 90.0
        rate = (taken_days / total_entitled_days) * 100.0
        if rate <= 40.0: score = 60.0
        elif rate >= 60.0: score = 100.0
        else: score = clamp(90.0 + (rate - 55.0) / 0.5 * 1.0, 60.0, 100.0)
        self.results["行政單位員工特休實施率"] = {"score": score, "weight": 1}
        return score

    def calc_employee_productivity(self, actual_prod, budget_prod):
        if budget_prod == 0: return 80.0
        diff_pct = ((actual_prod - budget_prod) / budget_prod) * 100.0
        score = clamp(80.0 + diff_pct * 1.0, 60.0, 100.0)
        self.results["員工生產力"] = {"score": score, "weight": 5}
        return score

    def calc_mail_operating_ratio(self, current_ratio, last_year_ratio):
        if last_year_ratio == 0: return 85.0
        diff = (current_ratio / last_year_ratio) * 100.0 - 100.0
        score = clamp(85.0 + diff * 2.0 if diff >= 0 else 85.0 + diff * 1.0, 60.0, 100.0)
        self.results["郵務營業收支比"] = {"score": score, "weight": 3}
        return score

    def calc_postage_net_revenue(self, current_net, last_year_net):
        if last_year_net == 0: return 85.0
        diff_pct = ((current_net - last_year_net) / last_year_net) * 100.0
        score = clamp(85.0 + diff_pct * 2.0, 60.0, 100.0)
        self.results["郵費收入淨額"] = {"score": score, "weight": 8}
        return score

    def calc_crm(self, bureau_tier, quarterly_data, current_special_rev, last_special_rev):
        tier_targets = {"特等": (50, 5), "一等甲": (50, 5), "一等乙": (40, 4), "二等甲": (30, 3), "二等乙": (20, 2)}
        total_target, pot_target = tier_targets.get(bureau_tier, (40, 4))
        q_scores = []
        for total_visited, pot_visited in quarterly_data:
            pot_diff = pot_visited - pot_target
            total_diff_pct = ((total_visited - total_target) / total_target) * 100.0
            q_score = clamp(85.0 + (pot_diff * 0.5) + (total_diff_pct * 1.0), 60.0, 100.0)
            q_scores.append(q_score)
        score_a = sum(q_scores) / len(q_scores) if q_scores else 85.0
        growth_b = ((current_special_rev - last_special_rev) / last_special_rev) * 100.0 if last_special_rev else 0.0
        score_b = clamp(85.0 + growth_b * 1.0, 60.0, 100.0)
        score = score_a * 0.60 + score_b * 0.40
        self.results["客戶關係管理"] = {"score": score, "weight": 2}
        return score

    def calc_mail_delivery_volume(self, curr_weight_pts, past3_avg_weight_pts):
        if past3_avg_weight_pts == 0: return 85.0
        diff_pct = ((curr_weight_pts - past3_avg_weight_pts) / past3_avg_weight_pts) * 100.0
        score = clamp(85.0 + diff_pct * 1.0, 70.0, 100.0)
        self.results["郵件投遞量"] = {"score": score, "weight": 3}
        return score

    def calc_ibox_promotion(self, slots_count, send_count, take_count, violations_count=0):
        def get_sub_score(actual, target):
            if target == 0: return 80.0
            diff = (actual / target) * 100.0 - 100.0
            return clamp(80.0 + (diff * 2.0 if diff >= 0 else diff * 1.0), 60.0, 100.0)
        s_send = get_sub_score(send_count, slots_count * 37)
        s_take = get_sub_score(take_count, slots_count * 27)
        score = clamp(((s_send + s_take) / 2.0) - violations_count * 0.5, 60.0, 100.0)
        self.results["i郵箱業務推廣"] = {"score": score, "weight": 2}
        return score

    def calc_philately_revenue(self, a_act, a_tgt, b_act, b_tgt, c_act, c_tgt):
        rate_a = min((a_act / a_tgt) * 100.0 if a_tgt else 100.0, 120.0)
        rate_b = min((b_act / b_tgt) * 100.0 if b_tgt else 100.0, 120.0)
        rate_c = min((c_act / c_tgt) * 100.0 if c_tgt else 100.0, 120.0)
        score = clamp(90.0 + ((rate_a * 0.8 + rate_b * 0.1 + rate_c * 0.1) - 100.0) * 1.5, 60.0, 100.0)
        self.results["集郵總收入"] = {"score": score, "weight": 3}
        return score

    def calc_ebanking_users(self, net_act, net_tgt, mobile_act, mobile_tgt):
        rate_a = min((net_act / net_tgt) * 100.0 if net_tgt else 100.0, 120.0)
        rate_b = min((mobile_act / mobile_tgt) * 100.0 if mobile_tgt else 100.0, 120.0)
        score = clamp(80.0 + ((rate_a * 0.4 + rate_b * 0.6) - 80.0) * 1.0, 60.0, 100.0)
        self.results["網路/行動郵局新使用戶數"] = {"score": score, "weight": 2}
        return score

    def calc_savings_deposit(self, daily_avg_act, daily_avg_tgt, count_curr, count_prev):
        rate_a = (daily_avg_act / daily_avg_tgt) * 100.0 if daily_avg_tgt else 95.0
        score_a = clamp(80.0 + (rate_a - 95.0) * 1.0, 60.0, 100.0)
        diff_b_pct = ((count_curr - count_prev) / count_prev) * 100.0 if count_prev else 0.0
        score_b = clamp(75.0 + (diff_b_pct / 0.1) * 1.0, 60.0, 100.0)
        score = score_a * 0.60 + score_b * 0.40
        self.results["存簿儲金"] = {"score": score, "weight": 4}
        return score

    def calc_alert_accounts(self, monthly_ratios, bureau_tier, pre_controls_count, post_releases_count):
        annual_a = sum([8.35 if r <= 1.0 else 6.85 if r <= 1.1 else 5.35 if r <= 1.2 else 5.0 for r in monthly_ratios])
        is_high_tier = bureau_tier in ["特等", "一等甲"]
        add_bonus = pre_controls_count * (0.4 if is_high_tier else 0.5)
        sub_penalty = post_releases_count * (0.2 if is_high_tier else 0.3)
        score = clamp(annual_a + add_bonus - sub_penalty, 60.0, 100.0)
        self.results["警示帳戶"] = {"score": score, "weight": 3}
        return score

    def calc_visa_debit_card(self, fee_act, fee_tgt, active_rate, issued_act, issued_tgt):
        score_a = clamp(80.0 + (((fee_act / fee_tgt) * 100.0 if fee_tgt else 100.0) - 100.0) * 1.0, 60.0, 100.0)
        score_b = clamp(80.0 + (active_rate - 50.0) * 1.0, 60.0, 100.0)
        rate_c = (issued_act / issued_tgt) * 100.0 if issued_tgt else 40.0
        score_c = clamp(60.0 + ((rate_c - 40.0) * 2.0 if (rate_c - 40.0) >= 0 else (rate_c - 40.0) * 1.0), 30.0, 100.0)
        score = score_a * 0.55 + score_b * 0.20 + score_c * 0.25
        self.results["郵政VISA金融卡"] = {"score": score, "weight": 4}
        return score

    def calc_mobile_payments(self, cloud_act, cloud_tgt, link_act, link_tgt):
        r_a = min((cloud_act / cloud_tgt) * 100.0 if cloud_tgt else 100.0, 110.0)
        r_b = min((link_act / link_tgt) * 100.0 if link_tgt else 100.0, 110.0)
        score = clamp(90.0 + ((r_a * 0.3 + r_b * 0.7) - 100.0) * 1.0, 60.0, 100.0)
        self.results["行動支付新使用戶數"] = {"score": score, "weight": 2}
        return score

    def calc_life_new_premium(self, actual, target):
        rate = (actual / target) * 100.0 if target else 75.0
        score = clamp(80.0 + (rate - 75.0) * 0.8, 60.0, 100.0)
        self.results["新契約保費收入"] = {"score": score, "weight": 7}
        return score

    def calc_long_term_protection_share(self, actual_premium, target_premium):
        rate = (actual_premium / target_premium) * 100.0 if target_premium else 40.0
        score = clamp(75.0 + (rate - 40.0) * 1.0, 50.0, 100.0)
        self.results["10年期以上保障型月保費占率"] = {"score": score, "weight": 4}
        return score

    def calc_online_life_contracts(self, web_act, web_tgt, mobile_act, mobile_tgt):
        score_a = clamp(80.0 + (((web_act / web_tgt) * 100.0 if web_tgt else 80.0) - 80.0) * 1.0, 60.0, 100.0)
        score_b = clamp(80.0 + (((mobile_act / mobile_tgt) * 100.0 if mobile_tgt else 80.0) - 80.0) * 1.0, 60.0, 100.0)
        score = score_a * 0.40 + score_b * 0.60
        self.results["網路投保及行動投保新契約件數"] = {"score": score, "weight": 2}
        return score

    def calc_micro_insurance(self, normal_rate, disabled_rate, met_august_target=True):
        avg_rate = (min(normal_rate, 120.0) + min(disabled_rate, 120.0)) / 2.0
        score = clamp(80.0 + (avg_rate - 80.0) * 1.0, 60.0, 100.0)
        score = score if met_august_target else score * 0.5
        self.results["微型傷害保險附約"] = {"score": score, "weight": 1}
        return score

    def calc_life_loan(self, interest_rate, mort_rate):
        score = clamp(80.0 + (interest_rate - 80.0) * 1.0, 60.0, 100.0) * 0.5 + clamp(80.0 + (mort_rate - 80.0) * 1.0, 60.0, 100.0) * 0.5
        self.results["保單借款利息及房貸新借款"] = {"score": score, "weight": 3}
        return score

    def calc_lapse_rate(self, bureau_lapse, global_lapse):
        diff = bureau_lapse - global_lapse
        steps = diff / 0.05
        score = clamp(80.0 + abs(steps) * 2.0 if steps <= 0 else 80.0 - steps * 1.0, 60.0, 100.0)
        self.results["契約脫落率"] = {"score": score, "weight": 2}
        return score

    def calc_asset_operation(self, goal_pct, curr_rent, prev_rent):
        rent_growth = ((curr_rent - prev_rent) / prev_rent) * 100.0 if prev_rent else 0.0
        score = clamp(80.0 + (goal_pct - 100.0) * 1.0, 70.0, 90.0) + clamp(5.0 + rent_growth * 1.0, 0.0, 10.0)
        self.results["資產營運收入"] = {"score": score, "weight": 2}
        return score

    def calc_ecommerce(self, agency_rate, ibox_shopping_rate):
        total_rate = min(agency_rate, 110.0) * 0.3 + min(ibox_shopping_rate, 110.0) * 0.7
        diff = total_rate - 90.0
        score = clamp(80.0 + (diff * 2.0 if diff >= 0 else diff * 1.0), 60.0, 100.0)
        self.results["電子商務"] = {"score": score, "weight": 2}
        return score

    def calc_occupational_safety(self, curr_freq, past3_avg_freq):
        score = clamp(80.0 - ((curr_freq - past3_avg_freq) / 0.1) * 0.5, 60.0, 100.0)
        self.results["職業安全"] = {"score": score, "weight": 1}
        return score

    def calc_legal_compliance(self, deductions):
        score = clamp(100.0 - deductions, 60.0, 100.0)
        self.results["法令遵循"] = {"score": score, "weight": 3}
        return score

    def set_audit_evaluation(self, risk_35, control_45, legal_audit_15, asset_2, follow_up_3):
        score = (risk_35 * 0.35 + control_45 * 0.45 + legal_audit_15 * 0.15 + asset_2 * 0.02 + follow_up_3 * 0.03)
        self.results["稽核考評"] = {"score": score, "weight": 5}
        return score

    def set_service_quality(self, unannounced_score, prompt_delivery_achieve_pct, culture_score):
        delivery_score = clamp(80.0 + ((prompt_delivery_achieve_pct - 98.0) / 0.2) * 2.0, 60.0, 100.0)
        score = (unannounced_score * 1.0 + delivery_score * 2.0 + culture_score * 2.0) / 5.0
        self.results["服務品質"] = {"score": score, "weight": 5}
        return score

    def set_comprehensive_evaluation(self, emergency_20, outside_concerns_20, main_errors_20, others_40):
        score = (emergency_20 * 0.20 + outside_concerns_20 * 0.20 + main_errors_20 * 0.20 + others_40 * 0.40)
        self.results["綜合考評"] = {"score": score, "weight": 5}
        return score

    def calculate_total_performance(self):
        total_weighted_score = sum(d["score"] * (d["weight"] / 100.0) for d in self.results.values())
        total_weight = sum(d["weight"] for d in self.results.values())
        return round(total_weighted_score, 3), total_weight


# ==========================================
# 2. Streamlit 網頁使用者介面 (UI)
# ==========================================
def main():
    st.set_page_config(page_title="郵政績效計算引擎", page_icon="📮", layout="wide")
    st.title("📮 年度套餐項目評分計算引擎")#郵政年度績效衡量項目評分計算引擎
    st.markdown("支援上下限夾擠 (Clamping)、各指標獨立計算、加權匯總。")

    # 初始化計算器
    calc = PostalPerformanceCalculator()

    # 利用 Tabs 建立分頁，讓畫面不至於太長
    tabs = st.tabs(["基礎營運與郵務", "儲匯與集郵", "壽險業務", "其他營運與考評", "📊 計算結果"])

    with tabs[0]:
        st.header("共同經營指標")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. 郵儲壽支出 (權數 8)")
            exp_act = st.number_input("實際支出", value=100.0, key="exp_a")
            exp_tgt = st.number_input("預算目標", value=100.0, key="exp_t")
            
            st.subheader("3. 特休實施率 (權數 1)")
            leave_taken = st.number_input("已休天數", value=55.0)
            leave_total = st.number_input("總天數", value=100.0)
        with col2:
            st.subheader("2. 用人費用 (權數 8)")
            pers_act = st.number_input("實際用人費用", value=100.0, key="pers_a")
            pers_tgt = st.number_input("預算目標", value=100.0, key="pers_t")

            st.subheader("4. 員工生產力 (權數 5)")
            prod_act = st.number_input("實際生產力", value=100.0, key="prod_a")
            prod_tgt = st.number_input("預算生產力", value=100.0, key="prod_t")
        
        st.divider()
        st.header("重點業務：郵務業務")
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("5. 郵務營業收支比 (權數 3)")
            mail_op_curr = st.number_input("本年收支比", value=1.0)
            mail_op_prev = st.number_input("上年收支比", value=1.0)

            st.subheader("8. 郵件投遞量 (權數 3)")
            deliv_curr = st.number_input("本年投遞量", value=100.0)
            deliv_prev = st.number_input("前3年平均量", value=100.0)

        with col4:
            st.subheader("6. 郵費收入淨額 (權數 8)")
            rev_curr = st.number_input("本年淨額", value=100.0)
            rev_prev = st.number_input("上年淨額", value=100.0)

            st.subheader("9. i郵箱業務推廣 (權數 2)")
            ibox_slots = st.number_input("格數", value=10)
            ibox_send = st.number_input("寄件數", value=370)
            ibox_take = st.number_input("取件數", value=270)
            ibox_viol = st.number_input("虛增違規次數", value=0)

        st.subheader("7. 客戶關係管理 (權數 2)")
        tier = st.selectbox("局等", ["特等", "一等甲", "一等乙", "二等甲", "二等乙"])
        st.write("請輸入四季拜訪數據 (總拜訪數, 潛在拜訪數)")
        q_data = []
        c1, c2, c3, c4 = st.columns(4)
        for i, col in enumerate([c1, c2, c3, c4]):
            with col:
                t_vis = st.number_input(f"Q{i+1} 總拜訪數", value=50, key=f"q{i}t")
                p_vis = st.number_input(f"Q{i+1} 潛在拜訪數", value=5, key=f"q{i}p")
                q_data.append((t_vis, p_vis))
        crm_curr = st.number_input("本年特約貢獻", value=100.0)
        crm_prev = st.number_input("去年特約貢獻", value=100.0)

    with tabs[1]:
        st.header("集郵與儲匯業務")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("10. 集郵總收入 (權數 3)")
            phil_a_act = st.number_input("集郵收入實際", value=100.0)
            phil_a_tgt = st.number_input("集郵收入目標", value=100.0)
            phil_b_act = st.number_input("個人化郵票實際", value=100.0)
            phil_b_tgt = st.number_input("個人化郵票目標", value=100.0)
            phil_c_act = st.number_input("降庫存實際", value=100.0)
            phil_c_tgt = st.number_input("降庫存目標", value=100.0)

            st.subheader("12. 存簿儲金 (權數 4)")
            save_avg_act = st.number_input("日平均結存實際", value=95.0)
            save_avg_tgt = st.number_input("日平均結存目標", value=100.0)
            save_cnt_act = st.number_input("結存戶數本年", value=100.0)
            save_cnt_prev = st.number_input("結存戶數去年", value=100.0)

        with col2:
            st.subheader("11. 網路/行動郵局用戶 (權數 2)")
            ebank_net_act = st.number_input("網郵實際", value=100.0)
            ebank_net_tgt = st.number_input("網郵目標", value=100.0)
            ebank_mob_act = st.number_input("行郵實際", value=100.0)
            ebank_mob_tgt = st.number_input("行郵目標", value=100.0)
            
            st.subheader("14. 郵政VISA金融卡 (權數 4)")
            visa_fee_act = st.number_input("手續費實際", value=100.0)
            visa_fee_tgt = st.number_input("手續費目標", value=100.0)
            visa_act_rate = st.number_input("累計啟動率(%)", value=50.0)
            visa_iss_act = st.number_input("核發實際", value=40.0)
            visa_iss_tgt = st.number_input("核發目標", value=100.0)

        st.subheader("13. 警示帳戶 (權數 3)")
        alert_str = st.text_input("12個月每月比較值(用逗號分隔)", value="1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0")
        try:
            alert_ratios = [float(x.strip()) for x in alert_str.split(",")]
        except:
            alert_ratios = [1.0] * 12
            st.warning("請確保填入 12 個數字並用逗號隔開。")
        alert_pre = st.number_input("前置管制戶數", value=0)
        alert_post = st.number_input("解除後警示戶數", value=0)

        st.subheader("15. 行動支付新使用戶數 (權數 2)")
        mp_cloud_act = st.number_input("雲支付實際", value=100.0)
        mp_cloud_tgt = st.number_input("雲支付目標", value=100.0)
        mp_link_act = st.number_input("綁定實際", value=100.0)
        mp_link_tgt = st.number_input("綁定目標", value=100.0)

    with tabs[2]:
        st.header("壽險業務")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("16. 新契約保費收入 (權數 7)")
            life_new_act = st.number_input("新契約實際", value=75.0)
            life_new_tgt = st.number_input("新契約目標", value=100.0)
            
            st.subheader("18. 網路及行動投保 (權數 2)")
            life_web_act = st.number_input("網路投保實際", value=80.0)
            life_web_tgt = st.number_input("網路投保目標", value=100.0)
            life_mob_act = st.number_input("行動投保實際", value=80.0)
            life_mob_tgt = st.number_input("行動投保目標", value=100.0)

            st.subheader("20. 保單借款及壽險房貸 (權數 3)")
            life_loan_int = st.number_input("保單借款達成率(%)", value=80.0)
            life_loan_mort = st.number_input("壽險房貸達成率(%)", value=80.0)

        with col2:
            st.subheader("17. 保障型商品月保費占率 (權數 4)")
            life_long_act = st.number_input("長保實際保費", value=40.0)
            life_long_tgt = st.number_input("長保目標保費", value=100.0)
            
            st.subheader("19. 微型傷害保險附約 (權數 1)")
            micro_norm = st.number_input("非身障達成率(%)", value=80.0)
            micro_dis = st.number_input("身障達成率(%)", value=80.0)
            micro_aug = st.checkbox("已達成 8 月底目標", value=True)

            st.subheader("21. 契約脫落率 (權數 2)")
            lapse_bur = st.number_input("局脫落率(%)", value=2.0, format="%.2f")
            lapse_glb = st.number_input("全區脫落率(%)", value=2.0, format="%.2f")

    with tabs[3]:
        st.header("其他營運業務、工安、法遵與考評")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("22. 資產營運收入 (權數 2)")
            asset_goal = st.number_input("年度目標達成率(%)", value=100.0)
            asset_curr = st.number_input("本年租金", value=100.0)
            asset_prev = st.number_input("上年租金", value=100.0)

            st.subheader("24. 職業安全 (權數 1)")
            safe_curr = st.number_input("本年職災頻率", value=1.0)
            safe_prev = st.number_input("前三年平均頻率", value=1.0)

            st.subheader("26. 稽接考評 (權數 5)")
            audit_risk = st.number_input("風險(35%)", value=100.0)
            audit_ctrl = st.number_input("內控(45%)", value=100.0)
            audit_legal = st.number_input("法遵稽核(15%)", value=100.0)
            audit_asset = st.number_input("資產(2%)", value=100.0)
            audit_fup = st.number_input("追蹤(3%)", value=100.0)

        with col2:
            st.subheader("23. 電子商務 (權數 2)")
            ecom_ag = st.number_input("代售手續費達成率(%)", value=90.0)
            ecom_ib = st.number_input("i郵購手續費達成率(%)", value=90.0)

            st.subheader("25. 法令遵循 (權數 3)")
            legal_deduct = st.number_input("各項法規扣分總和", value=0.0)

            st.subheader("27 & 28. 服務品質與綜合考評")
            sq_unann = st.number_input("為民服務不定期考核", value=80.0)
            sq_prompt = st.number_input("妥投率(%)", value=98.0)
            sq_cult = st.number_input("企業文化活動", value=80.0)
            
            comp_em = st.number_input("緊急事件(20%)", value=100.0)
            comp_out = st.number_input("外部關注(20%)", value=100.0)
            comp_err = st.number_input("重大缺失(20%)", value=100.0)
            comp_oth = st.number_input("其他(40%)", value=100.0)

    # 執行所有計算
    calc.calc_post_expenditure(exp_act, exp_tgt)
    calc.calc_personnel_cost(pers_act, pers_tgt)
    calc.calc_annual_leave_rate(leave_taken, leave_total)
    calc.calc_employee_productivity(prod_act, prod_tgt)
    calc.calc_mail_operating_ratio(mail_op_curr, mail_op_prev)
    calc.calc_postage_net_revenue(rev_curr, rev_prev)
    calc.calc_crm(tier, q_data, crm_curr, crm_prev)
    calc.calc_mail_delivery_volume(deliv_curr, deliv_prev)
    calc.calc_ibox_promotion(ibox_slots, ibox_send, ibox_take, ibox_viol)
    calc.calc_philately_revenue(phil_a_act, phil_a_tgt, phil_b_act, phil_b_tgt, phil_c_act, phil_c_tgt)
    calc.calc_ebanking_users(ebank_net_act, ebank_net_tgt, ebank_mob_act, ebank_mob_tgt)
    calc.calc_savings_deposit(save_avg_act, save_avg_tgt, save_cnt_act, save_cnt_prev)
    calc.calc_alert_accounts(alert_ratios, tier, alert_pre, alert_post)
    calc.calc_visa_debit_card(visa_fee_act, visa_fee_tgt, visa_act_rate, visa_iss_act, visa_iss_tgt)
    calc.calc_mobile_payments(mp_cloud_act, mp_cloud_tgt, mp_link_act, mp_link_tgt)
    calc.calc_life_new_premium(life_new_act, life_new_tgt)
    calc.calc_long_term_protection_share(life_long_act, life_long_tgt)
    calc.calc_online_life_contracts(life_web_act, life_web_tgt, life_mob_act, life_mob_tgt)
    calc.calc_micro_insurance(micro_norm, micro_dis, micro_aug)
    calc.calc_life_loan(life_loan_int, life_loan_mort)
    calc.calc_lapse_rate(lapse_bur, lapse_glb)
    calc.calc_asset_operation(asset_goal, asset_curr, asset_prev)
    calc.calc_ecommerce(ecom_ag, ecom_ib)
    calc.calc_occupational_safety(safe_curr, safe_prev)
    calc.calc_legal_compliance(legal_deduct)
    calc.set_audit_evaluation(audit_risk, audit_ctrl, audit_legal, audit_asset, audit_fup)
    calc.set_service_quality(sq_unann, sq_prompt, sq_cult)
    calc.set_comprehensive_evaluation(comp_em, comp_out, comp_err, comp_oth)

    # 結算與結果展示
    with tabs[4]:
        st.header("📈 計算結果總表")
        total_score, total_weight = calc.calculate_total_performance()
        
        st.metric("總加權得分", f"{total_score} 分", f"總計權數: {total_weight}%")
        
        # 將字典轉換為 DataFrame 顯示表格
        df_results = pd.DataFrame.from_dict(calc.results, orient="index")
        df_results.reset_index(inplace=True)
        df_results.columns = ["衡量指標", "單項得分 (Score)", "指標權重 (%)"]
        
        # 增加一欄計算該項的加權得分
        df_results["加權後分數"] = round(df_results["單項得分 (Score)"] * (df_results["指標權重 (%)"] / 100), 3)
        
        st.dataframe(df_results, use_container_width=True)

if __name__ == "__main__":
    main()
