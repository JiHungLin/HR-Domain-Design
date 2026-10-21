# annual-leave-grant ③ 流程與狀態

| 項目 | 內容 |
|---|---|
| 切片 | annual-leave-grant |
| 步驟 | ③ 流程與狀態 |
| 狀態 | 已凍結 |
| 版本 | annual-leave-grant/03-v3 |
| 產出者 | AI（Claude） |
| 讀取的輸入 | 01_scope.md @ annual-leave-grant/01-v1；02_entities.md @ annual-leave-grant/02-v1；core/ @ 9c729ce（hire-employee 的狀態機、事件與更正方式：CorrectRecord、AnnulEntry、RevokeAnnulment、OverrideWarning、Employment 的狀態）；docs/03 P1、P2、P4；inputs/research/特別休假.md #01～#04 @ 9c729ce |

**狀態怎麼來**（沿用 core 的做法，core/flows.md「狀態怎麼來」）：
- 每個狀態都由事件序列解釋（平台 P1）。由日期觸發的事件（取得日到達、年度終結、約定或公司規定開始適用、廢止生效）是依登錄的日期與其他事件**推導**出來的；它依據的日期或事件被更正、註銷時，重新推導。
- 但**依規則給予的特休與年度終結的判定，推導出來之後就是事實**（02_entities D-03、D-06）：重新推導不是把舊結果蓋掉，而是透過 ReassessLeaveEntitlements、RejudgeLeaveYearEnd 記下「改了什麼、因為什麼」，更正前的內容保留（D-04）。
- 只是值打錯用 core 的 CorrectRecord；整筆登錯用 core 的 AnnulEntry（本切片可註銷的事件見「更正方式」，D-08）。
- 更正、註銷、較晚得知造成的轉換，凡是對員工不利（負數差額）或依據還沒處理完（重新判定後才補做的年度終結），先停在「待確認」，人資確認後才交給薪資；正常的年度終結與補發的正數差額直接交給薪資（D-11）。

## 狀態機
<!-- 歷史需求：只需現況／需要軌跡／需要重建當時（依 Qnn）。「規則」欄第 ④ 步回填 -->

### LeaveEntitlement（請假權利）（歷史需求：需要重建當時，依 Q01、Q09、Q10、Q11）
狀態：Active（可休）→ YearEnded（已年度終結）／EndedWithEmployment（隨僱傭關係結束，交由契約終止處理）／Voided（已作廢）
終態：Voided、EndedWithEmployment（本切片的終態；之後由 resignation 依契約終止轉換）

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Active | GrantLeaveEntitlement | 系統 | 取得日到達（依年資與特休年度算出，Q02）；取得日不早於雇主開始由系統管理的日子（之前的由人補登，01_scope D-09）；當天系統已知的僱傭關係仍在職（之後才得知結束日早於取得日的，見 EndLeaveEntitlementsWithEmployment；結束日剛好是取得日見 EQ-006 ④）；這位員工在取得日有特休年度（個別約定或雇主預設；兩者都沒有時第 ④ 步決定，[待專家確認: EQ-002]）；法定一筆，符合公司規定的每條加給各一筆（02_entities D-02） | R65、R66、R67、R68、R69、R70、R71、R74、R77、R80、R99 |
| （無） | Active | RegisterExistingLeaveEntitlement | 人資 | 僱傭關係的到職日早於雇主開始由系統管理的日子；可休迄日不早於開始由系統管理的日子（那天仍可以休，01_scope D-09）；來歷是補登當期或補登遞延 | R97 |
| （無） | Active | CloseLeaveYear | 系統 | 遞延進來的那一筆：原來那一筆有一筆「已協商」的遞延協商；遞延進來的額度是協商額度與終結時未休兩者較小的，協商本身不改（D-12） | R86、R87 |
| （無） | Active | RejudgeLeaveYearEnd | 系統 | 遞延進來的那一筆：原來那一筆年度終結之後才登錄遞延協商（D-06） | R84、R87、R92 |
| （無） | Active | ReassessLeaveEntitlements | 系統 | 依新依據多出一期，和任何既有的一筆都對不上（D-04）；可休迄日已經過了的，進來之後立刻由 CloseLeaveYear 判定，轉換先停在待確認（D-11） | R91、R93 |
| Active | Active | ReassessLeaveEntitlements | 系統 | 依新依據仍有同一來源（同一條公司規定）、同一期別、而且新舊可休期間有重疊的一筆（④ R91），但額度、年資級別或依據不同：就地更正，更正前的內容保留（02_entities D-07）；遞延進來的那一筆，原來那一筆的年度終結日改變時，可休期間跟著更正 | R91 |
| Active | YearEnded | CloseLeaveYear | 系統 | 可休迄日（年度終結日）已經過完；系統已知的僱傭關係到那天仍在職（結束日剛好是年度終結日的情況見 [待專家確認: EQ-011]） | R85、R86、R88、R89、R90、R93 |
| Active | EndedWithEmployment | EndLeaveEntitlementsWithEmployment | 系統 | 僱傭關係的結束日早於可休迄日，且取得日不晚於結束日（01_scope D-15） | R85 |
| Active | Voided | EndLeaveEntitlementsWithEmployment | 系統 | 結束日較晚才得知，這一筆的取得日晚於結束日：其實從未取得（D-05） | R95 |
| Active | Voided | ReassessLeaveEntitlements | 系統 | 依新依據這一筆不再成立，也對不上新的任何一筆（D-04）；或建立它的事件被註銷（RegisterExistingLeaveEntitlement 的 AnnulEntry） | R91 |
| Active | Voided | RejudgeLeaveYearEnd | 系統 | 遞延進來的那一筆：遞延協商撤回，或修改成 0（D-06） | R92 |
| YearEnded | YearEnded | ReassessLeaveEntitlements | 系統 | 依新依據仍是同一來源、同一期別、新舊可休期間有重疊（④ R91），但額度或依據不同：就地更正，接著 RejudgeLeaveYearEnd 記轉換差額 | R91、R92 |
| YearEnded | YearEnded | RejudgeLeaveYearEnd | 系統 | 年度終結判定用到的資料之後改變：已休、遞延協商（修改、撤回、事後才登錄）、這一筆的額度（D-06） | R92、R93 |
| YearEnded | Active | ReassessLeaveEntitlements | 系統 | 依新依據，這一筆的可休迄日還沒到（例：到職日往後更正）；已做的轉換各記一筆負數差額（待確認，D-11） | R91、R93 |
| YearEnded | Voided | ReassessLeaveEntitlements | 系統 | 依新依據這一筆不再成立，或建立它的事件被註銷；已做的轉換各記一筆負數差額（待確認） | R91、R93 |
| YearEnded | Voided | EndLeaveEntitlementsWithEmployment | 系統 | 遞延進來的那一筆：年度終結判定之後才得知僱傭關係在原年度終結日之前就結束，那次年度終結其實沒有發生（D-05） | R95 |
| YearEnded | EndedWithEmployment | EndLeaveEntitlementsWithEmployment | 系統 | 年度終結判定之後才得知僱傭關係在年度終結日之前就結束；已做的轉換各記一筆負數差額（待確認），遞延進來的那一筆作廢，整筆交給 resignation（D-05） | R93、R95 |
| EndedWithEmployment | EndedWithEmployment | ReassessLeaveEntitlements | 系統 | 依新依據仍是同一來源、同一期別、新舊可休期間有重疊（④ R91），但額度或依據不同：就地更正；契約終止的轉換由 resignation 處理差額 | R91 |
| EndedWithEmployment | Active | ReassessLeaveEntitlements | 系統 | 僱傭關係的結束被註銷，或結束日更正到可休迄日之後；resignation 已做的契約終止轉換由 resignation 記負數差額（D-05） | R85、R91 |
| EndedWithEmployment | Voided | ReassessLeaveEntitlements | 系統 | 依新依據這一筆不再成立 | R91 |

說明：
- 「依規則給予」「遞延進來」「補登當期」「補登遞延」四種來歷用同一個狀態機；不同的是怎麼進到 Active，以及遞延進來與補登遞延的那筆不能再遞延（LeaveDeferralAgreement 的前提條件）。
- 補登的那筆是人登錄的事實，不參加重新判定的比對：依據更正時不會被系統作廢；和依規則重算的期間重疊或中間出現空檔時，由 NotifyLeaveReassessment 列出，人處理（D-04）。
- 需要重建當時：額度、期間、年資級別可能因依據更正而就地更正（02_entities D-07 要求標成需要重建當時），要回答「更正前給了什麼、當時依哪一版、誰在什麼時候改的」（Q09、Q11）；規則改版不觸發重新判定（02_entities D-03，Q10）。
- 作廢的那筆保留紀錄，不算進任何推導值（02_entities X-17）；上面已休的天數、告知日、遞延協商不自動搬到新的一筆，由 NotifyLeaveReassessment 列出，人處理（D-04）。
- 「告知」不是這個狀態機的狀態，是推導的（見「推導的狀態與預估」，D-09）。

