# annual-leave-grant 變更紀錄

<!-- 只新增，不改舊紀錄；最新的在最上面。
     類型：凍結／回頭修改（第 0 級）／新增規則（第 1 級）／擴充模型（第 2 級）／改變意思（第 3 級）／專家回覆／升為已驗證
     每次凍結記一筆；凍結過的檔案被修改，每次都記；草稿階段不逐筆記。
     送審後到第一次凍結前：改變設計的修改逐筆記（新增、刪除、拆、合名詞、關係、狀態機、事件、規則、Use Case；
     範圍改變；推翻或取消 D-nn；改到其他步驟或切片）；整理性修改不逐筆記，在第一次凍結那一筆的「審查期間的修改」總結。

## <日期>　<tag 或（未凍結）>　<步驟>　<類型>
- 改了什麼：
- 依據：
- 舊 → 新：
- 影響與回歸：
- 產出者：；審查者：
-->

## 2026-10-22　annual-leave-grant/03-v4、annual-leave-grant/04-v3、annual-leave-grant/05-v3　③④⑤　凍結
- 改了什麼：⑥ 實作時發現的 22 項設計問題與平台約定 P4 的回頭修改（第 0 級）後重新凍結，內容見下方「（未凍結）③④⑤ 回頭修改（第 0 級）：⑥ 實作時發現的 22 項設計問題、平台約定 P4」那一筆。相對 03-v3：D-17、D-18（LeaveEntitlement 新增 ConfirmLeaveConversion 兩列，事件 RejudgeLeaveYearEnd、ConfirmLeaveConversion、NotifyLeaveReassessment 改寫，UC-12）；相對 04-v2：R66、R76、R83、R86、R87、R92、R97、C01、C02 改寫，參數改新格式、分類值新增 8 個（D-26～D-32）；相對 05-v2：D-23～D-35、api.yaml 0.2.0、schema.mongo.js、黃金案例 GC07～GC09
- 依據：06_evidence/signoff.md #1～#22（實作 @ af460ea）；docs/03 P4（工具包 @ 8df026a）
- 反例處理：這次沒有另開挑錯子代理，沒有新的 X-nn；修改來自 signoff 22 項
- 依審查重點登記同意的決定（審查者 JiHungLin，2026-10-22）：
  - 03_flows：D-18 依審查重點第 2 列同意（D-17 送審前已由使用者同意）
  - 04_rules：D-28 依第 2 列、D-26 依第 3 列、D-29 依第 4 列、D-30 依第 5 列、D-31 依第 6 列、D-32 依第 7 列同意（D-27 送審前已同意）
  - 05_mapping：D-33 依第 2 列、D-31 依第 3 列、D-32 依第 4 列、D-34 依第 5 列、D-27 依第 6 列、D-23～D-26、D-29、D-30、D-35 依第 7 列同意（D-28 送審前已同意）
- 黃金案例：GC07～GC09 預期結果由 JiHungLin 填寫；第一次凍結檢查時 GC08 ②（還可以休 0 → −1）、GC09 ①（有 → 沒有）、GC09 ③ 2026-03-15 的遞延出去（2 → 0）與設計不一致，計算者確認設計正確後改正預期結果（設計不用回頭）；紙上判定三筆都一致
- 審查方式：審查重點 ③ 3 列、④ 8 列、⑤ 9 列；寫成問題的 13 列回答「同意」；抽查由審查者自選（③ 狀態機、事件觸發來源；④ 分類值代碼、守恆式；⑤ Use Case 走一遍、紙上驗證）
- 合併進 core/：flows.md LeaveEntitlement 狀態機改 1 列、新增 2 列（ConfirmLeaveConversion），LeaveConversion Provisional → Determined 改寫，事件 RejudgeLeaveYearEnd、ConfirmLeaveConversion、NotifyLeaveReassessment 改寫，兩個狀態機與三個事件的出處改 03-v4；rules.md R66、R76、R83、R86、R87、R92、R97、C01、C02 改寫，出處改 04-v3，分類值新增 8 列 [候選]；沒有刪除項目，狀態仍是 [候選]
- 實作：impl/signoff-fixes 已依此版本修改（seed.py RULE_SET＝annual-leave-grant/04-v3），59 個測試通過；signoff「處理」欄補上新 tag，impl/README 的設計版本改為本版
- 產出者：AI（Claude）；審查者：JiHungLin（2026-10-22，通過）

