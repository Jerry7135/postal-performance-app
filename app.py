import streamlit as st
import pandas as pd

# ==========================================
# 1. 核心計算邏輯 (您的原始程式碼)
# ==========================================
def clamp(val, min_v, max_v):
    """將數值限制在 [min_v, max_v] 區間"""
    return max(min_v, min(max_v, val))

class PostalPerformanceCalculator:
    def __init__(self):
        self.results = {}

    # (此處保留您的所有計算函式，為節省版面，邏輯皆與您提供的一致)
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
    st.title("📮 郵政年度績效衡量項目評分計算引擎")
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