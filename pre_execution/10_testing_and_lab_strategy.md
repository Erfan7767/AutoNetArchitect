# Testing and Lab Strategy

تبدأ الاختبارات بـ schema وunit tests، ثم contract tests، ثم integration tests على fixtures، ثم lab validation مع أجهزة أو محاكيات معتمدة. لا تعتبر نتيجة lab دليلًا على كل بيئة إنتاجية.

كل command generated يجب أن يملك expected output أو validation rule، وتُحفظ نتائج الاختبار مع schema version وvendor/model/version.