## 2026-10-22　（未凍結）　③④⑤　回頭修改（第 0 級）：⑥ 實作時發現的 22 項設計問題、平台約定 P4
- 改了什麼：
  - ③ 03_flows.md：D-17 年度終結後才登錄或加大遞延協商，遞延進來的那一筆等扣回確認（ConfirmLeaveConversion）後才建立或增加（LeaveEntitlement 新增 ConfirmLeaveConversion 兩列，RejudgeLeaveYearEnd 那一列加前提；LeaveConversion Provisional → Determined、事件表 ConfirmLeaveConversion、RejudgeLeaveYearEnd 跟著改）；D-18 NotifyLeaveReassessment 的觸發來源補 EndLeaveEntitlementsWithEmployment。03_use_cases.md：UC-12 主流程與規則（加 R83、R87）
  - ④ 04_rules.md：R83 已年度終結的用「額度減已休」比（D-26）；R92 遞延加大要扣回時增加的部分等確認（D-27），R87、R92 套用對象加 ConfirmLeaveConversion；C01、C02 改寫（D-28）；R87、R97 取得日＝可休起日（D-29）；R76 看生效日與今天較晚的那天（D-30）；參數表改新格式：6 個可選做法寫代碼、2 個天數表寫「參數欄位」，分類值新增 8 個（D-31）；R66 v1 生效日以沒有下限表示（D-32）；R86 文字配合 C01
  - ⑤ 05_mapping.md：D-23～D-35（Superseded 的 discarded_by_id 可空、PERIOD_CHANGED_WITH_USED、已休從事件還原、basis_rule_versions 記哪幾條、Q01 篩選、今天依 P4、警告版本、訊息代碼表 2.3、3.2 新格式與 fixed_start_year_method 放公司規定、employer_settings 查哪一天、未來的結束日由排程執行、受影響的僱傭關係、存完整代碼）；D-03、D-10、D-12、D-18、D-21 加指向新決定的標註（內容不改）；1.1、1.2、1.3、第二節、3.1、3.2、第四節 P12、第六區 UC-12 跟著改。api.yaml 0.1.0 → 0.2.0；schema.mongo.js（payment_deadline_rule 完整代碼、fixed_start_year_method、NOTICE_ACTION 新代碼）
  - ⑤ 06_evidence/golden_cases.md：新增 GC07～GC09（情境與紙上推演由 AI 寫，預期結果待 JiHungLin）
  - questions.md：EQ-002、EQ-003、EQ-009 的「影響」追加
  - 三份交付物狀態 → 待檢查；受影響的完成標準重新自評；各加「審查重點（2026-10-22 回頭修改）」
- 依據：06_evidence/signoff.md「實作時發現的設計問題」#1～#22（實作 @ af460ea）；docs/03 P4 時間欄位與時區、docs/02 參數格式（工具包 @ 8df026a、5a98cab）；使用者 2026-10-22 決定 #16 採「確認後才建立」、#6 改成引用 P4、其餘照 AI 建議（第 0 級）
- 舊 → 新：
  - D-12「版本欄為『—』的規則填 annual-leave-grant/04-v1」→ 填規則所在的 04 凍結版本（05 D-29，推翻 D-12 這一部分）
  - 年度終結後才登錄遞延：遞延進來的那一筆立刻可以休 → 扣回確認後才建立（04 D-27、03 D-17）
  - C01「已年度終結的還可以休為 0」→ ＝待確認中的負數差額＋等確認的遞延（04 D-28）
  - R83 已年度終結的跟還可以休比 → 跟額度減已休比（04 D-26）
  - 未來的結束日：載入時就停止特休 → 到結束日那天由排程停止（05 D-33）
  - 「今天」：雇主所在管轄區的日期 → 依 P4，雇主所在地的當地日期（05 D-28）
- 影響與回歸：①② 不受影響，維持凍結；core/ 不受影響（③④ 改的是本切片 [候選] 的狀態轉換與規則，凍結時依 /domain-freeze 合併）。實作：impl/signoff-fixes 分支已依此改程式（seed、basis、engine、ledger、actions、scheduler、errors、clock），59 個測試通過；⑥ 要重跑 GC01、GC04、GC06 與新增的 GC07～GC09。hire-employee：「今天」的入口一起改（見 hire-employee CHANGELOG 同日那一筆）
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-21　annual-leave-grant/05-v2　⑤　凍結
- 改了什麼：lint 既有格式問題的回頭修改（第 0 級）後重新凍結，內容見「（未凍結）⑤ 回頭修改（第 0 級）：lint 抓到的既有格式問題」那一筆。相對 annual-leave-grant/05-v1：黃金案例 GC02、GC03、GC05 不採用、完成標準「已做紙上驗證」的自評補一句、新增「審查重點（2026-10-21 回頭修改）」。設計不變
- 依據：annual-leave-grant/05-v1；tools/lint.py（工具包 @ 8b5f2bd）；docs/02 ⑥
- 反例處理：無
- 審查方式：審查重點第 1 列打勾；抽查由審查者寫理由略過（「這次只改 golden_cases 的內容修復，不需要再跑 AI 自評」）
- lint --freeze 剩 1 個紅燈，使用者同意照樣凍結（2026-10-21）：core R52（hire-employee 的規則）套用對象「查看個資（hire-employee:UC-14、hire-employee:UC-15）」，lint 先濾掉其他切片的編號，剩下沒有編號而亮紅燈；是工具誤報，待工具包修 lint
- 合併進 core/：core/ 中 annual-leave-grant 的 48 處 Qnn、US-Dnn 加前綴（entities.md、flows.md、relations.md、rules.md R75）；內容不變、出處不變、仍為 [候選]
- 產出者：AI（Claude）；審查者：JiHungLin（2026-10-21，通過）