### LeaveDeferralAgreement（遞延協商）（歷史需求：需要重建當時，依 Q05、Q06）
狀態：Agreed（已協商，待年度終結）→ Applied（已依它遞延）／Withdrawn（已撤回）／Lapsed（失效：要遞延的那一筆沒有進到年度終結）
終態：Withdrawn、Lapsed

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Agreed | RecordLeaveDeferral | 人資 | 要遞延的那一筆是 Active；來歷是依規則給予或補登當期（遞延進來、補登遞延的不能再遞延，特別休假#01 `[未核對]`）；那一筆沒有其他有效的遞延協商（02_entities D-05）；公司規定的那筆能不能延 [待專家確認: EQ-005]；遞延額度的上限第 ④ 步 | R82、R83、R98 |
| （無） | Applied | RecordLeaveDeferral | 人資 | 要遞延的那一筆已經 YearEnded（年度終結後才登錄）；登錄時間晚於年度終結日一律成立「年度終結後才登錄遞延協商」的警告（不論填的協商日是哪天）；協商日晚於年度終結日的算不算數 [待專家確認: EQ-003]，這版可以登錄、不阻擋；登錄後立刻 RejudgeLeaveYearEnd，減少工資的差額待確認（D-06、D-11） | R82、R84、R92、R98 |
| Agreed | Agreed | AmendLeaveDeferral | 人資 | 雙方重新協商（協商日、遞延額度改變），原內容保留 | R82、R83、R98 |
| Agreed | Withdrawn | WithdrawLeaveDeferral | 人資 | 雙方取消遞延；記撤回者、撤回時間、理由 | — |
| Agreed | Applied | CloseLeaveYear | 系統 | 要遞延的那一筆年度終結 | R86 |
| Agreed | Lapsed | EndLeaveEntitlementsWithEmployment | 系統 | 年度終結之前僱傭關係結束（未休的交給 resignation，01_scope D-15） | R85 |
| Agreed | Lapsed | ReassessLeaveEntitlements | 系統 | 要遞延的那一筆因重新判定而作廢 | R91 |
| Applied | Applied | AmendLeaveDeferral | 人資 | 年度終結後才重新協商 [待專家確認: EQ-003]；同樣成立「年度終結後才登錄」的警告；修改後 RejudgeLeaveYearEnd 更正遞延進來的那一筆並記轉換差額（D-06） | R82、R84、R92、R98 |
| Applied | Withdrawn | WithdrawLeaveDeferral | 人資 | 年度終結後才撤回 [待專家確認: EQ-003]；撤回後 RejudgeLeaveYearEnd：遞延進來的那一筆作廢，原來那一筆的未休改為轉為工資（差額） | R84、R92 |
| Applied | Lapsed | ReassessLeaveEntitlements | 系統 | 原來那一筆因重新判定而作廢；遞延進來的那一筆也作廢 | R91 |
| Applied | Lapsed | EndLeaveEntitlementsWithEmployment | 系統 | 年度終結判定之後才得知僱傭關係在原年度終結日之前就結束；遞延進來的那一筆作廢（D-05） | R95 |
| Lapsed | Agreed | ReassessLeaveEntitlements | 系統 | 讓它失效的原因被更正（僱傭關係的結束被註銷或結束日更正；那一筆恢復對應），而且那一筆還沒做過年度終結判定（看狀態，不看日期；之後補做年度終結時依恢復的協商遞延，④ X-23） | R91 |

說明：
- 需要重建當時，不只是需要軌跡：年度終結的判定依「判定當時已知的協商內容」做，之後協商被修改或撤回，要能說出判定當時是多少、差額是因為哪一次修改（Q05、Q06；雇主負舉證責任，勞基法第 38 條第 6 項，特別休假#01 `[未核對]`）。
- 「修改」和「更正」分開：雙方重新談是 AmendLeaveDeferral（協商日改變）；只是登錄時打錯是 CorrectRecord（協商日不變）。兩者都保留原內容（D-06）。
- 協商遞延的額度大於年度終結時的未休（例：談定延 3 天，之後又休了 2 天，只剩 2 天）：遞延進來的那一筆只建 2 天，協商仍記 3 天，成立「協商遞延額度超過未休」的警告（D-12）。

### LeaveYearAgreement（特休年度約定）（歷史需求：需要軌跡，依 Q03、Q14）
狀態：Scheduled（尚未適用）→ Effective（適用中）→ Superseded（已被下一筆取代）／Ended（已終止，之後回到雇主預設）
終態：Superseded、Ended

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Scheduled | RecordLeaveYearAgreement | 人資 | 適用起日在未來；同一段僱傭關係、同一假別同一天只有一筆有效（第 ④ 步） | R72、R98 |
| （無） | Effective | RecordLeaveYearAgreement | 人資 | 適用起日不在未來；適用起日早於已給予的特休的取得日時，觸發 ReassessLeaveEntitlements（D-10） | R72、R75、R98 |
| Scheduled | Effective | ActivateLeaveYearAgreement | 系統 | 適用起日到達 | R71、R75 |
| Effective | Superseded | ActivateLeaveYearAgreement | 系統 | 同一段僱傭關係、同一假別的下一筆約定開始適用 | R75 |
| Scheduled | Ended | EndLeaveYearAgreement | 人資 | 還沒適用就取消 | R98 |
| Effective | Ended | EndLeaveYearAgreement | 人資 | 雙方協商不再個別約定，之後套用雇主預設；終止日早於已給予的取得日時觸發 ReassessLeaveEntitlements | R75、R98 |

說明：
- 需要軌跡，不需要重建當時：「這位員工某天適用哪一種」由各筆約定的適用起日與終止日就看得出來（Q03）；每一筆特休給予時依哪一種已經凍結在那一筆上（`leave_year_basis` 與 appliedYearAgreement，02_entities D-04），所以約定本身只要知道誰、何時登錄或更正。
- 改用另一種的那一年怎麼換算是第 ④ 步的規則 [待專家確認: EQ-002]；已經給予的特休不因為改用另一種而改變（Q14、US-D10）。
- 僱傭關係結束時約定不另外轉換狀態：結束後不再給予，約定也不會再被用到。
- 雇主改了預設，沒有個別約定的員工之後就套用新的預設；年度是勞雇雙方協商的結果（01_scope D-12），所以預設改變時，對還在套用預設的員工成立警告，不同意的員工由人資替他登錄一筆維持原年度的約定（D-13）。工作規則改預設算不算協商 [待專家確認: EQ-002]。

### CompanyPolicy（公司規定）（歷史需求：需要重建當時，依 Q09、Q10）
狀態：Scheduled（尚未生效）→ Effective（生效中）→ Repealed（已廢止）
終態：Repealed

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Scheduled | EstablishCompanyPolicy | 人資或雇主（老闆） | 第一次生效日在未來；這版以固定資料提供 [靜態替代]（02_entities CompanyPolicy 卡） | R73、R78、R98 |
| （無） | Effective | EstablishCompanyPolicy | 人資或雇主（老闆） | 第一次生效日不在未來；早於已經給予的特休取得日時，觸發 ReassessLeaveEntitlements（補上那段期間應有的加給，D-14） | R73、R76、R78、R98 |
| Scheduled | Scheduled | ReviseCompanyPolicy | 人資或雇主（老闆） | 還沒生效前修改內容（新的版本） | R73、R78 |
| Scheduled | Effective | ActivateCompanyPolicy | 系統 | 第一次生效日到達 | R76 |
| Effective | Effective | ReviseCompanyPolicy | 人資或雇主（老闆） | 內容修改是同一條規定的新版本，有自己的生效日（版本是規則資料，第 ④ 步，平台 P5）；已經依舊版給予的特休不變（Q10）；年度終結時依哪一版處理見 [待專家確認: EQ-013]。版本內容登錄錯誤時新增一筆修訂（只限人資），是依據更正，接著 ReassessLeaveEntitlements、RejudgeLeaveYearEnd（D-16） | R73、R76、R78、R79、R91、R92 |
| Effective | Effective | RepealCompanyPolicy | 人資或雇主（老闆） | 登錄廢止，廢止日在未來（到那天由 ExpireCompanyPolicy 轉換） | R98 |
| Scheduled | Repealed | RepealCompanyPolicy | 人資或雇主（老闆） | 還沒生效就取消 | R98 |
| Effective | Repealed | RepealCompanyPolicy | 人資或雇主（老闆） | 廢止日不在未來；已經依它給予的特休不受影響 | R76、R98 |
| Effective | Repealed | ExpireCompanyPolicy | 系統 | 廢止日到達 | R76 |
| Repealed | Repealed | ReviseCompanyPolicy | 人資 | 只限修訂已登錄的版本內容（登錄錯誤）；依它給予的特休可能還在可休；接著 ReassessLeaveEntitlements、RejudgeLeaveYearEnd（D-16） | R73、R78、R91、R92 |

說明：需要重建當時：特休要能說出「依哪一條公司規定的哪一版」給的（Q09），公司規定改版或廢止後，已給予的依原版本（Q10）。公司規定本身的生效日、廢止日是登錄的事實，打錯更正時和到職日一樣觸發重新判定（D-14）；版本內容（多給幾天、適用對象、年度終結處理）登錄錯誤時新增一筆修訂，也是依據更正，觸發重新判定；改版（新的版本）不觸發（02_entities D-03，D-16）。

### LeaveConversion（請假權利轉換）（歷史需求：需要重建當時，依 Q05、Q08、Q11）
狀態：Provisional（待確認）→ Determined（已判定）／Discarded（未確認即被取代）
終態：Determined、Discarded

| 從 | 到 | 觸發事件 | 誰可以做 | 前提條件 | 規則 |
|---|---|---|---|---|---|
| （無） | Determined | CloseLeaveYear | 系統 | 正常的年度終結：那一筆年度終結時有未休額度，沒有遞延的部分轉為工資；公司規定的那筆依公司規定轉為工資（失效的見下一列，[待專家確認: EQ-005]）；遞延進來、補登遞延的那筆全部轉為工資，依原年度終結日計算（02_entities D-05） | R79、R86、R89、R90、R93 |
| （無） | Provisional | CloseLeaveYear | 系統 | 補做的年度終結：判定日晚於可休迄日的隔天（由重新判定新增、恢復，或就地更正後迄日變成過去；結束被註銷或延後後補做），已休、遞延協商還沒由人處理（D-11）；公司多給的轉為失效；公司多給的那一筆找不到依據的版本（④ R93） | R86、R93 |
| （無） | Determined | RejudgeLeaveYearEnd | 系統 | 更正差額，增加員工的工資（正數）：依更正後的資料重新判定，和已判定的總額不同；指回被更正的那一次，記更正原因（02_entities D-06） | R89、R90、R92、R93 |
| （無） | Provisional | RejudgeLeaveYearEnd | 系統 | 更正差額，減少員工的工資（負數）或改為失效（D-11） | R92、R93 |
| （無） | Provisional | ReassessLeaveEntitlements | 系統 | 更正差額：那一筆因重新判定而回到可休、作廢、額度改變，或建立它的事件被註銷、撤銷註銷 | R90、R91、R93 |
| （無） | Provisional | EndLeaveEntitlementsWithEmployment | 系統 | 負數差額：年度終結判定之後才得知僱傭關係在年度終結日之前就結束（D-05） | R90、R93、R95 |
| Provisional | Determined | ConfirmLeaveConversion | 人資 | 人資看過 NotifyLeaveReassessment 列出的事（已休、遞延協商、告知日），確認這一筆；確認後才交給薪資（D-11） | R94 |
| Provisional | Discarded | RejudgeLeaveYearEnd | 系統 | 確認前依據又改變，重新算出的取代它；被取代的保留紀錄 | R92 |
| Provisional | Discarded | ReassessLeaveEntitlements | 系統 | 確認前依據又改變，重新算出的取代它 | R91 |

