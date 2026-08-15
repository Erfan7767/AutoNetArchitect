# Runtime Mode

V1 هو **single-user وlocal-first**. يمكن تشغيله في بيئة تطوير أو مختبر يسيطر عليه المستخدم. لا يُفترض وجود backend متعدد المستخدمين أو جلسات متزامنة أو عزل مستأجرين.

إذا تغير القرار إلى multi-user، يجب إضافة ADR وعقود authentication، authorization، tenancy، audit، وconcurrency قبل التنفيذ.