## 2026-10-21　（未凍結）　⑤　回頭修改（第 0 級）：lint 抓到的既有格式問題
- 改了什麼：⑤ 06_evidence/golden_cases.md 沒挑的 GC02、GC03、GC05，「紙上判定」「判定」由 [未執行] 改為「不採用」，檔頭的挑選紀錄同步；05_mapping.md 完成標準「已做紙上驗證」的 AI 自評補一句，新增「審查重點（2026-10-21 回頭修改）」；狀態 → 待檢查。questions.md：EQ-002、EQ-006 的「影響」把「03_flows 推導的狀態」寫成段落全名「推導的狀態與預估」（lint 對不上）；EQ-009 補 04_rules R94。inputs/research 6 個條目的「用在」追加 annual-leave-grant（勞動契約與年資#06、#10，期間計算#02、#03，特別休假#03，請假#05；只追加；INDEX.md 請假、期間計算同步）
- 依據：tools/lint.py（工具包 @ 8b5f2bd）的 EQ 影響、黃金案例、用在檢查；docs/02 ⑥「候選與不採用」
- 凍結時一併套用到 core/（內容不變）：core/ 中沒有切片前綴的 Qnn、US-Dnn 依所在項目的出處加前綴，annual-leave-grant 的 48 處（entities.md LeaveType～LeaveConversion、flows.md 第 356、427 行附近的 US-D10、US-D01、relations.md、rules.md R75 的 US-D10）；hire-employee 的與 rules.md 守恆式表記在 hire-employee CHANGELOG 同日那一筆
- 舊 → 新：設計不變；lint 紅燈 7 → 4（剩下的都在 core/：R52 的 UC-14、UC-15 與守恆式表，凍結時清掉）
- 影響與回歸：沒有改設計；①～④ 維持凍結；還沒實作
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-21　annual-leave-grant/03-v3、annual-leave-grant/04-v2、annual-leave-grant/05-v1　③④⑤　凍結
- 改了什麼：
  - ⑤ 初版（05-v1）：05_mapping.md（集合 13 個：業務 8、固定資料 2、平台 3；事件 → API、Use Case → API、可更正欄位與可註銷事件；規則 R65～R99 與 C01、C02 的落實位置；參數放置；推導值與歷史需求；UC-01～UC-12 走一遍；決定 D-01～D-22）；schema.mongo.js（MongoDB 驗證規則與索引）；api.yaml（OpenAPI 3.1，24 個路徑、26 個操作、56 個格式）；06_evidence/golden_cases.md（候選 6 個，JiHungLin 挑 GC01、GC04、GC06 並填預期結果，紙上驗證 3 個一致）。
  - ③ 第三版（03-v3）相對 03-v2：D-16 公司規定內容登錄錯誤的修訂（CompanyPolicy 狀態機、事件、更正方式、UC-03）；告知狀態不判定隨僱傭關係結束、作廢的那一筆；通知列出已判定轉換的基準日或發給期限改變。
  - ④ 第二版（04-v2）相對 04-v1：D-22（R91、R92 公司規定修訂）、D-23（R90 發給期限由雇主擇一，新增參數 `wage_payment_lag_months`）、D-24（R81）、D-25（R92、R96）；EQ-014 答覆（R80、R90 從隔天算改為已確認，未答的移到 EQ-015）。
  - 逐筆見下方 2026-10-21 四筆未凍結紀錄。
- 依據：slices/annual-leave-grant/05_mapping.md @ annual-leave-grant/05-v1；03_flows.md、03_use_cases.md @ annual-leave-grant/03-v3；04_rules.md @ annual-leave-grant/04-v2；inputs/drafts/特休未休工資發給期限.md（推想，已接受為假設）
- 反例處理：⑤ 兩輪挑錯共 21 個（第一輪 9、第二輪 12），接受並修改 20、拒絕 1（X-14）、轉問專家 0；③④ 的修改來自 ⑤ X-03、X-15 與紙上驗證 GC04、GC06。schema.mongo.js、api.yaml 沒有另跑挑錯，只用程式核對結構與對照表一致。
- 審查期間的修改（⑤ 第一次凍結）：⑤ 在紙上驗證完成後才送審（2026-10-21），送審到凍結之間沒有整理性修改；凍結時把 D-01～D-03、D-05～D-18、D-20 的「提出／同意」依審查者勾選的審查重點與「全部同意」改為 JiHungLin。草稿期間改變設計的修改已逐筆記 4 筆（下方 2026-10-21 未凍結紀錄）。
- 決定：③ D-16、④ D-22～D-25、⑤ D-01～D-22 由 JiHungLin 於 2026-10-21 同意。
- 產出者：AI（Claude）；審查者：JiHungLin