說明：
- 已判定（Determined）的轉換不再改變（02_entities D-06）：已經交給薪資的那一批不能改，發現要更正時另記一筆差額（可以是負數，多發的怎麼處理 [待專家確認: EQ-009]）。每一筆轉換由哪一次判定產生、判定當時依哪些資料，要查得到（Q05、Q11）。
- 待確認（Provisional）的還沒交給薪資，所以可以被取代（Discarded）而不是記差額；被取代的保留紀錄。待確認期間發給期限照樣計算，確認晚於期限的成立警告（第 ④ 步）。

### LeaveType（假別）（歷史需求：只需現況，依 Q01）
狀態：Active（使用中）→ Deprecated（已停用）
終態：Deprecated

不設事件與轉換表：法令訂定的假別是全平台共用的參考資料（02_entities D-10、D-15），由平台維運直接維護；法令廢止時標為停用，不刪除，已經給予的請假權利照原意解讀（docs/01 0.2 第 1 級）。

說明：只需現況：驗收問題只問「這一筆是哪一種假」（Q01），沒有人問假別的名稱或代碼什麼時候改過；依 docs/01 ③「可以簡化的時候」不做事件（D-07）。公司自訂的假別由之後的切片定義，到時再判斷要不要事件。

## 推導的狀態與預估
<!-- 不是狀態機：不存、不由事件改變，依據改了就重算（D-09） -->

| 項目 | 可能的值 | 怎麼推出來 | 依哪條 Q |
|---|---|---|---|
| 一筆法定特休的告知狀態（只有依規則給予的法定特休；補登的不判定，01_scope D-09；隨僱傭關係結束、作廢的不判定，④ D-24） | 待告知（期限內）／已告知／逾期未告知／逾期後告知 | 取得日、告知期限（`notice_due_on`）、實際告知日（`notified_on`）與今天；告知日被更正過的看得出來（core CorrectRecord 保留原值）；逾期是法規警告，可以忽略（core OverrideWarning），不阻擋。符合條件之前就告知算不算數 [待專家確認: EQ-006]；曆年制一筆可能要告知兩次 [待專家確認: EQ-002] | Q07 |
| 還可以休的、已休、遞延出去、轉為工資、失效 | 數量 | 02_entities 的推導值；已休這版以固定資料提供 [靜態替代] | Q05、Q08 |
| 某天適用哪一種特休年度 | 週年制、曆年制（固定起始日的年度） | 當天有效的個別約定；沒有就用當天有效的雇主預設 | Q03 |
| 之後各期的預估（還沒取得的） | 預計取得日、天數、可休期間 | 依目前的到職日、特休年度與目前的規則版本試算；只是預估，不建立請假權利，取得日到達才由 GrantLeaveEntitlement 給予（D-01）；規則改版、到職日更正、改用另一種年度後預估會變 | Q01、Q02（US-D01） |
| 法規警告：告知逾期、可能應合併年資、曆年制換算少於法定、公司規定少於法定、年度終結後才登錄遞延協商（看登錄時間）、協商遞延額度超過未休、雇主預設的特休年度改變而員工還在套用預設、待確認的轉換超過發給期限 | 成立／不成立 | 依資料與規則推出，資料改正就消失；忽略時用 core 的 OverrideWarning（02_entities D-16）；判斷條件是第 ④ 步的規則 | Q02、Q05、Q07、Q14 |

## 事件
<!-- 觸發來源：人的動作／其他單位個體的變化／外部系統或訊息／時間或條件到達
     層：要求／建議／決定／發生／執行（「建議」層不改變狀態）
     有意義的時間：發生／得知／生效 -->

| 事件 | 觸發來源 | 層 | 主體 | 改變什麼 | 證據 | 能否撤銷 | 有意義的時間 |
|---|---|---|---|---|---|---|---|
| GrantLeaveEntitlement（給予特休） | 時間或條件到達（取得日到達，且系統已知的僱傭關係當天在職、取得日不早於開始由系統管理的日子） | 發生 | LeaveEntitlement | （無）→ Active；法定一筆，符合的公司加給各一筆；記下依據（規則版本、特休年度與它依據的約定或預設、取得日當時的年資、依據的到職日，02_entities D-03） | 到職日、特休年度約定或雇主預設、規則版本 | 不可撤銷；依據更正時由 ReassessLeaveEntitlements 重新判定 | 發生（取得日）、得知、生效（可休起日） |
| RegisterExistingLeaveEntitlement（補登仍可休的特休） | 人的動作（人資） | 發生 | LeaveEntitlement | （無）→ Active；登錄來源、來歷（補登當期或補登遞延）、額度、開始管理前已休、可休期間；補登遞延的另登原年度終結日（01_scope D-09） | 雇主原有的紀錄（例：既有的特休表） | 值用 CorrectRecord；整筆登錯用 AnnulEntry（觸發 ReassessLeaveEntitlements） | 發生（開始由系統管理的日子）、得知 |
| RecordLeaveNotice（登錄告知排定特休） | 人的動作（人資或雇主（老闆）） | 發生 | LeaveEntitlement | 不改變狀態；記實際告知日，告知狀態跟著重推 | 告知方式的說明（例：電子郵件、公告） | 值用 CorrectRecord（人資）；整筆登錯用 AnnulEntry（人資） | 發生（告知日）、得知 |
| RecordLeaveYearAgreement（登錄特休年度約定） | 人的動作（人資，依雙方協商的結果） | 決定 | LeaveYearAgreement | （無）→ Scheduled 或 Effective；適用起日早於已給予的取得日時觸發 ReassessLeaveEntitlements | 協商日、協商方式的說明（例：個別書面約定） | 值用 CorrectRecord；整筆登錯用 AnnulEntry；改用另一種是登錄新的一筆 | 發生（協商日）、得知、生效（適用起日） |
| ActivateLeaveYearAgreement（約定開始適用） | 時間或條件到達（適用起日到達） | 發生 | LeaveYearAgreement | Scheduled → Effective；同一段僱傭關係、同一假別的前一筆 Effective → Superseded | 適用起日 | 不可撤銷；適用起日更正時重新推導 | 生效 |
| EndLeaveYearAgreement（終止特休年度約定） | 人的動作（人資，依雙方協商的結果） | 決定 | LeaveYearAgreement | Scheduled 或 Effective → Ended；之後套用雇主預設；終止日早於已給予的取得日時觸發 ReassessLeaveEntitlements | 協商日、說明 | 值用 CorrectRecord；登錯用 AnnulEntry | 發生（協商日）、得知、生效（終止日） |
| EstablishCompanyPolicy（訂定公司規定） | 人的動作（人資或雇主（老闆）） | 決定 | CompanyPolicy | （無）→ Scheduled 或 Effective；第一版的內容（第 ④ 步的規則資料）；生效日早於已給予的取得日時觸發 ReassessLeaveEntitlements | 依據說明（例：工作規則第 12 條、公司公告） | 值用 CorrectRecord；整筆登錯用 AnnulEntry | 發生、得知、生效 |
| ReviseCompanyPolicy（修改公司規定） | 人的動作（人資或雇主（老闆）） | 決定 | CompanyPolicy | 不改變狀態；新增一個版本，有自己的生效日；已經依舊版給予的特休不變；事項為特休年度預設的，對還在套用預設的員工成立警告（D-13）；修訂（登錄錯誤，只限人資）觸發 ReassessLeaveEntitlements、RejudgeLeaveYearEnd（D-16） | 依據說明 | 版本內容要更正是新的修訂（平台 P5，D-16） | 發生、得知、生效 |
| ActivateCompanyPolicy（公司規定生效） | 時間或條件到達（第一次生效日到達） | 發生 | CompanyPolicy | Scheduled → Effective | 第一次生效日 | 不可撤銷；生效日更正時重新推導 | 生效 |
| RepealCompanyPolicy（廢止公司規定） | 人的動作（人資或雇主（老闆）） | 決定 | CompanyPolicy | 登錄廢止日；廢止日不在未來的 Scheduled 或 Effective → Repealed，在未來的到那天由 ExpireCompanyPolicy 轉換；已給予的特休不受影響 | 依據說明 | 值用 CorrectRecord；整筆登錯用 AnnulEntry | 發生、得知、生效（廢止日） |
| ExpireCompanyPolicy（公司規定廢止生效） | 時間或條件到達（廢止日到達） | 發生 | CompanyPolicy | Effective → Repealed | 廢止日 | 不可撤銷；廢止日更正時重新推導 | 生效 |
| RecordLeaveDeferral（登錄遞延協商） | 人的動作（人資，依勞雇雙方協商的結果） | 決定 | LeaveDeferralAgreement | （無）→ Agreed；年度終結後才登錄的 → Applied，並觸發 RejudgeLeaveYearEnd | 協商日、遞延額度、協商方式與憑據的說明（例：書面同意書） | 用 AmendLeaveDeferral 修改、WithdrawLeaveDeferral 撤回；打錯用 CorrectRecord | 發生（協商日）、得知 |
| AmendLeaveDeferral（修改遞延協商） | 人的動作（人資，依雙方重新協商的結果） | 決定 | LeaveDeferralAgreement | 不改變狀態（Agreed 或 Applied 不變）；改協商日與遞延額度，原內容保留；已 Applied 的觸發 RejudgeLeaveYearEnd | 新的協商日、憑據說明 | 可以再修改或撤回 | 發生（新的協商日）、得知 |
| WithdrawLeaveDeferral（撤回遞延協商） | 人的動作（人資，依雙方取消遞延） | 決定 | LeaveDeferralAgreement | Agreed 或 Applied → Withdrawn；已 Applied 的觸發 RejudgeLeaveYearEnd | 撤回理由 | 不可撤銷；要再遞延是新的一筆協商 | 發生、得知 |
| CloseLeaveYear（年度終結判定） | 時間或條件到達（一筆請假權利的可休迄日過完，且系統已知的僱傭關係到那天仍在職） | 發生 | LeaveEntitlement | 那一筆 Active → YearEnded；依「已協商」的遞延協商產生遞延進來的一筆（Active，額度見 D-12），協商 Agreed → Applied；其餘未休額度產生轉換（LeaveConversion：轉為工資，或公司規定的失效），記工資計算基準日與發給期限（02_entities D-06）；由重新判定新增的那一筆，轉換是待確認（D-11） | 判定當時已知的已休（記下當時的數字，D-15）、遞延協商的內容、規則版本 | 不可撤銷；判定用到的資料之後改變時由 RejudgeLeaveYearEnd 記差額 | 發生（年度終結日）、得知（判定日） |
| RejudgeLeaveYearEnd（重新判定年度終結） | 其他單位個體的變化（已年度終結的那一筆：已休改變（含這版固定資料的改正）、遞延協商修改、撤回或事後登錄、額度就地更正、依據的公司規定版本被修訂（D-16）） | 發生 | LeaveEntitlement | YearEnded 不變；遞延進來的那一筆新增、更正額度或作廢；轉換另記差額，指回被更正的那一次，記更正原因，負數的待確認（D-11）；待確認還沒確認的被取代；產生 NotifyLeaveReassessment | 改變了什麼、判定當時與現在的資料 | 不可撤銷；資料再改變時再重新判定 | 發生（年度終結日）、得知 |
| ReassessLeaveEntitlements（依據更正後重新判定特休） | 其他單位個體的變化（到職日更正；特休年度約定登錄、終止、更正或註銷；員工類型等決定適用哪一條公司規定的資料更正；公司規定的生效日、廢止日登錄或更正；公司規定版本內容的修訂（D-16）；僱傭關係的到職或結束被註銷、撤銷註銷；結束日更正；補登的特休被註銷或撤銷註銷） | 發生 | LeaveEntitlement | 依新依據重算每一期，和既有的依規則給予的逐筆對應（D-04）：對得上的就地更正（保留更正前內容；已年度終結的接著 RejudgeLeaveYearEnd）、對不上的作廢、多出來的新增；已年度終結的回到可休或作廢時，轉換記差額（待確認）；遞延協商依對應結果失效或恢復；產生 NotifyLeaveReassessment。規則改版不觸發（02_entities D-03） | 被更正的依據（更正前、更正後）、更正者 | 不可撤銷；依據再更正時再重新判定 | 發生（依據被更正的時間）、得知 |
| EndLeaveEntitlementsWithEmployment（僱傭關係結束，停止特休） | 其他單位個體的變化（系統得知僱傭關係 Active → Ended：core 的 RecordEarlyDeparture，或 resignation 定義的離職；這版一般離職以固定資料提供 [靜態替代]，載入結束日視同這個變化） | 發生 | LeaveEntitlement | 取得日不晚於結束日、可休迄日晚於結束日的每一筆 Active → EndedWithEmployment；取得日晚於結束日的（結束日較晚得知）→ Voided；年度終結判定之後才得知的，那一筆 YearEnded → EndedWithEmployment、遞延進來的那筆作廢、Applied 的協商 Lapsed、已做的轉換記負數差額（待確認）；Agreed 的遞延協商 → Lapsed；之後不再給予（01_scope D-15，D-05） | 結束日 | 不可撤銷；結束被註銷或結束日更正時由 ReassessLeaveEntitlements 重新推導 | 發生（結束日）、得知 |
| ConfirmLeaveConversion（確認待確認的轉換） | 人的動作（人資） | 決定 | LeaveConversion | Provisional → Determined；確認後交給薪資切片（D-11） | 確認者、時間；人資處理過的事（已休、遞延協商、告知日） | 不可撤銷；確認後發現要更正，另記差額 | 發生、得知 |
| NotifyLeaveReassessment（通知特休重新判定結果） | 其他單位個體的變化（ReassessLeaveEntitlements、RejudgeLeaveYearEnd 改變了額度、期間、狀態，或產生轉換差額；CloseLeaveYear 遇到協商遞延額度超過未休） | 建議 | LeaveEntitlement | 不改變狀態；列出改了哪幾筆（更正前、更正後）、新增或作廢的、轉換差額與待確認的轉換，以及要人處理的：作廢的那筆上已休的天數、要重新登錄的告知日、要重新登錄的遞延協商、已休超過更正後額度的、補登的那筆和依規則重算的期間重疊或有空檔的、已判定轉換的工資計算基準日或發給期限依新依據會不同的（原 → 新，④ D-25）；通知人資與雇主（老闆）（D-04） | 重新判定的紀錄 | 不可作廢（保留紀錄） | 得知 |

