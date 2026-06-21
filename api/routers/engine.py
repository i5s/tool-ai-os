from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from toll.engine.content_machine import ContentMachine
from toll.engine.prompt_gen import PromptGenerator
from toll.engine.reports import Reports
from toll.core.ai import AI
from toll.core.connection_manager import ConnectionManager
from toll.core.conversations import ConversationStore
from toll.context.engine import ContextEngine
from toll.planner.planner import Planner, ApprovalLevel
from toll.workflow.engine import WorkflowEngine
from toll.application.handler_registry import register_handlers
from toll.application.artifact_service import ArtifactService
from api.dependencies import get_connection_manager

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


@router.post("/chat")
def chat(
    req: ChatRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    try:
        ai = AI(cm=cm)
        cmachine = ContentMachine(cm=cm)
        pg = PromptGenerator(cm=cm)
        rp = Reports(cm=cm)
        conv_store = ConversationStore(cm=cm)
        context_engine = ContextEngine(cm=cm)
        planner = Planner()
        wf_engine = WorkflowEngine(cm=cm)
        artifact_svc = ArtifactService(cm)

        # Register content handlers from application layer
        register_handlers(wf_engine, cm)

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

        # Classify intent and approval level
        plan = planner.plan(req.message)

        # PLAN ONLY — create workflow, auto-run, return plan result
        if plan.level == ApprovalLevel.PLAN_ONLY:
            workflow = wf_engine.create_and_run(
                plan.__dict__,
                metadata={"conversation_id": conv_id},
            )
            response_text = (
                f"📋 **{plan.title}**\n\n"
                f"{plan.description}\n\n"
            )
            conv_store.add_message(
                conv_id, "assistant", response_text,
                {"plan": plan.__dict__, "workflow_id": workflow.id},
            )
            return {
                "response": response_text,
                "type": "plan",
                "plan": plan.__dict__,
                "conversation_id": conv_id,
                "workflow_id": workflow.id,
                "html_files": [],
            }

        # APPROVAL REQUIRED — create a pending workflow
        if plan.level == ApprovalLevel.APPROVAL:
            workflow = wf_engine.create(plan.__dict__, metadata={"conversation_id": conv_id})
            approval_msg = (
                f"⚠️ هذا الإجراء يتطلب موافقتك:\n\n"
                f"**{plan.title}**\n{plan.description}\n\n"
                f"معرف الموافقة: `{workflow.id}`"
            )
            conv_store.add_message(conv_id, "assistant", approval_msg, {"workflow_id": workflow.id})
            return {
                "response": approval_msg,
                "type": "approval_required",
                "workflow_id": workflow.id,
                "plan": plan.__dict__,
                "conversation_id": conv_id,
                "html_files": [],
            }

        # AUTO EXECUTE — route by intent
        files = []
        intent = plan.intent

        if intent == "search":
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

        elif intent == "report":
            wf = wf_engine.create_and_run(
                plan.__dict__,
                metadata={"conversation_id": conv_id},
            )
            result = wf.result or {}
            artifact_id = result.get("artifact_id")
            preview_url = result.get("preview_url")
            if artifact_id:
                files.append(preview_url or f"/api/artifacts/{artifact_id}/render")
                response_text = (
                    f"📄 **تم إنشاء التقرير**\n\n"
                    f"معرف: `{artifact_id}`\n"
                    f"{f'معاينة: {preview_url}' if preview_url else ''}"
                )
            else:
                error = result.get("error", "Unknown error")
                response_text = f"❌ فشل إنشاء التقرير: {error}"

        elif intent == "research_plan":
            ai_prompt = f"اكتب بحثاً علمياً بالعربية عن: {req.message}\n\nيجب أن يشمل: الملخص، المقدمة، المنهجية، النتائج، المناقشة، الخاتمة، المراجع."
            response_text = ai.ask(ai_prompt)

        elif intent == "presentation":
            wf = wf_engine.create_and_run(
                plan.__dict__,
                metadata={"conversation_id": conv_id},
            )
            result = wf.result or {}
            artifact_id = result.get("artifact_id")
            preview_url = result.get("preview_url")
            if artifact_id:
                files.append(preview_url or f"/api/artifacts/{artifact_id}/render")
                response_text = (
                    f"📺 **تم إنشاء العرض التقديمي**\n\n"
                    f"معرف: `{artifact_id}`\n"
                    f"{f'معاينة: {preview_url}' if preview_url else ''}"
                )
            else:
                error = result.get("error", "Unknown error")
                response_text = f"❌ فشل إنشاء العرض: {error}"

        elif intent == "prompt_generation":
            response_text = pg.generate(req.message)

        elif intent == "carousel":
            wf = wf_engine.create_and_run(
                plan.__dict__,
                metadata={"conversation_id": conv_id},
            )
            result = wf.result or {}
            artifact_id = result.get("artifact_id")
            preview_url = result.get("preview_url")
            if artifact_id:
                files.append(preview_url or f"/api/artifacts/{artifact_id}/render")
                response_text = (
                    f"🎠 **تم إنشاء Carousel**\n\n"
                    f"عدد الشرائح: {result.get('slides', 0)}\n"
                    f"معرف: `{artifact_id}`\n"
                    f"{f'معاينة: {preview_url}' if preview_url else ''}"
                )
            else:
                error = result.get("error", "Unknown error")
                response_text = f"❌ فشل إنشاء Carousel: {error}"

        elif intent == "code_snippet":
            ai_prompt = f"اكتب كود لـ: {req.message}\n\nالرجاء تقديم الكود مع الشرح."
            response_text = ai.ask(ai_prompt)

        else:
            context = context_engine.build(
                message=req.message,
                recent_messages=conversation.get("messages", []),
            )
            ai_prompt = (
                f"أجب بالعربية على السؤال التالي بشكل مفيد ودقيق، مع مراعاة السياق أدناه:\n\n"
                f"{context.prompt}"
            )
            response_text = ai.ask(ai_prompt)

        if req.image:
            response_text += "\n\n📎 تم استلام الصورة."

        # Store assistant message
        metadata = {"type": intent, "html_files": files, "intent": intent}
        conv_store.add_message(conv_id, "assistant", response_text, metadata)

        return {
            "response": response_text,
            "type": intent,
            "html_files": files,
            "conversation_id": conv_id,
            "intent": intent,
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
        cmachine = ContentMachine()
        carousel = cmachine.carousel(req.task)
        post = cmachine.social_post(req.platform, req.task)
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
def status(cm: ConnectionManager = Depends(get_connection_manager)):
    ai = AI(cm=cm)
    return {
        "limits": ai.limit_status(),
        "providers": ai.provider_status(),
    }