## 2026-10-21　（未凍結）　③④⑤　回頭修改（第 0 級）：紙上驗證 GC04、GC06 發現的兩處
- 改了什麼：04_rules.md 新增 D-24（R81 與決策表：隨僱傭關係結束、作廢的那一筆不判定告知狀態）、D-25（R92、R96：已判定轉換的工資計算基準日或發給期限依新依據會不同時，不改轉換，列入通知原 → 新）；審查重點差異表加第 4、5 列。03_flows.md 推導的狀態表「告知狀態」列、事件表 NotifyLeaveReassessment 跟著改，審查重點差異表加第 2 列。05_mapping.md 新增 D-22、審查重點第 12 列；schema.mongo.js、api.yaml 的 `action_items[].kind` 新增 `NOTICE_ACTION.CONVERSION_DATES_CHANGED`
- 依據：06_evidence/golden_cases.md GC04（第一次推演不一致）、GC06（推演時發現）；JiHungLin 2026-10-21 同意：「可以，照你建議」「要排除，已離職並發給未休代金了，就不需要警告了」
- 舊 → 新：天數差額 0 時什麼都不記 → 列入通知交給人；離職後仍判定告知狀態 → 不判定
- 影響與回歸：③④ 已是「待檢查」，⑤ 是草稿，三步一起審查、一起凍結；core/flows.md、core/rules.md 在凍結時更新；monthly-payroll 接手補發或扣回時要看這類通知
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-21　（未凍結）　④　專家回覆：EQ-014（期限的日數從隔天算）
- 改了什麼：questions.md EQ-014 改為已回覆，新增 EQ-015（EQ-014 沒回答的：期限末日遇休息日、第一筆和滿 1 年那筆重疊）；04_rules.md R80、R90「從隔天算第 1 日」改為已確認，末日遇休息日改標 EQ-015；R69 改標 EQ-015；D-05、D-18 的依據跟著改；審查重點（2026-10-21 回頭修改）加第 3 列。06_evidence/golden_cases.md GC01、GC02 的專家確認欄跟著改
- 依據：EQ-014，JiHungLin（使用者，不是 HC）2026-10-21 引民法第 120 條回答「始日不算入」；引文的但書不在 inputs/research/期間計算.md #02 的原文摘錄中，以已存的原文為準
- 舊 → 新：從隔天算 [待專家確認: EQ-014] → 已確認（規則內容不變）；末日遇休息日、重疊 EQ-014 → EQ-015
- 影響與回歸：規則內容沒有改，⑤ 不受影響；GC01 ② 的預期結果（2025-10-01）和答覆不一致，請計算者複核；core/rules.md R69、R80、R90 在凍結時更新
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-21　（未凍結）　④　回頭修改（第 0 級）：年度終結轉為工資的發給期限由雇主擇一
- 改了什麼：04_rules.md R90 改寫（雇主擇一；採「契約約定的工資給付日」時是年度終結日所屬計薪期間的給付日）；參數 `payment_deadline_rule` 改為依雇主，新增參數 `wage_payment_lag_months`；新增 D-23；讀取的輸入加推想草稿；審查重點（2026-10-21 回頭修改）加第 2 列。連帶 05_mapping.md（草稿）D-21、1.1、3.2、審查重點第 11 列，schema.mongo.js `employer_settings` 多兩個欄位；06_evidence/golden_cases.md 共同前提補「每月 5 日發上一個月的工資」
- 依據：inputs/drafts/特休未休工資發給期限.md（使用者問其他 AI 的答覆，推想，JiHungLin 2026-10-21 接受為假設：「是問 AI 的，先當推想，照 1～3 做」）；EQ-003 ③ 仍待 HC 確認
- 舊 → 新：發給期限的做法全部雇主相同、採工資給付日時是年度終結日之後第一個給付日（GC01 會得 2026-03-05）→ 依雇主擇一、採工資給付日時是年度終結日所屬計薪期間的給付日（GC01 得 2026-04-05）
- 影響與回歸：④ 已是「待檢查」（上一筆），和 ③⑤ 一起凍結；core/rules.md R90 在凍結時更新；monthly-payroll 第 ④ 步定義計薪期間與給付日時要接手這兩個參數；其他切片還沒有引用 R90
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-21　（未凍結）　③④　回頭修改（第 0 級）：公司規定內容登錄錯誤的修訂
- 改了什麼：03_flows.md 新增 D-16；CompanyPolicy 狀態機 Effective → Effective（ReviseCompanyPolicy）前提加「修訂接著重新判定」，新增 Repealed → Repealed（ReviseCompanyPolicy，只限修訂）；事件表 ReviseCompanyPolicy 的改變什麼、ReassessLeaveEntitlements 與 RejudgeLeaveYearEnd 的觸發來源加上公司規定版本的修訂；更正方式「公司規定」列與 CompanyPolicy 說明改寫；03_use_cases.md UC-03 例外、事件、規則。04_rules.md 新增 D-22，R91、R92 加修訂的處理；回填紀錄補一行
- 依據：05_mapping.md X-03、X-15、D-19（JiHungLin 2026-10-21 同意：「三件事都照你的建議」）
- 舊 → 新：版本內容登錄錯誤「由第 ④ 步決定」（未決定）→ 修訂是依據更正，重新判定已給予與已年度終結的
- 影響與回歸：③ 03-v2、④ 04-v1 改回「待檢查」，只審差異，和 ⑤ 一起凍結（03-v3、04-v2、05-v1）；core/flows.md、core/rules.md 的對應內容在凍結時更新；其他切片還沒有引用這些候選項目
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-21　annual-leave-grant/03-v2、annual-leave-grant/04-v1　③④　凍結
- 改了什麼：
  - ④ 初版（04-v1）：規則 35 條（R65～R99；前提條件 14、計算 11、判定 10），分取得日與天數、公司多給、告知、遞延協商、年度終結、重新判定與待確認、補登與資料一致、合併年資警告八組；決策表 6 張（R67、R68、R79、R81、R85、R93）；守恆式 2 條（C01、C02）；參數 17 個；分類值 26 個；決定 D-01～D-21。
  - ③ 第二版（03-v2）相對 03-v1：56 個狀態轉換的「規則」欄與 UC-01～UC-12 的「規則」回填；D-04 重新判定的新舊對應改為「同一來源、同一期別，而且新舊可休期間有重疊」；LeaveEntitlement 三列就地更正的前提、UC-08 主流程同步；LeaveConversion 兩列 CloseLeaveYear 的前提改為「補做的年度終結」看判定日；LeaveDeferralAgreement Lapsed → Agreed 改看狀態（逐筆見下方 2026-10-20 的回頭修改紀錄）。
