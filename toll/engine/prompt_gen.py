from ..core.ai import AI
from ..core.storage import Storage

TEMPLATES = {
    "تسويق": "اكتب لي {task} بأسلوب تسويقي مقنع يستهدف الجمهور المستهدف ويبرز القيمة الفريدة.",
    "برمجة": "اكتب لي كود {task} مع شرح وافي ومنسق. استخدم أفضل الممارسات.",
    "تصميم": "صمم لي {task} مع وصف العناصر البصرية، الألوان، الخطوط، وتجربة المستخدم.",
    "كتابة": "اكتب لي {task} بأسلوب سلس وجذاب مع مقدمة وعرض وخاتمة.",
    "تقرير": "أعد لي تقرير عن {task} يشمل: المقدمة، التحليل، النتائج، التوصيات.",
}

class PromptGenerator:
    def __init__(self):
        self.ai = AI()
        self.db = Storage()

    def generate(self, task: str, category: str = "") -> str:
        if category and category in TEMPLATES:
            base = TEMPLATES[category].format(task=task)
        else:
            base = f"نفذ المهمة التالية بدقة واحترافية: {task}"
        try:
            result = self.ai.ask(f"قم بتوليد برومبت مفصل بالعربية للمهمة التالية:\n{base}\n\nالبرومبت يجب أن يكون واضحاً، منظم الخطوات، وجاهزاً للاستخدام.")
            self.db.save_history("prompt", task, result)
            return f"🧠 البرومبت المولد:\n\n{result}"
        except RuntimeError:
            return f"🧠 برومبت مقترح (بدون AI):\n\n{base}"

    def categories(self) -> list:
        return list(TEMPLATES.keys())
