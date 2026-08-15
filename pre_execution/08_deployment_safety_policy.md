# Deployment Safety Policy

لا deployment دون preflight، inventory match، backup قابل للاستعادة، diff قابل للقراءة، approval، timeout، audit record، وخطة rollback. يفشل النظام مغلقًا عند target mismatch أو missing credential أو vendor غير مدعوم.

لا تحفظ الأسرار في logs أو generated files، ولا تنفذ command لم يمر عبر vendor allowlist.