- 依據：slices/annual-leave-grant/04_rules.md @ annual-leave-grant/04-v1；03_flows.md、03_use_cases.md @ annual-leave-grant/03-v2；inputs/research 特別休假 #01～#04、勞動契約與年資 #05、#07、#08、期間計算 #02、#03
- 反例處理：④ 兩輪挑錯共 31 個（第一輪 19、第二輪 12），全部接受並修改，沒有拒絕或轉問專家；③ 的修改來自 ④ 的 X-06、X-20、X-23、X-31。
- 決定：③ D-04 與 ④ D-01～D-21 由 JiHungLin 於 2026-10-21 同意。
- 審查期間的修改（④ 第一次凍結）：送審後沒有再修改內容，審查者只填寫審查重點、抽查與結論；送審前改變設計的修改已逐筆記 2 筆（2026-10-20 的 ③ 回頭修改、questions.md）。
- 仍待處理：規則與參數全部 [未核對]；引用的 research 條目原文也都 [未核對]；[待專家確認] 涉及 EQ-002、003、005、006、009、011～014，EQ 全部「待問」。
- 產出者：AI（Claude）；審查者：JiHungLin

## 2026-10-20　（未凍結）　③　回頭修改（第 0 級）：第 ④ 步回填規則與挑錯後調整
- 改了什麼：03_flows.md 狀態轉換的「規則」欄回填 56 列（CompanyPolicy 的 Establish、Activate、Repeal、Expire 4 列另加 R76）；03_use_cases.md UC-01～UC-12 的「規則」回填。挑錯後修改：D-04 重新判定的新舊對應由「同一來源、同一可休期間」改為「同一來源、同一期別，而且新舊可休期間有重疊」，提出／同意改回 AI／待確認；LeaveEntitlement 三列就地更正的前提、UC-08 主流程同步；LeaveConversion（無）→ Determined、（無）→ Provisional 兩列 CloseLeaveYear 的前提改為「補做的年度終結、公司多給失效、找不到版本」先待確認；LeaveDeferralAgreement Lapsed → Agreed 改看狀態。兩份狀態改回「待檢查」，03_flows.md 加「審查重點（2026-10-20 回頭修改）」
- 依據：04_rules.md「回填紀錄」；04_rules.md X-06、X-20、X-23、X-31、D-15、D-20
- 舊 → 新：D-04「同一可休期間」→「同一期別＋期間重疊」；補做年度終結的判斷由「由重新判定新增」→「判定日晚於可休迄日的隔天」
- 影響與回歸：③ 要重新審查差異並重新凍結（annual-leave-grant/03-v2），和 ④ 一起；core/flows.md 的對應內容在凍結時更新；其他切片還沒有引用這些候選項目
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-20　（未凍結）　①②③　回頭修改（第 0 級）：questions.md 新增 EQ-014、更新 EQ-012 與影響欄
- 改了什麼：新增 EQ-014（告知期限、發給期限的日數從哪天算、末日遇休息日；週年制第一筆可休期間和滿 1 年那筆重疊）；EQ-012 的「這版的做法」改為就地更正、告知日留在原來那一筆；EQ-002、003、005～009、011～013 的「影響」欄加上 04_rules 的規則、決策表、參數與決定
- 依據：04_rules.md X-02、X-16、X-21、X-27、X-31
- 舊 → 新：專家問題 13 題 → 14 題
- 影響與回歸：無；EQ 都還沒送出
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-20　（未凍結）　①②③　回頭修改（第 0 級）
- 改了什麼：questions.md 的「影響」欄，EQ-001～EQ-013 依實際的 `[待專家確認]` 標記補齊，加上檔名前綴（01_scope、02_entities、03_flows、03_use_cases）；決定或事件依賴答案、但內文沒有加標記的，另列「內文未標」：03_flows D-01、D-02、D-05、D-10、D-12、ConfirmLeaveConversion、EndLeaveEntitlementsWithEmployment、推導的狀態（告知狀態），以及會用到答案的其他切片
- 依據：使用者要求確認答覆回來時能不能找全受影響的地方；原本的「影響」欄只寫了提出那一步的項目，之後各步新增的引用沒有回填
- 舊 → 新：只改 questions.md 的「影響」欄；交付物的內文、設計都沒有改，「內文未標」的地方沒有補標記（補標記要改已凍結的 01～03，等答覆回來處理時一起改）
- 影響與回歸：無；/domain-expert-reply 比對答覆時以「影響」欄為準
- 產出者：AI（Claude）；審查者：（使用者要求，未另行審查）