沿用 core 的事件（不重新定義）：CorrectRecord（更正資料）、AnnulEntry（註銷誤登）、RevokeAnnulment（撤銷註銷）、OverrideWarning（忽略警告）、WithdrawWarningOverride（撤回忽略），這些依 core 只有人資可以做；觸發本切片的 core 事件：RecordEarlyDeparture、StartEmployment、RegisterExistingEmployment（D-08）。

## 決策流程
<!-- 訊號 → 證據 → 狀態 → 建議 → 決定；沒有需要判斷的地方寫「無」 -->

本切片需要人判斷的地方有五個。範圍沒有主動提醒（01_scope X-29），所以「建議」只有法規警告與重新判定的通知，不主動建議何時休假、要不要遞延（D-03）。

**1. 告知員工排定特休**（Q07、US-D06）
- 訊號：一筆依規則給予的法定特休取得（GrantLeaveEntitlement）
- 證據：取得日、告知期限（取得日起 30 日內，特別休假#02 `[未核對]`）、實際告知日
- 狀態：告知狀態（推導，見上表）；逾期未告知時成立法規警告
- 建議：查詢這位員工的特休時看得到告知狀態與期限；逾期時列為未處理的法規警告
- 決定：雇主（老闆）告知員工後，人資或雇主登錄 RecordLeaveNotice；或由人資以 OverrideWarning 忽略警告並寫理由（法規警告不阻擋，01_scope「做」）

**2. 年度終結的遞延**（Q05、Q06、US-D04）
- 訊號：一筆特休的年度終結日接近，還有未休額度（查詢時看得到）
- 證據：還可以休的額度、已休（這版是固定資料）、有沒有遞延協商、這一筆能不能遞延（遞延進來、補登遞延的不能；公司規定的 [待專家確認: EQ-005]）
- 狀態：年度終結時如果沒有協商，未休的額度會轉為工資
- 建議：無（範圍不含提醒，D-03）
- 決定：員工與雇主協商；談定後人資登錄 RecordLeaveDeferral。沒有登錄協商就由 CloseLeaveYear 全部轉為工資——這是法令的結果（沒有協商就是發工資，01_scope D-06），不是系統替雙方決定

**3. 法規警告**（Q02、Q05、Q14；01_scope D-11）
- 訊號：到職或補登僱傭關係（StartEmployment、RegisterExistingEmployment）、登錄或終止特休年度約定、公司規定生效或改版、給予特休、年度終結後才登錄或修改遞延協商、年度終結時協商額度超過未休
- 證據：同一人在同一雇主前一段僱傭關係的結束日與這一段的到職日；曆年制換算後的天數與依法應給的天數；公司規定的天數與法定天數；協商的登錄時間與年度終結日；還在套用雇主預設的員工
- 狀態：各項警告是否成立（推導，判斷條件第 ④ 步）
- 建議：列為未處理的法規警告（不改變任何狀態）
- 決定：人資改正資料（警告就消失）、替不同意新預設的員工登錄個別約定，或以 OverrideWarning 忽略並寫理由；合併年資這版不計算（由 seniority-recognition 補上）

**4. 重新判定之後的處理**（Q11、US-D08）
- 訊號：ReassessLeaveEntitlements 或 RejudgeLeaveYearEnd 改變了已給予的特休或已判定的轉換
- 證據：更正前後的每一筆、轉換差額、待確認的轉換
- 狀態：哪幾筆作廢、哪幾筆額度改了、哪些轉換差額待確認
- 建議：NotifyLeaveReassessment 列出要人處理的事
- 決定：人資處理——這版改正已休的固定資料、重新登錄告知日與遞延協商；之後已休怎麼搬到新的一筆由 annual-leave-request 定義（D-04）。處理完再到第 5 點確認轉換

**5. 待確認的轉換**（Q05、Q08、Q11）
- 訊號：產生了待確認（Provisional）的轉換
- 證據：轉換的額度、原因、更正原因、指回的那一次；判定當時的已休與協商；發給期限
- 狀態：待確認；超過發給期限還沒確認時成立警告
- 建議：NotifyLeaveReassessment 列出待確認的轉換
- 決定：人資確認（ConfirmLeaveConversion）後交給薪資；確認前資料又改了，系統重算取代它。負數差額能不能從之後的薪資扣回由 monthly-payroll 決定 [待專家確認: EQ-009]

## 更正方式

更正都不需要第二個人核准，能追溯就好（inputs/shared/範圍釐清_更正不需核准.md）：一律記錄誰、何時、理由。沒有任何一種更正是直接覆蓋舊值或刪除事件，實際保存方式依平台 P2（第 ⑤ 步）。對員工不利的轉換差額先停在待確認（D-11）。

