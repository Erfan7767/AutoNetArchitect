# Product Scope V1

المنتج الفعلي في V1 هو أداة single-user تساعد المستخدم على تعريف طوبولوجيا شبكة، تحويل المتطلبات إلى تصميم منظم، توليد configuration proposal، وإجراء validation في lab قبل deployment. المنتج لا يدّعي اكتشاف البيئة الحية أو تنفيذ تغييرات إنتاجية دون موافقة.

خارج النطاق: multi-tenancy، billing، إدارة هوية مؤسسية، اكتشاف شامل لكل vendor، وقرارات تشغيلية مبنية على بيانات غير مقدمة من المستخدم.

| داخل V1 | خارج V1 |
|---|---|
| topology، inventory، design proposal، validation، reports | تنفيذ إنتاجي تلقائي، اكتشاف غير موثق، تعدد المؤسسات |
| Huawei device library | اعتماد vendor إضافي دون ADR |