## 2026-10-20　annual-leave-grant/03-v1　③　凍結
- 改了什麼：初版。狀態機 6 個：LeaveEntitlement（請假權利：Active、YearEnded、EndedWithEmployment、Voided；需要重建當時）、LeaveDeferralAgreement（遞延協商：Agreed、Applied、Withdrawn、Lapsed；需要重建當時）、LeaveYearAgreement（特休年度約定：Scheduled、Effective、Superseded、Ended；需要軌跡）、CompanyPolicy（公司規定：Scheduled、Effective、Repealed；需要重建當時）、LeaveConversion（請假權利轉換：Provisional、Determined、Discarded；需要重建當時）、LeaveType（假別：只需現況，不設事件）；告知狀態、之後各期的預估、法規警告是推導的，不是狀態機（D-09）；新增事件 20 個（建議層 1 個：NotifyLeaveReassessment），沿用 core 的 CorrectRecord、AnnulEntry、RevokeAnnulment、OverrideWarning、WithdrawWarningOverride，不修改 hire-employee 的內容（D-08）；決策流程 5 個；更正方式 9 列；正式 Use Case 12 個（UC-01～UC-12），草稿 US-D01～US-D11 都有涵蓋；決定 D-01～D-15；專家問題新增 EQ-011～EQ-013（待問）
- 依據：01_scope.md @ annual-leave-grant/01-v1；02_entities.md @ annual-leave-grant/02-v1；core/ @ 9c729ce；docs/03 P1、P2、P4；inputs/research/特別休假.md #01～#04
- 反例處理：X-01～X-15 共 15 個，來源都是 AI 挑錯（另開 context 的挑錯子代理）；接受並修改 14 個（最大的改動：更正、註銷、較晚得知造成的扣回與重新判定後補做的年度終結，先停在待確認，由人資確認後才交給薪資，D-11），轉問專家 1 個（X-08 → EQ-013），拒絕 0 個
- 審查期間的修改：送審後沒有修改設計；整理性修改 1 處：D-01～D-15 的「提出／同意」由「AI／待確認」改為「AI／JiHungLin（2026-10-20）」（審查重點第 1～8 列涵蓋全部 D-nn，審查者逐列打勾）。同一段期間地圖新增切片 event-leave（PLAN.md D-39，記在 slices/CHANGELOG.md），不影響本步
- 產出者：AI（Claude）；審查者：JiHungLin（2026-10-20，審查重點 9 列與抽查：每個事件標了觸發來源、由人觸發的標了誰有權觸發；需要判斷的地方有決策流程，系統或 AI 的建議不直接改變狀態）

## 2026-10-19　annual-leave-grant/02-v1　②　凍結
- 改了什麼：初版。引用 core 的 7 個 Entity（Tenant、Person、Employer、Jurisdiction、Employment、EmploymentContract、WarningOverride），都不修改；新增 6 個 Entity：LeaveType（假別，參考資料）、CompanyPolicy（公司規定：特休加給、特休年度預設）、LeaveYearAgreement（特休年度約定，週年制或固定起始日的年度）、LeaveEntitlement（請假權利，以「一筆」為單位、額度有單位；依規則給予的是取得時凍結的事實，D-03）、LeaveDeferralAgreement（遞延協商，一筆對一筆）、LeaveConversion（請假權利轉換：轉為工資或失效，已交給薪資的不改、更正記差額，D-06）；關係 17 條；「不是 Entity」約 30 列（餘額類都是推導值，事件交第 ③ 步、規則資料交第 ④ 步）；決定 D-01～D-18；變更提案：無。專家問題 EQ-002 追加一題，新增 EQ-009、EQ-010（待問）。全局名詞草圖新增 3 個名詞、調整 4 列（記在 slices/CHANGELOG.md）
- 依據：01_scope.md @ annual-leave-grant/01-v1；core/ @ ca04a27；slices/ENTITY_SKETCH.md、slices/PLAN.md @ ca04a27（D-09、D-15、D-27、D-28、D-31、D-38）；docs/03 P2、P3、P5、P11；inputs/research/特別休假.md #01～#04
- 反例處理：X-01～X-19 共 19 個，來源都是 AI 挑錯（另開 context 的挑錯子代理兩輪：X-01～X-11、X-12～X-19）；接受並修改 17 個，轉問專家 2 個（X-07 → EQ-002、X-10 → EQ-010），拒絕 0 個
- 審查期間的修改：送審後沒有逐筆記的修改（沒有改變設計）；整理性修改 1 處：D-01～D-18 的「提出／同意」由「AI／待確認」改為「AI／JiHungLin（2026-10-19）」（使用者在對話中同意）
- 產出者：AI（Claude）；審查者：JiHungLin（2026-10-19，審查重點 9 列與抽查：每張新卡都有「不是什麼」「不能跟誰合併」「主要屬性」，每個新增的 Entity 至少被一條驗收問題用到）