| 對象 | 更正事件 | 誰發現 | 誰核准 | 與原紀錄的關係 |
|---|---|---|---|---|
| 到職日、員工類型等給予特休的依據（core 的僱傭關係資料） | CorrectRecord（core），接著 ReassessLeaveEntitlements | 人資或員工 | 不需核准，留紀錄；到職日的更正依 core 是重大更正 | 原值保留；已給予的每一筆依 D-04 對應：就地更正的保留更正前內容，作廢的保留紀錄；已判定的轉換不改，另記差額（02_entities D-06）；NotifyLeaveReassessment 列出結果 |
| 特休年度約定的內容（年度種類、適用起日、終止日、協商日） | CorrectRecord（core），接著 ReassessLeaveEntitlements | 人資 | 不需核准，留紀錄 | 原值保留；依它給予的特休依 D-04 重新判定 |
| 整筆登錯的特休年度約定 | AnnulEntry（core，註銷 RecordLeaveYearAgreement），接著 ReassessLeaveEntitlements | 人資 | 不需核准，留紀錄 | 原事件保留並標為已註銷；那段期間改用前一筆約定或雇主預設 |
| 補登的特休（額度、開始管理前已休、可休期間、原年度終結日） | CorrectRecord（core）；整筆登錯用 AnnulEntry（註銷 RegisterExistingLeaveEntitlement），接著 ReassessLeaveEntitlements | 人資 | 不需核准，留紀錄 | 原值保留；已年度終結的由 RejudgeLeaveYearEnd 記差額；被註銷的那筆作廢，已做的轉換記負數差額（待確認），上面已休的天數由 NotifyLeaveReassessment 列出；撤銷註銷時恢復，轉換再依 ReassessLeaveEntitlements 記差額 |
| 實際告知日 | CorrectRecord（core）；整筆登錯用 AnnulEntry（註銷 RecordLeaveNotice） | 人資或雇主（老闆） | 不需核准，留紀錄（由人資執行） | 原值保留；告知狀態重推，看得出更正過 |
| 遞延協商登錄時打錯（協商日、額度） | CorrectRecord（core） | 人資 | 不需核准，留紀錄 | 原值保留；已 Applied 的由 RejudgeLeaveYearEnd 記差額。雙方重新談不是更正，用 AmendLeaveDeferral（D-06） |
| 已判定的轉換（額度、工資計算基準日、發給期限） | RejudgeLeaveYearEnd 或 ReassessLeaveEntitlements 記一筆差額 | 系統（依據改變時）或人資 | 不需核准，留紀錄；負數差額由人資確認後才交給薪資 | 不改原判定；差額指回被更正的那一次，記更正原因（02_entities D-06）；不能用 CorrectRecord 直接改 |
| 公司規定的名稱、依據說明、生效日、廢止日 | CorrectRecord（core）；整筆登錯用 AnnulEntry（註銷 EstablishCompanyPolicy） | 人資 | 不需核准，留紀錄 | 原值保留；生效日、廢止日改變時接著 ReassessLeaveEntitlements（D-14）；版本內容的登錄錯誤用 ReviseCompanyPolicy 新增修訂（只限人資），接著 ReassessLeaveEntitlements、RejudgeLeaveYearEnd（D-16） |
| 已休（這版的固定資料） | RejudgeLeaveYearEnd（人資改正固定資料 [靜態替代] 後，對已年度終結的那一筆） | 人資 | 不需核准，留紀錄 | 固定資料的改正也記誰、何時、理由；判定當時的已休記在那次判定上，不會被改正蓋掉（D-15）；正式的請假更正由 annual-leave-request 定義 |

本切片可以註銷的事件：RegisterExistingLeaveEntitlement、RecordLeaveNotice、RecordLeaveYearAgreement、EndLeaveYearAgreement、EstablishCompanyPolicy、RepealCompanyPolicy。不能註銷的：遞延協商的三個事件（用修改、撤回、更正處理，D-06）、ReviseCompanyPolicy（版本更正是新的修訂）、ConfirmLeaveConversion（確認後的更正記差額）、所有由時間或條件、其他單位個體的變化觸發的事件（推導的，依據改了就重新推導或記差額）、建議層的 NotifyLeaveReassessment（D-08）。

不能直接改的：依規則給予的特休額度沒有人工加減的動作（02_entities D-07）；覺得給錯時，更正它依據的資料。

## 詞彙對照表新增

| ID | 種類 | 定義 | zh-TW | 對照備註 |
|---|---|---|---|---|
| LeaveEntitlement.Active | 狀態 | 請假權利可以休 | 可休 | |
| LeaveEntitlement.YearEnded | 狀態 | 已做年度終結判定，未休的已遞延或轉換 | 已年度終結 | |
| LeaveEntitlement.EndedWithEmployment | 狀態 | 年度終結前僱傭關係結束，未休的交由契約終止處理 | 隨僱傭關係結束 | 之後由 resignation 轉換 |
| LeaveEntitlement.Voided | 狀態 | 重新判定後不再成立、從未取得，或遞延撤回，保留紀錄 | 已作廢 | |
| LeaveDeferralAgreement.Agreed | 狀態 | 已協商遞延，還沒到年度終結 | 已協商 | |
| LeaveDeferralAgreement.Applied | 狀態 | 年度終結時已依它產生遞延進來的那一筆 | 已遞延 | |
| LeaveDeferralAgreement.Withdrawn | 狀態 | 雙方取消遞延 | 已撤回 | |
| LeaveDeferralAgreement.Lapsed | 狀態 | 要遞延的那一筆沒有進到年度終結（離職或作廢） | 已失效 | |
| LeaveYearAgreement.Scheduled | 狀態 | 已約定，還沒到適用起日 | 尚未適用 | |
| LeaveYearAgreement.Effective | 狀態 | 目前適用的約定 | 適用中 | |
| LeaveYearAgreement.Superseded | 狀態 | 被下一筆約定取代 | 已取代 | |
| LeaveYearAgreement.Ended | 狀態 | 雙方不再個別約定，之後套用雇主預設 | 已終止 | |
| CompanyPolicy.Scheduled | 狀態 | 已訂定，還沒到第一次生效日 | 尚未生效 | |
| CompanyPolicy.Effective | 狀態 | 公司規定生效中 | 生效中 | |
| CompanyPolicy.Repealed | 狀態 | 公司規定已廢止 | 已廢止 | |
| LeaveConversion.Provisional | 狀態 | 更正造成的不利差額或依據未處理完的判定，等人資確認 | 待確認 | 還沒交給薪資 |
| LeaveConversion.Determined | 狀態 | 轉換已判定，之後不再改變 | 已判定 | |
| LeaveConversion.Discarded | 狀態 | 待確認的轉換在確認前被重新算出的取代 | 已取代 | 保留紀錄 |
| LeaveType.Active | 狀態 | 假別使用中 | 使用中 | |
| LeaveType.Deprecated | 狀態 | 假別已停用，不刪除 | 已停用 | |
| GrantLeaveEntitlement | 事件 | 取得日到達時依規則給予特休 | 給予特休 | |
| RegisterExistingLeaveEntitlement | 事件 | 補登開始由系統管理那天仍可以休的特休 | 補登仍可休的特休 | |
| RecordLeaveNotice | 事件 | 登錄雇主告知員工排定特休的日期 | 登錄告知排定特休 | |
| RecordLeaveYearAgreement | 事件 | 登錄員工與雇主協商的特休年度 | 登錄特休年度約定 | |
| ActivateLeaveYearAgreement | 事件 | 特休年度約定的適用起日到達 | 約定開始適用 | |
| EndLeaveYearAgreement | 事件 | 雙方不再個別約定特休年度，回到雇主預設 | 終止特休年度約定 | |
| EstablishCompanyPolicy | 事件 | 訂定一條公司規定 | 訂定公司規定 | |
| ReviseCompanyPolicy | 事件 | 公司規定新增一個版本 | 修改公司規定 | |
| ActivateCompanyPolicy | 事件 | 公司規定的第一次生效日到達 | 公司規定生效 | |
| RepealCompanyPolicy | 事件 | 登錄公司規定的廢止 | 廢止公司規定 | |
| ExpireCompanyPolicy | 事件 | 公司規定的廢止日到達 | 公司規定廢止生效 | |
| RecordLeaveDeferral | 事件 | 登錄勞雇雙方協商的遞延 | 登錄遞延協商 | |
| AmendLeaveDeferral | 事件 | 雙方重新協商遞延的內容 | 修改遞延協商 | |
| WithdrawLeaveDeferral | 事件 | 雙方取消遞延 | 撤回遞延協商 | |
| CloseLeaveYear | 事件 | 可休迄日過完時判定未休額度遞延或轉換 | 年度終結判定 | 台灣法令稱「年度終結」 |
| RejudgeLeaveYearEnd | 事件 | 年度終結判定用到的資料改變後重新判定並記差額 | 重新判定年度終結 | |
| ReassessLeaveEntitlements | 事件 | 給予特休的依據被更正後重新判定 | 依據更正後重新判定特休 | |
| EndLeaveEntitlementsWithEmployment | 事件 | 系統得知僱傭關係結束時停止特休 | 僱傭關係結束，停止特休 | |
| ConfirmLeaveConversion | 事件 | 人資確認待確認的轉換，之後交給薪資 | 確認待確認的轉換 | |
| NotifyLeaveReassessment | 事件 | 通知重新判定的結果與要人處理的事 | 通知特休重新判定結果 | |

## 決定與理由

