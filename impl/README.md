# hire-employee、annual-leave-grant 實作（MongoDB＋FastAPI）

依 `slices/annual-leave-grant/` 凍結的設計實作特休：`02_entities.md` @ `annual-leave-grant/02-v1`；`03_flows.md`、`03_use_cases.md` @ `annual-leave-grant/03-v4`；`04_rules.md` @ `annual-leave-grant/04-v3`；`05_mapping.md`、`schema.mongo.js`、`api.yaml`（0.2.0）@ `annual-leave-grant/05-v3`。兩條切片共用同一個資料庫與 API。

依 `slices/hire-employee/` 凍結的設計實作：`02_entities.md` @ `hire-employee/02-v4`；`03_flows.md` @ `hire-employee/03-v6`；`04_rules.md` @ `hire-employee/04-v5`；`05_mapping.md`、`schema.mongo.js`、`api.yaml`（0.5.0）@ `hire-employee/05-v7`。

## 需要

- MongoDB replica set（多文件交易，PLAN.md D-35）。連線字串預設 `mongodb://localhost:27017/?replicaSet=rs0`，可用 `HR_MONGO_URI` 覆寫。
- `mongosh`（建立集合時執行 `schema.mongo.js`）
- [uv](https://docs.astral.sh/uv/)

## 使用

```bash
uv sync
uv run python scripts/init_db.py --reset     # 建立 hr_hire_dev：兩條切片的集合、驗證規則、索引、參考資料
uv run python scripts/run_daily.py           # 特休的每日排程（給予、年度終結、約定與公司規定的狀態、重新判定佇列）
uv run uvicorn app.main:app --reload         # http://localhost:8000/docs
uv run pytest                                # 在真的 MongoDB 上跑；每次建立獨立的測試資料庫，跑完刪除
```

呼叫 API 要帶 `Authorization: Bearer <user_accounts.user_id>`。**這只是開發用的身分**，沒有驗證簽章；正式的登入方式由平台決定（05_mapping D-09）。

## 結構

| 位置 | 內容 | 對應設計 |
|---|---|---|
| `app/spec.py` | 依 api.yaml 檢查請求；OpenAPI 文件的請求、回應、components 直接取自 api.yaml | 05_mapping D-18 |
| `app/seed.py` | 參考資料：管轄區、5 種保險制度（施行日附來源）、規則版本（分級表載入時從 `inputs/` 的來源檔解析）、多語名稱（從 `04_rules.md` 分類值表解析） | P5、P10 |
| `app/store.py` | 寫事件、只新增的版本（A）、覆寫＋變更紀錄（B）、引用檢查 | P1、P2、D-06、D-10 |
| `app/rules/` | 各保險的適用、期限、級距（R22～R44、R60）；提醒類規則（R11、R14、R15、R21、R45、R61） | 04_rules |
| `app/services/` | 各動作：一個動作一個多文件交易 | 05_mapping 第二節 |
| `app/hooks.py` | 其他切片在 hire-employee 動作的同一交易中執行的處理（掛勾）。到職（StartEmployment）、更正到職日（CorrectRecord）會呼叫；註銷、到職後立刻離開等 API 實作時要照 hooks.py 的種類呼叫 | annual-leave-grant 05_mapping D-04、「core 事件的連鎖」 |
| `app/services/corrections.py` | hire-employee 的 `POST /v1/corrections`，只實作 `employments.start_date`（特休 UC-08 用） | hire-employee 05_mapping 2.2 |
| `app/leave/` | 特休：`basis.py` 依規則應給予的每一期（R65～R70、R77）；`engine.py` 給予、年度終結、重新判定、離職停止特休與通知；`ledger.py` 讀寫與推導的數量（C01、C02）；`locks.py` 鎖與重新判定佇列；`scheduler.py` 每日排程；`actions.py`、`queries.py` 各支 API；`handlers.py` 掛勾；`seed.py` 規則版本（參數取自 04 參數表）；`clock.py` 雇主所在地的「今天」 | annual-leave-grant 05_mapping |
| `app/routers/leave.py` | annual-leave-grant 已實作的 API | annual-leave-grant api.yaml |
| `app/routers/uc01.py` | 已實作的 API | api.yaml |
| `app/stubs.py` | api.yaml 中還沒實作的 API，回 501 | api.yaml |

## 範圍

已實作 UC-01（錄用本國籍員工並到職）、UC-02（判定各保險，含待人判斷的決定、登錄僱傭關係的期間屬性）、UC-03（登錄實際加保與投保薪資），共 11 支 API；其餘 27 支回 501。
UC-01～UC-03 照 05_mapping 第六區走一遍，每一步只用前一步回應的欄位（`tests/test_gc01.py`）。

尚未實作：系統排程（ContractTermStarts、ExpireWorkAuthorization、PromptStartConfirmation 等時間觸發的事件）、更正與註銷、個資相關的 API、外籍員工的工作許可登錄（R16、R18～R20、R59）。

## 範圍（annual-leave-grant）

已實作 22 支 API（`app/routers/leave.py`）與每日排程；UC-01～UC-12 都有測試，黃金案例 GC01、GC04、GC06 照 05_mapping 第六區走（`tests/test_leave_gc.py`、`tests/test_leave_uc.py`）。
回 501：ReviseCompanyPolicy、RepealCompanyPolicy；註銷與撤銷註銷、OverrideWarning、RecordEarlyDeparture 是 hire-employee 的 API，也還是 501。
暫時的做法與設計問題（22 項，全部待處理）列在 `slices/annual-leave-grant/06_evidence/signoff.md`，程式裡標 `signoff.md #n`。

測試用 `app.leave.clock.fixed()` 固定「今天」，用 `scheduler.process_employment(db, employment_id, today)` 跑某一天的排程。

## 暫時的做法

程式裡的暫時做法都標了 `暫時：…（signoff.md #n）`，並列在 `slices/hire-employee/06_evidence/signoff.md`「實作時發現的設計問題」：

- 等專家回覆的參數假設：#7 EQ-012、#8 EQ-003、#9 EQ-006、#10 EQ-008、#11 EQ-019、#12 EQ-023
- 待處理的設計問題：無（#1～#6、#13～#21 已依設計修改）

登入只是開發用（bearer token 等於 `user_accounts.user_id`）；正式的登入方式由平台決定（05_mapping D-09）。