## 2026-10-19　annual-leave-grant/01-v1　①　凍結
- 改了什麼：初版。範圍：依年資給予特休（勞基法第 38 條天數表），週年制或曆年制依每位員工與雇主的約定、雇主可登記預設（D-12）；公司多給只做「在取得法定特休的同一天多給」（D-13）；告知員工排定特休的 30 日期限與實際告知日；年度終結時未休天數遞延或轉為工資的判定（算到天數、依哪個年度終結計算、發給期限；金額與每年書面通知歸 monthly-payroll，PLAN.md D-38）；年度終結之前就離職的交給 resignation（D-15）；例外：補登員工、到職日更正、未滿 6 個月離職；依法應合併的年資只對一種情況警告（D-11），由 seniority-recognition 補上；留職停薪由 leave-of-absence 補上（D-07）。模式完整，大小剛好；草稿 User Story 11 個（例外 6 個，全部由 AI 撰寫）、驗收問題 14 條（P0 5 條，全部待專家確認）、決定 D-01～D-15、專家問題 EQ-001～EQ-008（待問）
- 依據：slices/PLAN.md（annual-leave-grant 列、D-36、D-37、D-38）；inputs/annual-leave-grant/範圍釐清_第一次.md、範圍釐清_原文對照修正.md；inputs/shared/ 的範圍釐清檔（P-01、補登員工、更正不需核准、法規警告不阻擋、年資合併切片、留職停薪切片、年度終結未休工資歸屬）；inputs/research/特別休假.md #01～#04、勞動契約與年資.md #04～#08、#10、期間計算.md #02、#03、請假.md #05、#14
- 反例處理：X-01～X-35 共 35 個，來源都是 AI 挑錯（X-01～X-10 送審前；X-11～X-22 使用者要求逐條對照原文後由 AI 找到；X-23～X-33 由另開 context 的挑錯子代理找到；X-34、X-35 使用者審查後要求再分析），全部接受並修改
- 審查期間的修改：送審後逐筆記的有 8 筆（本檔下方 2026-10-19 的回頭修改：D-07、D-11 的後續切片 2 筆；D-12、D-13、D-14 各 1 筆；D-07／D-11 依原文改寫 1 筆；對照原文的其他更正 1 筆；挑錯子代理反例 1 筆）。沒有逐筆記的整理性修改約 15 處，主要是把改寫的法條改回原文引用並標解讀、更正引用來源、同步前幾輪修改留下的舊說法（X-21、X-34、X-35）；審查重點表依使用者決定合併成一張（不另列差異表）；切片地圖與名詞草圖的連帶修改記在 slices/CHANGELOG.md（D-36、D-37、D-38）
- 產出者：AI（Claude）；審查者：JiHungLin（2026-10-19，審查重點 13 列與抽查：模式判定、草稿 User Story 數量與例外）