| # | 決定 | 考慮過的替代做法 | 理由 | 依據 | 提出／同意 |
|---|---|---|---|---|---|
| D-01 | 依規則給予的特休，在取得日到達時由系統給予（GrantLeaveEntitlement，時間或條件到達、發生層），不需要人確認；還沒取得的之後各期只做預估（推導），不先建立 | ① 到職時一次建立之後所有各期；② 系統算出後由人資確認才給予 | 法令是「符合條件時，取得特別休假之權利」（勞基法施行細則第 24 條第 1 項，特別休假#02 `[未核對]`），權利在那天就發生，不是雇主決定的，所以是「發生」層；① 先建立的各期在到職日更正、改用另一種年度、規則改版時都要重算，等於還沒取得就有歷史；② 讓人確認會出現「已符合條件但系統沒給」的空窗。US-D01 要知道之後各期，用預估回答 | Q01、Q02、US-D01；02_entities D-03 | AI／JiHungLin（2026-10-20） |
| D-02 | 正常的年度終結由系統在年度終結日過完後判定（CloseLeaveYear，發生層）：有登錄遞延協商的部分遞延，其餘轉為工資（公司規定的那筆依公司規定），直接交給薪資切片，不設人資確認的關卡；更正、較晚得知造成的差額另依 D-11 | 系統算出後一律由人資確認，確認後才交給薪資 | 沒有協商就發工資是法令的結果（勞基法第 38 條第 4 項：年度終結未休的天數，雇主應發給工資，特別休假#01 `[未核對]`；01_scope D-06），不是要人決定的事；一律確認時，人資沒確認就會拖過發給期限。挑錯指出差額（特別是扣回）不是法令的結果（X-10），所以只把正常的年度終結排除在確認之外 | Q05、Q06；01_scope D-05、D-06；X-10 | AI／JiHungLin（2026-10-20） |
| D-03 | 不做主動建議：年度終結前不建議員工安排休假或協商遞延，告知期限前不提醒雇主；決策流程只用查詢看得到的狀態、法規警告與重新判定的通知 | 加一個建議層事件，年度終結前 N 天建議安排休假或協商遞延（docs/01 ③ 決策流程的請假例） | 第 ① 步已把「提醒」從範圍拿掉（01_scope X-29：範圍沒有提醒這項功能）；加進來是擴大範圍，要回第 ① 步由你決定。法規警告與重新判定的通知不是新功能：前者是 01_scope「法規檢查只警告」，後者是「看得出更正前的結果」的一部分 | 01_scope X-29、「做」 | AI／JiHungLin（2026-10-20） |
| D-04 | 〔回頭修改，2026-10-20，④ X-06〕重新判定（ReassessLeaveEntitlements）的新舊對應：依新依據重算每一期，和既有的**依規則給予的**逐筆比對「同一來源（同一條公司規定）、同一期別，而且新舊可休期間有重疊」——對得上的就地更正、保留更正前內容（已年度終結、已隨離職結束的也一樣），已休、告知日、遞延協商留在這一筆；對不上的舊的作廢、新的新增。補登的那筆是人登錄的事實，不參加比對、不被系統作廢；遞延進來的那筆跟著原來那一筆。作廢的那筆上已休的天數、告知日、遞延協商**不自動搬**到新的一筆，由 NotifyLeaveReassessment 列出，人處理 | ① 只依期別（第幾期）對應；② 依可休期間重疊最多的對應，並把已休、告知日自動搬過去；③ 只依「同一可休期間」（2026-10-20 前的寫法） | ① 02_entities X-15 已指出到職日往前更正一年時，舊的第 1 期其實對應新的第 2 期，已休會掛錯；② 已休是哪一天休的、扣哪一筆，是 annual-leave-request 的扣用規則（遞延的優先扣除），這條切片自己搬會替它定規則；告知日搬過去，可能讓實際沒有針對這一期的告知被當成已告知。補登的那筆不參加，是因為它沒有規則依據可以重算（X-15）。〔2026-10-20〕原本的「同一可休期間」在到職日只差一天時，每一期的期間都不同，全部作廢重建、已休與已發的工資都要人處理，也讓 YearEnded→Active 等就地更正的轉換永遠不會發生（④ X-06）；加上「期間有重疊」：差一天會重疊、就地更正，差一年不重疊、作廢重建，仍避免 ① 的問題。就地更正後期間或取得日改變、上面有已休或告知日的，也列入通知；原本的告知算不算數待 EQ-012 | Q11、Q12、US-D08；02_entities D-03、D-07、X-15、X-17；X-02、X-15；④ X-06、D-15 | AI／JiHungLin（2026-10-21） |
| D-05 | 僱傭關係在年度終結前結束時，可休的那筆進到 EndedWithEmployment，本切片不轉換（交給 resignation）。結束日較晚才得知時：取得日晚於結束日的那筆作廢（其實從未取得）；年度終結判定之後才得知結束日早於年度終結日的，那次年度終結視為沒有發生——已做的轉換記負數差額、遞延進來的那筆作廢、協商失效，原來那一筆整筆交給 resignation | 在本切片先依契約終止轉換；結束日較晚得知時不回頭處理 | 01_scope D-15 已決定年度終結前離職的交給 resignation；結束日較晚登錄在實務上可能發生（例：月底離職、月初才登錄，這版的固定資料也可能較晚載入），不處理會讓同一批天數在年度終結和離職時各轉一次（X-05），或讓從未取得的特休被折算工資（X-04） | 01_scope D-15、X-25；X-04、X-05、X-06 | AI／JiHungLin（2026-10-20） |
| D-06 | 遞延協商分「修改」與「更正」：雙方重新談用 AmendLeaveDeferral（協商日改變），登錄打錯用 CorrectRecord（協商日不變），兩者都保留原內容；年度終結之後仍可以修改、撤回、事後登錄，系統不阻擋，用 RejudgeLeaveYearEnd 更正遞延進來的那筆並記轉換差額；只要登錄時間晚於年度終結日就給警告（不只看填的協商日）；減少工資的差額待確認（D-11）。終結後才協商算不算數待 EQ-003 | 年度終結後鎖住，不能再改協商；警告只看協商日 | 01_scope X-07、02_entities D-05：協商會改、會事後補；鎖住會讓已經談好、只是晚登錄的協商無法反映，員工反而被發工資。是否合法由專家回答前，用警告而不是阻擋（範圍釐清_法規警告不阻擋.md）。警告只看協商日的話，回填較早的協商日就能繞過（X-09）。修改和更正分開，是因為雇主舉證時要分得出「雙方改談」和「我們打錯」 | Q05、Q06；01_scope X-07；02_entities D-05、X-12；EQ-003；X-09 | AI／JiHungLin（2026-10-20） |
| D-07 | 歷史需求：請假權利、轉換、遞延協商、公司規定為「需要重建當時」；特休年度約定為「需要軌跡」；假別為「只需現況」，不做事件 | 遞延協商只需要軌跡；特休年度約定需要重建當時；假別需要軌跡 | 遞延協商：年度終結依判定當時的協商內容，之後被修改要說得出判定時是多少（Q05、Q06）。特休年度約定：每一筆特休給予時依哪一種已凍結在那一筆上（02_entities D-04），約定本身只要知道誰何時登錄或更正（Q03）。假別：驗收問題只問是哪一種假（Q01），法令廢止時標停用、不刪除，舊資料照原意解讀；docs/01 ③ 允許只需現況的不做事件 | Q01、Q03、Q05、Q06、Q09、Q10、Q11 | AI／JiHungLin（2026-10-20） |
| D-08 | 沿用 core 的 CorrectRecord、AnnulEntry、RevokeAnnulment、OverrideWarning，不重新定義，執行者照 core 只有人資；本切片可以註銷的事件在本檔「更正方式」自己列出，不修改 hire-employee 的白名單（hire-employee 03_flows D-14）；重新判定的結果用本切片的 NotifyLeaveReassessment 通知，不擴充 core 的「重大更正」條件 | ① 本切片自己定義撤銷、更正事件；② 把特休的重新判定加進 core 的重大更正條件 | 同一個概念只有一份定義（docs/01 0.2）；① 會出現兩種「更正」。② 要改 hire-employee 已凍結的更正方式，需要先經你同意並回頭改那條切片；用本切片自己的通知不必改。到職日的更正本來就是重大更正（core），會通知雇主；年度約定的更正、協商修改造成的重新判定，由 NotifyLeaveReassessment 補上。挑錯指出初稿寫「雇主也可以更正、忽略警告」和 core 的權限衝突（X-12），已改為只有人資 | core/flows.md 更正方式；docs/01 0.2；X-12 | AI／JiHungLin（2026-10-20） |
| D-09 | 告知狀態、預估、法規警告都是推導的，不是狀態機：不存、不由事件改變，依據改了就重算 | 告知做成請假權利上的另一個狀態機（待告知 → 已告知／逾期） | 02_entities 已把告知期限、是否逾期判為推導值、法規警告判為推導值（02_entities「不是 Entity」）；做成狀態機會要一個「逾期」的時間事件，取得日一更正又要倒回 | 02_entities「不是 Entity」、D-12 | AI／JiHungLin（2026-10-20） |
| D-10 | 特休年度約定登錄、終止或更正時，日期早於已給予的特休的取得日，視同依據改變，觸發 ReassessLeaveEntitlements | 不允許日期早於已給予的取得日；不回頭處理，只影響之後的給予 | 實務上約定常常晚登錄（例：12 月談好 1 月 1 日起改曆年制，1 月 10 日才登錄），中間已經依舊的年度給了一筆；不回頭處理，那一筆的年度就和約定不一致；不允許則晚登錄的約定登不進去 | Q03、Q14、US-D10；02_entities D-03 | AI／JiHungLin（2026-10-20） |
| D-11 | 轉換分「待確認」與「已判定」：更正、註銷、較晚得知造成的差額中，減少員工工資或改為失效的（負數差額），以及由重新判定新增、可休迄日已經過了的那一筆的年度終結，先停在待確認，人資看過通知、處理完已休與協商後確認（ConfirmLeaveConversion）才交給薪資；正常的年度終結與增加員工工資的差額直接交給薪資。待確認期間資料又改了，重算的取代它 | ① 全部直接交給薪資（初稿）；② 全部都要人確認 | 挑錯有五個反例出自同一個原因：系統在沒有人確認的情況下，把轉換差額直接交給薪資（X-01、X-03、X-06、X-09、X-10）——重新判定新增的那一期，已休和協商還沒處理就被判定，會多發工資；回填協商、改到職日造成的扣回，沒有任何人看過就進了薪資，而扣回本身能不能做還待 EQ-009。② 會讓正常的年度終結拖過發給期限（D-02）。正數差額不停，是因為那是欠員工的錢 | X-01、X-03、X-06、X-09、X-10；D-02；EQ-009 | AI／JiHungLin（2026-10-20） |
| D-12 | 協商遞延的額度大於年度終結時的未休：遞延進來的那筆只建未休的部分，協商本身不改（仍記雙方談定的額度），成立警告並列入通知 | ① 照協商額度建立；② 自動把協商改成未休的天數 | ① 會讓原來那一筆的剩餘變成負數，守恆式不平；② 是系統改寫雙方談定的事實（02_entities D-05：延多少是協商的事實）。差距通常是協商之後又休了假，屬正常情況，所以只警告 | 02_entities D-05；X-03 | AI／JiHungLin（2026-10-20） |
| D-13 | 雇主改了特休年度的預設（ReviseCompanyPolicy），沒有個別約定的員工之後套用新的預設；改版時對這些員工成立警告，不同意的員工由人資登錄一筆維持原年度的個別約定；新增 EndLeaveYearAgreement，讓員工可以從個別約定回到預設 | 預設改版只適用之後到職的員工；預設改版時自動替每位現有員工建立維持原年度的約定 | 年度是勞雇雙方協商的結果（01_scope D-12），雇主改預設等於單方替還在套用預設的員工換年度（X-11）；但工作規則改預設算不算協商還待 EQ-002，所以先警告、不自動處理。自動替每人建立約定會把雇主的預設變成好像每個人都個別談過 | 01_scope D-12；EQ-002；X-11 | AI／JiHungLin（2026-10-20） |
| D-14 | 公司規定的生效日、廢止日是登錄的事實：登錄或更正時日期早於已給予的特休取得日，觸發 ReassessLeaveEntitlements（補上或拿掉那段期間的加給）；版本內容（多給幾天）的登錄錯誤仍由第 ④ 步決定 | 一律不重新判定（初稿，交第 ④ 步） | 生效日打錯（例：7 月生效登成隔年 1 月），7～12 月滿年資的員工就默默少拿加給（X-14）；生效日、廢止日是 CompanyPolicy 卡上的屬性（事實），不是規則版本，依 02_entities D-03「依據的事實被更正」應該重新判定 | 02_entities D-03、CompanyPolicy 卡；X-14 | AI／JiHungLin（2026-10-20） |
| D-15 | 年度終結判定時，把當時已知的已休記在那次判定上；這版已休的固定資料改正也要記誰、何時、理由，改正後觸發 RejudgeLeaveYearEnd | 只在需要時讀固定資料的目前值 | 固定資料被覆寫時，回答不了「判定當時以為休了幾天、誰何時改成幾天」（Q05、Q11），雇主舉證也拿不出依據（X-07） | Q05、Q11；X-07 | AI／JiHungLin（2026-10-20） |
| D-16 | 〔回頭修改，2026-10-21，⑤ X-03〕公司規定版本內容的登錄錯誤（多給幾天、適用對象、年度終結處理、年度預設）用 ReviseCompanyPolicy 新增一筆修訂，只限人資；修訂是依據更正：取得日落在那一版有效期間的特休（含原本因條件不符沒給的）ReassessLeaveEntitlements，已年度終結的 RejudgeLeaveYearEnd，更正原因為依據更正；已廢止的規定也可以修訂。改版（新的版本）仍不影響已給予的 | 修訂也不影響已給予的，只警告；不允許修訂 | 打錯 5 天實際 3 天時不重新判定，就會一直多給、多發工資，和到職日打錯的處理不一致；原本這件事交給第 ④ 步，④ 沒有寫（⑤ X-03、X-15） | 05_mapping D-19；02_entities D-03；D-14 | AI／JiHungLin（2026-10-21） |

