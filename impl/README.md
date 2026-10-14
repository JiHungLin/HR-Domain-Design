# hire-employee 實作（MongoDB＋FastAPI）

依 `slices/hire-employee/` 第 ⑤ 步凍結的設計（`05_mapping.md`、`schema.mongo.js`、`api.yaml` @ `hire-employee/05-v1`）實作。

## 需要

- MongoDB replica set（多文件交易，PLAN.md D-35）。連線字串預設 `mongodb://localhost:27017/?replicaSet=rs0`，可用 `HR_MONGO_URI` 覆寫。
- `mongosh`（建立集合時執行 `schema.mongo.js`）
- [uv](https://docs.astral.sh/uv/)

## 使用

```bash
uv sync
uv run python scripts/init_db.py --reset     # 建立 hr_hire_dev：32 個集合、驗證規則、索引、參考資料
uv run uvicorn app.main:app --reload         # http://localhost:8000/docs
uv run pytest                                # 在真的 MongoDB 上跑；每次建立獨立的測試資料庫，跑完刪除
```

呼叫 API 要帶 `Authorization: Bearer <user_accounts.user_id>`。**這只是開發用的身分**，沒有驗證簽章；正式的登入方式由平台決定（05_mapping D-09）。

## 結構

| 位置 | 內容 | 對應設計 |
|---|---|---|
| `app/seed.py` | 參考資料：管轄區、5 種保險制度、規則版本（最低工資、4 張分級表…）、多語名稱（從 `04_rules.md` 分類值表解析） | P5、P10 |
| `app/store.py` | 寫事件、只新增的版本（A）、覆寫＋變更紀錄（B）、引用檢查 | P1、P2、D-06、D-10 |
| `app/rules/` | 各保險的適用、期限、級距（R22～R44、R60）；提醒類規則（R11、R14、R15、R21） | 04_rules |
| `app/services/` | 各動作：一個動作一個多文件交易 | 05_mapping 第二節 |
| `app/routers/uc01.py` | 已實作的 API | api.yaml |
| `app/stubs.py` | api.yaml 中還沒實作的 API，回 501 | api.yaml |

## 範圍

已實作 UC-01（錄用本國籍員工並到職）、UC-02（判定各保險）、UC-03（登錄實際加保與投保薪資），共 9 支 API；其餘 27 支回 501。

尚未實作：系統排程（ContractTermStarts、ExpireWorkAuthorization、PromptStartConfirmation 等時間觸發的事件）、更正與註銷、個資相關的 API、外籍員工的工作許可登錄。

## 專家還沒回覆的地方怎麼處理

| 項目 | 做法 |
|---|---|
| EQ-003 健保、勞退的法定生效日 | 不給值，標出待確認；晚辦天數不計算（R35） |
| EQ-012 哪些固定給付算入投保薪資 | 規則 R39 的參數暫以「伙食津貼等四類都算入」為假設（使用者 GC01 預期結果的前提），標出待確認；確認後新增 R39 的修訂即可，不改程式 |
| EQ-006 65 歲界線 | R22、R24 參數 `max_age: 65` 含 65 歲；剛好 65 歲時標出待確認 |
| EQ-008 人數計入範圍 | 先以雇主的在職人數計（R23），標出待確認 |
| EQ-019 最低工資的比較基礎 | 先用底薪比較（R11 參數 `compare_basis`） |