## 2026-10-19　（未凍結）　①　回頭修改（第 0 級）
- 改了什麼：處理挑錯子代理的反例 X-23～X-33。設計上的改變：新增 D-15（年度終結之前就離職的，本切片不做年度終結判定，當期與遞延過來的未休天數交給 resignation）；D-11 改回「seniority-recognition 做完後，已給予的特休依合併後的年資重新判定」（X-23）；D-12 拿掉實務斷言，預設要看得出是套用的（X-26）；Q03 來源由客戶端使用者改為法規（X-27）；「範圍外但會用到」的 hire-employee 列加入勞動契約（X-30）。其餘為引用更正與補充（X-28、X-29、X-31、X-32、X-33），EQ-002、EQ-006、EQ-007 同步
- 依據：子代理挑錯（領域實務角度）；inputs/research/特別休假.md #01、#03、勞動契約與年資.md #04、#10、期間計算.md #02；slices/PLAN.md seniority-recognition、leave-of-absence、monthly-payroll 列；slices/hire-employee/01_scope.md D-21
- 舊 → 新：更正前一筆紀錄的錯誤：前一筆寫「切片地圖不用改（D-36、D-37 原本就沒有寫重新判定）」，只查了 D-36 那一列；地圖 seniority-recognition 列的情境已寫「已給予的特休依合併後的年資重新判定」，D-11 改回和地圖一致
- 影響與回歸：切片地圖可能要改（X-22、X-24：年度終結的未休工資、每年書面通知目前沒有切片負責；本切片會碰到人資／薪資），待使用者決定；第 ② 步要更新 ENTITY_SKETCH 的特休年度寫法（X-33）
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-19　（未凍結）　①　回頭修改（第 0 級）
- 改了什麼：對照原文的其他更正：遞延天數的工資基準改引用勞基法施行細則第 24-1 條原文，交給薪資切片的內容標解讀（X-15）；守恆式註明法定特休不會過期，「過期」只用在公司多給的部分（X-19）；「十年以上每一年加給一日」標解讀，EQ-006 新增第 ⑥ 題（X-20）；EQ-002 拿掉替專家回答的滿 6 個月日期（X-14）
- 依據：使用者要求逐條對照原文（上一個 session 發現多處幻覺）；inputs/research/特別休假.md #01、#03
- 舊 → 新：寫得像原文的改寫 → 引用原文並把 AI 的解讀標出來；範圍不變
- 影響與回歸：第 ② 步未開始；之後第 ④ 步的天數表、工資基準規則依 EQ-006、EQ-003 的答覆定
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-19　（未凍結）　①　回頭修改（第 0 級）
- 改了什麼：D-07、D-11 改寫。D-11：勞基法第 10 條引用原文全文，警告只對「同一雇主的前一段僱傭關係結束後未滿三個月又到職」這一種系統看得出的情況，條文沒有的「同一雇主」標解讀，拿掉「警告成本低」的理由（X-12、X-13）；D-07：拿掉「留停的員工可能多給特休」的預設，補上兩種留停的條文（X-16）；兩者都拿掉「那條切片做完後重新判定」，改為由那條切片的第 ① 步決定（X-18）。「做」「不做」、Q02、EQ-007 同步
- 依據：inputs/research/勞動契約與年資.md #05、請假.md #05、#14；slices/hire-employee/01_scope.md D-12；PLAN.md D-36、D-37
- 舊 → 新：§10 簡化成「回同一雇主」並寫得像原文 → 原文全文＋系統看得出的情況標解讀；替 seniority-recognition、leave-of-absence 定的範圍 → 交給那兩條切片決定
- 影響與回歸：本切片「做」「不做」、Q02、EQ-004、EQ-007；切片地圖不用改（D-36、D-37 原本就沒有寫重新判定）
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-19　（未凍結）　①　回頭修改（第 0 級）
- 改了什麼：新增 D-14：僱傭關係的結束日（一般離職）改列「範圍外但會用到」，歸 resignation，靜態替代；hire-employee 那一列拿掉結束日（X-13）
- 依據：slices/hire-employee/01_scope.md D-07、D-12（hire-employee 只記錄到職後立刻離開的結束日）；core/entities.md Employment；使用者同意（2026-10-19，建議 C）
- 舊 → 新：結束日直接引用 hire-employee → resignation 的靜態替代
- 影響與回歸：Q02、Q13、D-11 的警告；第 ② 步要把結束日當成外部提供的資料
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-19　（未凍結）　①　回頭修改（第 0 級）
- 改了什麼：新增 D-13：公司在法定門檻前預給的特休與預給天數的扣回，從「做」移到「不做」；US-D09、Q13、EQ-005 拿掉預給（X-17）
- 依據：inputs/shared/範圍釐清_P-01_優於法令.md、inputs/annual-leave-grant/範圍釐清_第一次.md（第 2 點）都沒有提預給；預給是 X-06 時 AI 自己加的；使用者同意（2026-10-19，建議 B）
- 舊 → 新：範圍做預給（扣回不做，但不做清單漏列）→ 預給與扣回都不做；公司多給只做「在取得法定特休的同一天多給」
- 影響與回歸：範圍縮小；X-06 的處理（加入預給）被這筆推翻
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-19　（未凍結）　①　回頭修改（第 0 級）
- 改了什麼：新增 D-12：週年制或曆年制改為每位員工依勞雇雙方的約定，雇主可以有預設做法，同一雇主的員工可以不同；「做」、Q03、Q14、US-D10、交給第 ② 步的觀察、EQ-002 同步（X-11）
- 依據：inputs/research/特別休假.md #02（勞基法施行細則第 24 條第 2 項「勞工得於勞雇雙方協商之下列期間內」）；使用者同意（2026-10-19，建議 A）
- 舊 → 新：雇主採用哪一種、雇主改制 → 每位員工適用哪一種、從哪天起，雇主可設預設
- 影響與回歸：第 ② 步的特休年度不能只掛在雇主身上
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-19　（未凍結）　①　回頭修改（第 0 級）
- 改了什麼：D-07 改寫：留職停薪由新切片 leave-of-absence 補上（PLAN.md D-37）；更正原本的理由「也沒有蒐集相關法規」（請假#05、#14 已蒐集，沒蒐集到的只有留停期間算不算年資）；「不做」清單與審查重點第 1、5 列同步
- 依據：審查時使用者指出 D-07 沒有寫後續；inputs/shared/範圍釐清_留職停薪切片.md
- 舊 → 新：先問 HC、再決定開切片或擴充 → 由 leave-of-absence（建議順序 12）補上；這版年資從到職日連續算的做法不變
- 影響與回歸：改到切片地圖（新增切片、順序 12～19 順延）；本切片其他內容不變
- 產出者：AI（Claude）；審查者：（待審查）

## 2026-10-19　（未凍結）　①　回頭修改（第 0 級）
- 改了什麼：D-11 改寫：依法應合併的年資由新切片 seniority-recognition 補上（PLAN.md D-36），不再寫「歸做年資合併的切片」；「不做」清單同步；審查重點第 1、5 列同步
- 依據：審查時使用者指出 D-11 沒有寫合併年資什麼時候補；inputs/shared/範圍釐清_年資合併切片.md
- 舊 → 新：歸 PLAN.md D-25 所說的切片（地圖上沒有）→ 由 seniority-recognition（建議順序 11）補上；這條切片在那之前的做法（§10 給警告、§20 不做）不變
- 影響與回歸：改到切片地圖（新增切片、順序 11～18 順延）；本切片其他內容不變
- 產出者：AI（Claude）；審查者：（待審查）