### 反例處理

| # | 反例 | 來源 | 處理 | 理由或去向 |
|---|---|---|---|---|
| X-01 | 到職日更正後新增的一期，可休迄日已經過了：只能用「（無）→ Active」進來後立刻年度終結，已休算 0、協商被作廢的那筆帶走，7 天全部轉為工資，實際應該只發 2 天 | AI 挑錯 | 接受，已修改 | 新增 D-11：這種年度終結的轉換先停在待確認，人資處理完已休與協商後確認；通知列出要重新登錄的協商 |
| X-02 | 同一可休期間的額度就地更正，只寫在 Active；已年度終結、已隨離職結束的那筆沒有轉換可走，誰算差額不清楚 | AI 挑錯 | 接受，已修改 | 新增 YearEnded → YearEnded（接著 RejudgeLeaveYearEnd）、EndedWithEmployment → EndedWithEmployment（差額由 resignation 處理）；D-04 寫明 |
| X-03 | 協商遞延的額度大於年度終結時的未休（之後又休了假，或額度被更正變少），遞延進來的那筆建幾天沒有定義 | AI 挑錯 | 接受，已修改 | 新增 D-12：只建未休的部分，協商不改，給警告 |
| X-04 | 結束日在給予之後才登錄（固定資料較晚載入）：從未取得的特休被轉成 EndedWithEmployment，交給 resignation 折算工資；這版沒有結束的事件，怎麼偵測也沒寫 | AI 挑錯 | 接受，已修改 | EndLeaveEntitlementsWithEmployment：取得日晚於結束日的作廢；觸發來源寫明「載入結束日視同這個變化」；D-05 |
| X-05 | 年度終結後才得知結束日在終結日之前：Applied 的協商沒有轉換，遞延進來的那筆帶著遞延的來歷交給 resignation，工資基準會錯 | AI 挑錯 | 接受，已修改 | 新增 Applied → Lapsed、遞延進來的 YearEnded／Active → Voided；原來那一筆整筆交給 resignation；D-05 |
| X-06 | 註銷後已交給薪資的轉換沒有事件沖回：註銷離職後回到可休、補登的特休被註銷，同一批天數會發兩次 | AI 挑錯 | 接受，已修改 | ReassessLeaveEntitlements 的觸發加上補登的特休被註銷或撤銷註銷，轉換記差額；EndedWithEmployment → Active 寫明 resignation 的轉換由 resignation 記負數差額 |
| X-07 | 已休（固定資料）的改正不是事件、不留紀錄，重建不了判定當時已知的已休 | AI 挑錯 | 接受，已修改 | 新增 D-15：判定時記下當時的已休；固定資料改正記誰、何時、理由，觸發 RejudgeLeaveYearEnd |
| X-08 | 年度終結時公司加給能不能失效依「判定時的版本」：雇主在年度終結前一天改版，已給的加給全部失效，和「已給予的依舊版」衝突 | AI 挑錯 | 轉問專家 | EQ-013；ReviseCompanyPolicy 標 [待專家確認: EQ-013]。年度終結依哪一版是第 ④ 步的規則 |
| X-09 | 回填較早的協商日就能繞過「年度終結後才協商」的警告，系統自動產生扣回的差額；員工沒有任何同意紀錄 | AI 挑錯 | 接受，已修改 | D-06：警告看登錄時間；D-11：負數差額待確認。員工端的同意紀錄不加：範圍沒有員工自己操作的功能，憑據寫在協商說明 |
| X-10 | 改到職日讓特休變少，負數差額自動送薪資，員工不會被通知；D-02 拿掉確認關卡的理由不適用於扣回 | AI 挑錯 | 接受，已修改 | D-11：負數差額待確認；D-02 限縮在正常的年度終結。通知員工不加：範圍沒有對員工的通知功能，列在 D-11 的考量 |
| X-11 | 改公司預設等於單方替不同意的員工換年度；員工沒有回到預設的事件；回溯改預設與回溯登錄約定的效果不一致 | AI 挑錯 | 接受，已修改 | 新增 D-13、EndLeaveYearAgreement 與 LeaveYearAgreement.Ended；預設改版成立警告。回溯改預設仍不觸發重新判定：預設的內容是規則版本（02_entities D-03 規則改版不觸發），和登錄的約定（事實）不同 |
| X-12 | 告知日可以默默回填；本切片寫雇主也能更正、忽略警告，和 core 的權限（只有人資）衝突 | AI 挑錯 | 接受，已修改 | 更正、註銷、忽略警告改為只有人資（D-08）；告知狀態看得出更正過（core CorrectRecord 保留原值）。員工確認告知不加：範圍沒有員工端功能 |
| X-13 | 廢止日在未來的 RepealCompanyPolicy 到期時沒有事件；Scheduled 的規定不能修改 | AI 挑錯 | 接受，已修改 | 新增 ExpireCompanyPolicy；新增 Scheduled → Scheduled（ReviseCompanyPolicy） |
| X-14 | 公司規定的生效日打錯，更正後不會補給，員工默默少拿 | AI 挑錯 | 接受，已修改 | 新增 D-14：生效日、廢止日是事實，更正觸發 ReassessLeaveEntitlements |
| X-15 | 補登的特休遇到到職日更正：要不要參加重新判定的比對沒有定義；遞延進來的那筆要不要跟著原來那筆改 | AI 挑錯 | 接受，已修改 | D-04：補登的不參加、不被作廢，重疊或空檔由通知列出；遞延進來的跟著原來那一筆 |

<!-- 來源：AI 挑錯／審查者／專家／其他切片。處理：接受，已修改／拒絕（理由必填）／轉問專家（填 EQ 編號） -->

## 檢查紀錄

<!-- AI 只填「AI 自評」（✓、✗、部分＋說明）並列出審查重點；「審查者確認」由非產出者填寫（輸入輸出規範「檢查紀錄」） -->
<!-- CHECKLIST:START -->
### 完成標準（AI 自評）

