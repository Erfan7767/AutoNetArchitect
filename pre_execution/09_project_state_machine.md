# Project State Machine

الحالات الرسمية هي `draft`، `specified`، `designed`، `validated`، `approved`، `deployed`، و`blocked`. الانتقال يجب أن يكون صريحًا ومبنيًا على شروط قابلة للتحقق.

المسار الطبيعي: `draft -> specified -> designed -> validated -> approved -> deployed`. الفشل ينقل إلى `blocked`، ولا يعاد إلى مسار التنفيذ إلا بعد معالجة السبب.
