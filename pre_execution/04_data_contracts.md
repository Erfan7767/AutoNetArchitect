# Data Contracts

العقود الرسمية بين الطبقات هي `ProductScope`، `RuntimeMode`، `HumanSuppliedMandatory`، `VendorProfile`، و`ProjectState`. كل عقد يحمل `schema_version`، ويجب رفض الحقول غير الصالحة بدل إسقاطها بصمت.

| العقد | الغرض | المالك |
|---|---|---|
| ProductScope | حدود المنتج | pre_execution |
| VendorProfile | الأجهزة والأوامر المدعومة | vendor library |
| ProjectState | انتقالات المشروع | state machine |
| HumanSuppliedMandatory | الحقائق المطلوبة من المستخدم | user |