| 完成標準 | 類 | AI 自評 |
|---|---|---|
| 每個會變狀態的 Entity，以及會隨時間推進的流程（動詞，不只名詞），都有狀態機，沒有走不到的狀態 | 品質檢查 | ✓ 6 個新增的 Entity 都有狀態機（假別只有狀態、不設事件，D-07）；會隨時間推進的動詞（遞延協商、特休年度約定、轉換的待確認）是各自的狀態機；給予、年度終結、重新判定是一次發生的事件，沒有自己的生命週期；告知是推導狀態（D-09）。每個狀態都有轉入的轉換，由 AI 逐一比對；check.py 不檢查可達性 |
| 「核准」和「發生」是分開的兩件事 | 品質檢查 | ✓ 本切片沒有核准；「決定」層（協商、約定、公司規定、確認轉換）和「發生」層（給予、年度終結、重新判定）分開，雙方協商遞延之後由年度終結才產生遞延進來的那一筆。由 AI 判斷 |
| 需要判斷的地方有寫出決策流程（訊號 → 證據 → 狀態 → 建議 → 決定）；系統或 AI 的建議不會直接改變狀態 | 品質檢查 | ✓ 5 個決策流程；唯一的建議層事件 NotifyLeaveReassessment 不改變狀態（lint.py「建議層」通過）；不主動建議的理由見 D-03 |
| 每個事件標了觸發來源；由人觸發的，標了誰有權觸發 | 品質檢查 | ✓ check.py「每個事件須標觸發來源」通過；20 個新事件中由人觸發的 11 個都在觸發來源括號中寫了人資或雇主（老闆），沿用 core 的更正事件依 core 只有人資（D-08）。由程式＋AI 比對 |
| 每個會變狀態的東西都標了歷史需求，並註明依據哪條驗收問題 | 關鍵決定 | ✓ 6 個狀態機的標題都有歷史需求與 Q 編號（md2build 解析通過）；只需現況的只有假別（D-07）。選擇的理由由 AI 判斷 |
| 有寫更正方式，且沒有任何一步是直接改舊紀錄 | 品質檢查 | ✓ 9 列更正方式；就地更正都保留更正前內容，已判定的轉換只記差額、待確認的被取代也保留紀錄；固定資料的改正也記誰、何時、理由（D-15）。由 AI 判斷 |
| 第 ① 步每個草稿 User Story，都至少被一個正式 Use Case 涵蓋 | 修正線索 | ✓ US-D01～US-D11 都在草稿涵蓋檢查表（lint.py「編號存在」沒有草稿 US 未涵蓋的紅燈） |
| 每個正式 Use Case 都註明了用到的 Entity、事件 | 修正線索 | ✓ UC-01～UC-12 都有；用到的名稱都已宣告（lint.py「編號存在」） |

### 審查重點（人）

<!-- AI 列出：〔關鍵決定〕要看的清單或位置（精簡版 0.2 的表）、AI 提出的決定、自評為「部分」或 ✗ 的完成標準；抽查那一列由審查者自選，AI 不預選 -->
| # | 要看的 | 在哪裡 | 審查者確認 |
|---|---|---|---|
| 1 | 標「只需現況」的項目只有 1 個：假別（代碼、名稱、停用）。理由：驗收問題只問「這一筆是哪一種假」；法令廢止時標停用、不刪除。其他 5 個都是需要軌跡或需要重建當時 | 「狀態機」LeaveType、D-07 | ✓ |
| 2 | 歷史需求的選擇：遞延協商選「需要重建當時」（年度終結後被修改，要說得出判定當時談的是幾天）；特休年度約定只選「需要軌跡」（每一筆特休已記下當時依哪一種年度） | 各狀態機標題與說明、D-07 | ✓ |
| 3 | 系統自動做、不需人確認的：取得日到了就給特休（D-01）；正常的年度終結，沒有協商遞延的未休天數直接轉為工資交給薪資（D-02，勞基法第 38 條第 4 項：年度終結未休的天數雇主應發給工資） | D-01、D-02 | ✓ |
| 4 | 要人確認才交給薪資的（D-11，挑錯後新增）：更正、註銷、較晚得知造成的**扣回**（負數差額），以及到職日更正後新增、而且已經過了年度終結的那一期。增加工資的差額不停 | 「狀態機」LeaveConversion、決策流程 5、D-11 | ✓ |
| 5 | 到職日更正後怎麼對應舊的特休（D-04）：同一來源、同一可休期間才算同一筆，其他作廢再新增；作廢的那筆上已休的天數、告知日、遞延協商不自動搬，系統列出來由人處理。週年制下到職日一改，幾乎每一期都會作廢再新增 | D-04、UC-08 | ✓ |
| 6 | 離職較晚才登錄時（D-05）：還沒取得的特休作廢；已經做過年度終結的，那次年度終結當作沒發生，扣回已轉的工資（待確認），整筆交給 resignation | D-05、UC-09 | ✓ |
| 7 | 雇主改特休年度的預設（D-13）：還在套用預設的員工會跟著換，系統給警告，不同意的要人資一個一個登錄維持原年度的約定 | D-13、UC-10 | ✓ |
| 8 | 其他 AI 提出的決定（全部待你確認）：D-03 不做「年度終結前建議休假」等主動提醒（第 ① 步已從範圍拿掉）；D-06 遞延協商年度終結後仍可改、只警告，警告看登錄時間；D-08 沿用 core 的更正與註銷，不改 hire-employee 的內容；D-09 告知狀態是算出來的；D-10、D-14 年度約定、公司規定的日期回溯時重新判定；D-12 協商延的天數比剩下的多時，只延剩下的；D-15 年度終結時記下當時的已休 | 「決定與理由」 | ✓ |
| 9 | 新增的專家問題：EQ-011 最後工作日剛好是年度終結日，未休的算年度終結還是契約終止；EQ-012 到職日更正後原本的告知算不算數；EQ-013 雇主在年度終結前改公司規定，讓公司多給的特休「沒休就失效」，可不可以 | questions.md | ✓ |
| 抽查 | （審查者自選 1～2 條 AI 自評 ✓ 的完成標準，寫出是哪幾條與結果） |每個事件標了觸發來源；由人觸發的，標了誰有權觸發。需要判斷的地方有寫出決策流程（訊號 → 證據 → 狀態 → 建議 → 決定）；系統或 AI 的建議會不直接改變狀態  | ✓ |
<!-- CHECKLIST:END -->

- 審查者（非產出者）： JiHungLin
- 日期： 20261020
- 結論：通過

### 審查重點（2026-10-20 回頭修改）

第 ④ 步回填規則編號、挑錯後回頭修改第 ③ 步；只看這次的差異，其他沿用上方已確認的審查重點。

| # | 要看的 | 在哪裡 | 審查者確認 |
|---|---|---|---|
| 1 | D-04 改了（你在 2026-10-20 同意過的決定，已改回「待確認」）：重新判定時「同一來源、同一期別，而且新舊可休期間有重疊」才算同一筆、就地更正，已休與告知日留在原來那一筆；原本是「同一可休期間」，到職日只差一天就整串作廢重建（④ X-06）。差一年仍不重疊、作廢重建，保留當初排除「只看期別」的理由 | D-04；LeaveEntitlement 狀態機三列就地更正的前提；UC-08 | ✓ |
| 2 | 年度終結的轉換：凡是補做的年度終結（判定日晚於可休迄日的隔天）、公司多給轉為失效、公司多給找不到依據版本的，都先停在待確認；正常的年度終結轉為工資才直接交給薪資（④ X-20、R93） | LeaveConversion 狀態機（無）→ Determined／Provisional 的兩列 CloseLeaveYear | ✓ |
| 3 | 遞延協商從「失效」恢復的條件改為看那一筆是否已經做過年度終結判定（看狀態，不看日期）（④ X-23） | LeaveDeferralAgreement 狀態機 Lapsed → Agreed | ✓ |
| 4 | 狀態轉換「規則」欄與 UC「規則」已回填 ④ 的規則編號（只有 Agreed → Withdrawn 沒有規則） | 各狀態機的「規則」欄；03_use_cases.md 各 UC；04_rules.md「回填紀錄」 | ✓ |
| 抽查 | （審查者自選 1～2 條 AI 自評 ✓ 的完成標準，寫出是哪幾條與結果） | 每個正式 Use Case 都註明了用到的 Entity、事件。核准」和「發生」是分開的兩件事 | ✓ |

- 審查者（非產出者）： JiHungLin
- 日期： 20261021
- 結論：通過

### 審查重點（2026-10-21 回頭修改）

第 ⑤ 步挑錯後回頭修改第 ③ 步（⑤ X-03、X-15，05_mapping D-19）；只看這次的差異。

| # | 要看的 | 在哪裡 | 審查者確認 |
|---|---|---|---|
| 1 | 新增 D-16：公司規定的內容打錯（例：加給打成 5 天，實際是 3 天）時，人資新增一筆修訂，已給予的特休跟著重新判定（含因條件打錯而原本沒給的），已年度終結的重新判定年度終結；已廢止的規定也可以修訂。改成新的版本（改版）仍不影響已給予的 | D-16；CompanyPolicy 狀態機兩列（Effective → Effective 的前提、新增 Repealed → Repealed）與說明；事件表 ReviseCompanyPolicy、RejudgeLeaveYearEnd、ReassessLeaveEntitlements 的觸發來源；更正方式「公司規定」列；UC-03 例外 | ✓ |
| 2 | ⑤ 紙上驗證後的兩處：告知狀態不判定隨僱傭關係結束、作廢的那一筆（④ D-24）；重新判定的通知多列「已判定轉換的基準日或發給期限：原 → 新」（④ D-25） | 推導的狀態表「告知狀態」列；事件表 NotifyLeaveReassessment | ✓ |
| 抽查 | （審查者自選 1～2 條 AI 自評 ✓ 的完成標準，寫出是哪幾條與結果） | 第 ① 步每個草稿 User Story，都至少被一個正式 Use Case 涵蓋。每個事件標了觸發來源；由人觸發的，標了誰有權觸發 | ✓ |

- 審查者（非產出者）： JiHungLin
- 日期： 20261021
- 結論：通過