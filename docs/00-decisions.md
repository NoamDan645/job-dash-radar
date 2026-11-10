# רדאר משרות: יומן החלטות (טיוטה)

מסמך עבודה שמתעדכן תוך כדי האפיון המשותף. הקבצים המסודרים (דיאגרמות, מודל נתונים) ייכתבו אחרי שנעבור על כל הרכיבים.

## מטרה
ללמוד לכתוב פייפליין מקצה לקצה ולהכיר את הטכנולוגיות שבדרך: Docker Compose, RabbitMQ, Kafka, PostgreSQL, Elasticsearch וניטור. כשיש התנגשות בין למידה לתוצאה מהירה, הלמידה קודמת.

## החלטות שהתקבלו

| נושא | החלטה |
|---|---|
| משתמשים | כרגע משתמש אחד. הסכמה וה-API בנויים עם `user_id` כדי שיהיה אפשר להוסיף משתמשים. |
| ערוץ התראות | בשלב הזה: מייל מקומי בקונטיינר (שרת מייל מדומה שמציג הודעות בדפדפן). בלי בוט טלגרם. הקוד כותב לממשק `NotificationChannel`, כך שטלגרם יתווסף בהמשך כמימוש נוסף בלי לשנות את שאר המערכת. הפרופיל מוגדר דרך ה-API של ASP.NET. |
| API | ASP.NET Core. |
| היקף חברות | כ-185 חברות עם מערכת גיוס מזוהה ב-Techmap (147 Comeet, 27 Greenhouse, 7 Lever, 4 Breezy; ייתכנו חפיפות). זיהוי אוטומטי של מערכת גיוס מקישורי קריירה (1,291) הוא תוספת בשבוע השני. |
| תדירות סריקה | כל 6 שעות לכל חברה. |
| תזמון | APScheduler בקונטיינר. Airflow ייכנס בשבוע השני למשימות האצווה היומיות. |
| RabbitMQ | exchange שמנתב לפי מערכת גיוס, ותור לכל מערכת (`scrape.comeet`, `scrape.greenhouse` וכו'). אישור (`ack`) ידני רק אחרי כתיבה מוצלחת ל-Kafka. |
| כשלונות סריקה | retry עם השהיה של דקה, ואחרי 3 ניסיונות הפתק עובר ל-`scrape.dlq`. |
| Workers | מביאים נתונים גולמיים ללא תרגום, בקצב של עד בקשה אחת בשנייה לכל אתר, וכותבים ל-`job.raw`. |
| Kafka | שרת אחד (KRaft), 3 partitions לכל topic, הודעות JSON עם `schema_version` וסכמות כקבצי JSON Schema. בלי Schema Registry בשלב הראשון. |
| שמירת `job.raw` | שבוע (הערכה גסה: כ-30 אלף הודעות ביום, להמדד בפועל). |
| התרגום | ה-adapters יושבים ב-Normalizer ולא ב-worker. כך אפשר לתקן תרגום ולנגן מחדש מהיומן. |
| הודעות שאי אפשר לפרש | עוברות ל-`job.raw.dlq` עם סיבת השגיאה, והזרם ממשיך. |
| זיהוי כישורים | מילון כישורים וכינויים עם כללי הקשר (למשל Go ו-R). מדידת דיוק מול כ-50 משרות שתויגו ידנית. |
| pandas | ב-Normalizer הניקוי נעשה בפונקציות Python רגילות, כי הוא קורא הודעה אחת בכל פעם. pandas ישמש ב: (1) מחברת לבחינת דוגמאות לפני כתיבת adapters, (2) מדידת הדיוק של זיהוי הכישורים, (3) משימת האצווה היומית ב-Airflow (`groupby` על מגמות כישורים). |
| PostgreSQL | הוא מקור האמת (הנתונים הרשמיים). Kafka הוא יומן אירועים ו-Elasticsearch הוא העתק לחיפוש שאפשר לבנות מחדש. |
| מזהה משרה | `job_id` בנוי מ-`{ats_type}:{company_id}:{external_id}`, למשל `greenhouse:513674309:8256182`. הוא קבוע לאורך זמן והוא מפתח ההודעות ב-Kafka. `content_hash` הוא נפרד ומזהה גרסה של תוכן המשרה. |
| משרה חדשה, שהשתנתה או נסגרה | הכותב ל-PostgreSQL משווה `content_hash`: אין משרה = "נפתחה", טביעה שונה = "השתנתה", זהה = רק עדכון `last_seen_at`. כשמגיעה `scan.completed`, משרה פתוחה של החברה שלא ברשימה מסומנת "נסגרה". כל אירוע נרשם ב-`job_events`. בודק ההתאמה מתריע רק על "נפתחה". |
| Elasticsearch | האינדקס מחזיק גם משרות סגורות, עם `status=closed`, כדי שיהיה אפשר לחפש בהיסטוריה. ההודעה `job.closed` מעדכנת את `status` ולא מוחקת את המשרה. כל חיפוש ב-API מסנן `status=open` כברירת מחדל. `_id` במסמך שווה ל-`job_id`, כך שכתיבה חוזרת דורסת. שדות טקסט (`title`, `description`) מנותחים באנגלית, ושדות סינון (`skills`, `city`, `level`, `role_family`, `work_mode`) מסוג `keyword`. |
| בודק ההתאמה | קורא `job.opened` בלבד (לא `job.normalized`), כדי שלא יתריע על משרות ישנות. סינון קשיח לפי תחום (`role_family`) ועיר, ואז ציון רך 0 עד 100 (הצעת משקלות, ניתנת לשינוי): כישורים 60, רמת ותק 25, אופן עבודה 15. חלק הכישורים הוא כמה מהכישורים שהמשתמש רוצה נמצאים במשרה. הציון נשמר עם הסיבה בטבלת `notifications`. |
| יום ראשון | מתריעים על כל התאמה שעוברת את הסף, גם בסריקה הראשונה, בלי שלב baseline. ההצפה מרוסנת בקצב השליחה (ראה את שליח ההודעות). |
| שליח ההודעות | פתק `notify` ב-RabbitMQ (משימה, לא אירוע) עם `prefetch=1` וקצב מבוקר, כדי לרסן הצפה. ניסיונות חוזרים עם השהיה, ואחרי 3 כשלונות `status=failed` והפתק עובר ל-DLQ. משימה מתוזמנת שולחת מחדש התראות שממתינות יותר מ-10 דקות (למקרה שהבודק נפל בין כתיבה לשליחה). שרת המייל המקומי הוא Mailpit (הממשיך המתוחזק של MailHog: המהדורה האחרונה שלו ב-31.10.2026, ושל MailHog ב-2020). |
| API | ASP.NET Core עם Swagger. Endpoints: `GET /jobs/search` (Elasticsearch, משרות פתוחות כברירת מחדל), `GET /jobs/{job_id}`, `GET` ו-`PUT /me/profile`, `GET /me/notifications`, `GET /stats/skills`, `GET /health`. אימות במפתח קבוע ב-`X-API-Key`, ובהמשך JWT. ה-API לא כותב משרות ואינו חלק מהנתיב של הפייפליין. |
| גישה למסד מה-API | Dapper וקבצי SQL. הטבלאות מוגדרות בתיקיית `db/migrations`, שאינה שייכת לשפה אחת, ומשותפת ל-API ול-workers. |
| פריסה בענן | תכנון עכשיו, פריסה בסוף. עכשיו: הגדרות ממשתני סביבה, בדיקות בריאות ו-volumes לנתונים. בסוף: מכונה וירטואלית אחת עם Docker Compose, CI ב-GitHub Actions ו-HTTPS ל-API. רק ה-API נחשף החוצה. |
| ניטור | Prometheus ו-Grafana. מדדי מערכת: עומק תורים ו-DLQ ב-RabbitMQ (התוסף המובנה), consumer lag ב-Kafka (kafka-exporter), מדדים מהקוד שלנו (סריקות שנכשלו, שגיאות פענוח, זמן תגובה ב-API). מדדים עסקיים (משרות חדשות ביום, כישורים מבוקשים, זמן מאז הסריקה האחרונה) כשאילתות SQL ישירות מ-Grafana על PostgreSQL. `scan_id` עובר בכל הודעה ובכל לוג, והלוגים הם JSON עם שדות קבועים. התראות על תקלות יוצאות מ-Grafana ל-Mailpit. |

## Topics בקצרה

| Topic | כותב | קורא | מפתח |
|---|---|---|---|
| `job.raw` | Workers | Normalizer | `company_id` |
| `scan.completed` | Workers | רכיב סימון משרות סגורות | `company_id` |
| `job.normalized` | Normalizer | כותב ל-PostgreSQL, מאנדקס ל-Elasticsearch | `job_id` |
| `job.opened` | כותב ל-PostgreSQL | בודק ההתאמה | `job_id` |
| `job.raw.dlq` | Normalizer | בדיקה ידנית | `company_id` |
| `job.closed` | כותב ל-PostgreSQL | מאנדקס ל-Elasticsearch | `job_id` |

## טבלאות ב-PostgreSQL

| טבלה | מה היא שומרת | עמודות עיקריות |
|---|---|---|
| `companies` | החברות לסריקה, בטעינה מ-Techmap | `company_id` (ח.פ), `name`, `ats_type`, `ats_id`, `is_active` |
| `job_postings` | המצב העדכני של כל משרה | `job_id`, `company_id`, `title`, `level`, `role_family`, `city`, `work_mode`, `url`, `description`, `content_hash`, `status`, `first_seen_at`, `last_seen_at`, `closed_at`, `ats_type`, `external_id` |
| `job_skills` | טבלת קישור בין משרה לכישור | `job_id`, `skill` |
| `job_events` | היסטוריה: נפתחה, השתנתה, נסגרה | `job_id`, `event_type`, `happened_at` |
| `users` | המשתמשים | `user_id`, `telegram_chat_id` |
| `user_profiles` | מה כל משתמש מחפש | `user_id`, `wanted_skills`, `cities`, `role_families`, `min_score` |
| `notifications` | התראות שנשלחו | `user_id`, `job_id`, `score`, `reason`, `status`, `sent_at`, עם `UNIQUE(user_id, job_id)` |
| `scan_runs` | היסטוריית סריקות לניטור | `company_id`, `started_at`, `finished_at`, `jobs_seen`, `error` |

אילוצים: `job_postings.company_id` הוא מפתח זר ל-`companies`, ו-`UNIQUE(ats_type, company_id, external_id)` על `job_postings`.

## הוחלט ביום 1 (2026-11-01)
- שפת ה-workers (Scheduler, Workers, Normalizer, Notifier): **Python**. ה-API נשאר ב-ASP.NET Core.

## הוחלט ביום 2 (2026-11-03)
- הרחבת מקורות נתונים: המערכת צריכה לאפשר בהמשך מקורות נוספים מעבר ל-Comeet ו-Greenhouse, למשל אתרי דרושים והתראות משרות שמגיעות למייל. לא בונים אותם עכשיו. בקוד שומרים על הפרדה: worker נפרד ו-adapter נפרד לכל מקור, וכל הודעה ב-`job.raw` מציינת מאיזה מקור הגיעה. מה שאחרי `job.normalized` לא אמור להשתנות.
- מה ישתנה כשנוסיף את המקור הראשון שאינו מערכת גיוס (ב-migration חדש): הרחבת `ats_type` למושג כללי של מקור, אפשרות למשרה בלי חברה מ-`companies`, פורמט `job_id`, וזיהוי משרה סגורה (למקור כזה אין רשימה מלאה לכל חברה, ולכן `scan.completed` לא יספיק).

## מוצע ועדיין לא אושר במפורש
- ה-topic `job.opened`: הבודק קורא אותו ולא את `job.normalized`.
- פורמט האפיון הסופי: קבצי Markdown עם Mermaid בתיקיית הפרויקט.

## שאלות פתוחות
- משרה שנמחקה ונפתחה מחדש עם מזהה חדש נחשבת משרה חדשה. האם לזהות אותה לפי כותרת ועיר?
- מה עושים עם אותה משרה שמופיעה בשתי מערכות גיוס?
- טלגרם (בהמשך): האם לשלוח בלבד או גם לקבל פקודות, ואם כן long polling או webhook?
- Lever: המזהים שבדקתי החזירו 404, צריך לאמת לפני שמסתמכים עליו.
