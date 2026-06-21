from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from toll.engine.content_machine import ContentMachine
from toll.engine.prompt_gen import PromptGenerator
from toll.engine.reports import Reports
from toll.core.ai import AI
from toll.core.storage import Storage
from toll.core.registry import ProviderRegistry
from toll.core.conversations import ConversationStore
from api.dependencies import get_registry

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    type: str = "auto"
    image: str = None
    conversation_id: str = None
    model: str = "auto"


class TaskRequest(BaseModel):
    task: str
    platform: str = "عام"
    slides: int = 5


def detect_type(msg: str, preferred: str) -> str:
    if preferred != "auto":
        return preferred
    msg_lower = msg.lower()
    keywords = {
        "report": ["تقرير", "ملخص", "report", "summary"],
        "research": ["بحث", "research", "دراسة", "تحليل", "study"],
        "search": ["ابحث", "بحث", "search", "find", "google", "قوقل"],
        "present": ["عرض", "presentation", "present", "برزنتيشن", "slides"],
        "prompt": ["برومبت", "prompt", "برمبت"],
        "carousel": ["carousel", "كروسيل", "عرض دوار"],
        "code": ["كود", "code", "برمجة", "programming", "function", "api"],
    }
    for t, words in keywords.items():
        if any(w in msg_lower for w in words):
            return t
    return "auto"


@router.post("/chat")
def chat(req: ChatRequest, registry: ProviderRegistry = Depends(get_registry)):
    try:
        ai = AI()
        cm = ContentMachine()
        pg = PromptGenerator()
        rp = Reports()
        db = Storage()
        conv_store = ConversationStore()

        # Load or create conversation
        if req.conversation_id:
            conversation = conv_store.get(req.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            title = req.message[:50] + ("..." if len(req.message) > 50 else "")
            conversation = conv_store.create(title=title)

        conv_id = conversation["id"]

        # Store user message
        conv_store.add_message(conv_id, "user", req.message)

        task_type = detect_type(req.message, req.type)
        files = []

        if task_type == "report":
            ai_prompt = f"اكتب تقريراً مفصلاً بالعربية عن: {req.message}\n\nالتقرير يجب أن يشمل مقدمة، نقاط رئيسية، تحليل، وتوصيات."
            response_text = ai.ask(ai_prompt)
            html_path = rp.report(req.message)
            files.append(html_path)

        elif task_type == "research":
            ai_prompt = f"اكتب بحثاً علمياً بالعربية عن: {req.message}\n\nيجب أن يشمل: الملخص، المقدمة، المنهجية، النتائج، المناقشة، الخاتمة، المراجع."
            response_text = ai.ask(ai_prompt)

        elif task_type == "search":
            response_text = f"🔍 **بحث عن: {req.message}**\n\n---\n"
            try:
                results = ai.search(req.message, max_results=5)
                if results:
                    response_text += "\n\n".join(
                        f"**{r['title']}**\n{r['snippet']}\n<{r['url']}>"
                        for r in results
                    )
                else:
                    response_text += "لم يتم العثور على نتائج."
            except Exception as e:
                response_text += f"❌ فشل البحث: {e}"

        elif task_type == "present":
            ai_prompt = f"اكتب محتوى عرض تقديمي بالعربية عن: {req.message}\n\nوزع المحتوى على 5 شرائح."
            response_text = ai.ask(ai_prompt)
            html_path = rp.presentation(req.message)
            files.append(html_path)

        elif task_type == "prompt":
            response_text = pg.generate(req.message)

        elif task_type == "carousel":
            result = cm.carousel(req.message)
            response_text = f"🎠 **تم إنشاء Carousel**\n\nالملف: {result}"
            if "http" in str(result) or ".html" in str(result):
                files.append(str(result))

        elif task_type == "code":
            ai_prompt = f"اكتب كود لـ: {req.message}\n\nالرجاء تقديم الكود مع الشرح."
            response_text = ai.ask(ai_prompt)

        else:
            ai_prompt = f"أجب بالعربية على السؤال التالي بشكل مفيد ودقيق:\n\n{req.message}"
            response_text = ai.ask(ai_prompt)

        if req.image:
            response_text += "\n\n📎 تم استلام الصورة."

        # Store assistant message
        metadata = {"type": task_type, "html_files": files}
        conv_store.add_message(conv_id, "assistant", response_text, metadata)

        db.save_history("chat", req.message[:100], response_text[:200])
        return {
            "response": response_text,
            "type": task_type,
            "html_files": files,
            "conversation_id": conv_id,
        }

    except RuntimeError as e:
        return {"response": f"⚠️ {str(e)}\n\nاستخدم مزود AI آخر أو حاول لاحقاً.", "type": "error", "html_files": [], "conversation_id": req.conversation_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content")
def content(req: TaskRequest):
    try:
        cm = ContentMachine()
        carousel = cm.carousel(req.task)
        post = cm.social_post(req.platform, req.task)
        return {"carousel": carousel, "post": post}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompt")
def prompt(req: TaskRequest):
    try:
        pg = PromptGenerator()
        result = pg.generate(req.task)
        return {"prompt": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report")
def report(req: TaskRequest):
    try:
        r = Reports()
        result = r.report(req.task)
        return {"report": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/present")
def present(req: TaskRequest):
    try:
        r = Reports()
        result = r.presentation(req.task, req.slides)
        return {"presentation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def status(registry: ProviderRegistry = Depends(get_registry)):
    ai = AI()
    return {
        "limits": ai.limit_status(),
        "providers": registry.status(),
    }
